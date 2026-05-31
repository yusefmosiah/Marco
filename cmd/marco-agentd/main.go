package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

const (
	defaultProvider  = "fireworks"
	defaultModel     = "accounts/fireworks/models/deepseek-v4-flash"
	defaultReasoning = "medium"
)

type server struct {
	root   string
	pyCLI  string
	zotBin string
}

type promptRequest struct {
	Prompt string `json:"prompt"`
}

func main() {
	var root string
	var host string
	var port int
	flag.StringVar(&root, "root", ".", "Marco repo root")
	flag.StringVar(&host, "host", "127.0.0.1", "HTTP host")
	flag.IntVar(&port, "port", 8787, "HTTP port")
	flag.Parse()

	absRoot, err := filepath.Abs(root)
	if err != nil {
		log.Fatal(err)
	}
	srv := newServer(absRoot)
	addr := fmt.Sprintf("%s:%d", host, port)
	log.Printf("marco-agentd listening on %s root=%s", addr, absRoot)
	log.Fatal(http.ListenAndServe(addr, srv.routes()))
}

func newServer(root string) *server {
	return &server{
		root:   root,
		pyCLI:  getenv("MARCO_PYTHON_CLI", defaultPythonCLI(root)),
		zotBin: getenv("MARCO_ZOT_BIN", "zot"),
	}
}

func (s *server) routes() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", s.handleHealth)
	mux.HandleFunc("/v1/chat", s.handleChat)
	mux.HandleFunc("/v1/agents/", s.handleAgent)
	return withCORS(mux)
}

func (s *server) handleHealth(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeError(w, http.StatusMethodNotAllowed, "method not allowed")
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"schema_version": "marco.agentd_health.v1",
		"status":         "ok",
		"service":        "marco-agentd",
		"root":           s.root,
		"python_cli":     s.pyCLI,
		"zot_bin":        s.zotBin,
	})
}

func (s *server) handleAgent(w http.ResponseWriter, r *http.Request) {
	trimmed := strings.TrimPrefix(r.URL.Path, "/v1/agents/")
	parts := strings.Split(strings.Trim(trimmed, "/"), "/")
	if len(parts) == 0 || parts[0] == "" {
		writeError(w, http.StatusNotFound, "agent id is required")
		return
	}
	agentID, ok := normalizeAgentID(parts[0])
	if !ok {
		writeError(w, http.StatusNotFound, "unknown agent")
		return
	}
	if len(parts) == 1 && r.Method == http.MethodGet {
		packet, err := s.loadAgentPacket(r.Context(), agentID)
		if err != nil {
			writeError(w, http.StatusBadGateway, err.Error())
			return
		}
		writeJSON(w, http.StatusOK, packet)
		return
	}
	if len(parts) == 2 && parts[1] == "prompt" && r.Method == http.MethodPost {
		req, err := readPromptRequest(r.Body)
		if err != nil {
			writeError(w, http.StatusBadRequest, err.Error())
			return
		}
		packet, err := s.loadAgentPacket(r.Context(), agentID)
		if err != nil {
			writeError(w, http.StatusBadGateway, err.Error())
			return
		}
		answer, err := s.promptWithZot(r.Context(), agentID, req.Prompt, packet)
		if err != nil {
			writeError(w, http.StatusBadGateway, err.Error())
			return
		}
		writeJSON(w, http.StatusOK, map[string]any{
			"schema_version":  "marco.agent_prompt_response.v1",
			"agent_id":        agentID,
			"prompt":          req.Prompt,
			"answer_markdown": answer,
			"context_packet":  packet,
			"context_refs":    contextRefs(s.root, agentID),
		})
		return
	}
	writeError(w, http.StatusNotFound, "route not found")
}

func (s *server) handleChat(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeError(w, http.StatusMethodNotAllowed, "method not allowed")
		return
	}
	req, err := readPromptRequest(r.Body)
	if err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}
	packets := map[string]any{}
	for _, agentID := range []string{"economic_modeling_agent", "news_agent", "analyst_agent"} {
		packet, err := s.loadAgentPacket(r.Context(), agentID)
		if err == nil {
			packets[agentID] = packet
		}
	}
	answer, err := s.promptWithZot(r.Context(), "ui_chatbot_agent", req.Prompt, packets)
	if err != nil {
		writeError(w, http.StatusBadGateway, err.Error())
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"schema_version":      "marco.chat_response.v1",
		"agent_id":            "ui_chatbot_agent",
		"prompt":              req.Prompt,
		"answer_markdown":     answer,
		"specialist_context":  packets,
		"specialist_handoffs": contextRefs(s.root, "ui_chatbot_agent"),
	})
}

func (s *server) loadAgentPacket(ctx context.Context, agentID string) (any, error) {
	ctx, cancel := context.WithTimeout(ctx, 60*time.Second)
	defer cancel()
	args, err := pythonArgs(agentID, s.root)
	if err != nil {
		return nil, err
	}
	cmd := exec.CommandContext(ctx, s.pyCLI, args...)
	cmd.Dir = s.root
	var stdout bytes.Buffer
	var stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	if err := cmd.Run(); err != nil {
		return nil, fmt.Errorf("python cli failed: %w: %s", err, strings.TrimSpace(stderr.String()))
	}
	var payload any
	if err := json.Unmarshal(stdout.Bytes(), &payload); err != nil {
		return nil, fmt.Errorf("invalid python cli JSON: %w", err)
	}
	return payload, nil
}

