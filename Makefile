PYTHON ?= .venv/bin/python
EMF ?= .venv/bin/emf-macro

.PHONY: setup test go-test web-build ci agent-context serve-agent-api serve-agentd deploy-node-a clean

setup:
	@tools/bootstrap.sh

test:
	@$(PYTHON) -m pytest -q

go-test:
	@go test ./...

web-build:
	@cd apps/web && npm run build

ci: test go-test web-build

agent-context:
	@$(EMF) agent-context --root . --run-id latest

serve-agent-api:
	@$(EMF) serve-agent-api --root . --host 127.0.0.1 --port 8765 --public-base-url https://choir-ip.com/marco

serve-agentd:
	@go run ./cmd/marco-agentd --root . --host 127.0.0.1 --port 8787

deploy-node-a:
	@tools/deploy_node_a_live.sh

clean:
	@rm -rf apps/web/dist .pytest_cache