func (s *server) promptWithZot(ctx context.Context, agentID string, prompt string, contextPacket any) (string, error) {
	if strings.TrimSpace(prompt) == "" {
		return "", errors.New("prompt is required")
	}
	ctx, cancel := context.WithTimeout(ctx, 180*time.Second)
	defer cancel()
	contextJSON, err := json.MarshalIndent(contextPacket, "", "  ")
	if err != nil {
		return "", err
	}
	systemPrompt := marcoSystemPrompt(agentID)
	userPrompt := fmt.Sprintf("User prompt:\n%s\n\nMarco context JSON:\n%s\n\nLatest handoff markdown:\n%s\n", prompt, string(contextJSON), latestHandoffText(s.root, agentID))
	args := []string{
		"-p",
		"--provider", getenv("MARCO_AGENT_PROVIDER", defaultProvider),
		"--model", getenv("MARCO_AGENT_MODEL", defaultModel),
		"--reasoning", getenv("MARCO_AGENT_REASONING", defaultReasoning),
		"--cwd", s.root,
		"--no-tools",
		"--no-session",
		"--no-skill",
		"--no-ext",
		"--max-steps", "4",
		"--system-prompt", systemPrompt,
		userPrompt,
	}
	cmd := exec.CommandContext(ctx, s.zotBin, args...)
	cmd.Dir = s.root
	var stdout bytes.Buffer
	var stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	if err := cmd.Run(); err != nil {
		return "", fmt.Errorf("zot prompt failed: %w: %s", err, strings.TrimSpace(stderr.String()))
	}
	return strings.TrimSpace(stdout.String()), nil
}

func pythonArgs(agentID string, root string) ([]string, error) {
	base := []string{"--root", root, "--compact"}
	switch agentID {
	case "economic_modeling_agent":
		return append([]string{"economic-model-agent"}, append(base, "--no-handoff")...), nil
	case "news_agent":
		return append([]string{"news-agent"}, base...), nil
	case "analyst_agent":
		return append([]string{"analyst-agent"}, base...), nil
	default:
		return nil, fmt.Errorf("unknown agent id: %s", agentID)
	}
}

func normalizeAgentID(id string) (string, bool) {
	switch id {
	case "economic-modeling-agent", "economic_modeling_agent":
		return "economic_modeling_agent", true
	case "news-agent", "news_agent":
		return "news_agent", true
	case "analyst-agent", "analyst_agent":
		return "analyst_agent", true
	default:
		return "", false
	}
}

func readPromptRequest(body io.Reader) (promptRequest, error) {
	var req promptRequest
	if err := json.NewDecoder(body).Decode(&req); err != nil {
		return req, err
	}
	req.Prompt = strings.TrimSpace(req.Prompt)
	if req.Prompt == "" {
		return req, errors.New("prompt is required")
	}
	return req, nil
}

func marcoSystemPrompt(agentID string) string {
	return strings.Join([]string{
		"You are a Marco macro research agent.",
		"Answer in concise markdown.",
		"Use only the provided Marco context unless you explicitly say a new specialist run is needed.",
		"Do not invent metrics, news IDs, sources, or model results.",
		"Separate evidence from interpretation.",
		"Active agent: " + agentID + ".",
	}, "\n")
}

func latestHandoffText(root string, agentID string) string {
	files := map[string][]string{
		"economic_modeling_agent": {"economic_modeling_agent.md"},
		"news_agent":              {"news_agent.md"},
		"analyst_agent":           {"analyst_agent.md"},
		"ui_chatbot_agent":        {"economic_modeling_agent.md", "news_agent.md", "analyst_agent.md"},
	}
	var parts []string
	for _, name := range files[agentID] {
		path := filepath.Join(root, "data", "agents", "latest", name)
		data, err := os.ReadFile(path)
		if err == nil {
			parts = append(parts, fmt.Sprintf("## %s\n\n%s", name, string(data)))
		}
	}
	return strings.Join(parts, "\n\n")
}

func contextRefs(root string, agentID string) []string {
	names := map[string][]string{
		"economic_modeling_agent": {"economic_modeling_agent.md"},
		"news_agent":              {"news_agent.md"},
		"analyst_agent":           {"analyst_agent.md"},
		"ui_chatbot_agent":        {"economic_modeling_agent.md", "news_agent.md", "analyst_agent.md"},
	}[agentID]
	var refs []string
	for _, name := range names {
		path := filepath.Join(root, "data", "agents", "latest", name)
		if _, err := os.Stat(path); err == nil {
			refs = append(refs, filepath.ToSlash(filepath.Join("data", "agents", "latest", name)))
		}
	}
	return refs
}

func defaultPythonCLI(root string) string {
	local := filepath.Join(root, ".venv", "bin", "emf-macro")
	if _, err := os.Stat(local); err == nil {
		return local
	}
	return "emf-macro"
}

func getenv(key string, fallback string) string {
	value := strings.TrimSpace(os.Getenv(key))
	if value == "" {
		return fallback
	}
	return value
}

func writeJSON(w http.ResponseWriter, status int, payload any) {
	body, err := json.MarshalIndent(payload, "", "  ")
	if err != nil {
		writeError(w, http.StatusInternalServerError, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	w.WriteHeader(status)
	_, _ = w.Write(append(body, '\n'))
}

func writeError(w http.ResponseWriter, status int, message string) {
	writeJSON(w, status, map[string]any{"status": status, "error": message})
}

func withCORS(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		next.ServeHTTP(w, r)
	})
}
