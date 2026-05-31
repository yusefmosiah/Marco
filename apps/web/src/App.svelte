<script>
  const artifactSpecs = {
    fred: {
      label: 'FRED FX/rate lab',
      path: './artifacts/fred-fx-rate-lab-summary.json'
    },
    global: {
      label: 'Global macro panel',
      path: './artifacts/global-macro-panel-summary.json'
    },
    news: {
      label: 'Macro news haul',
      path: './artifacts/macro-news-summary.json'
    }
  };

  const apiBase = import.meta.env.VITE_MARCO_AGENT_API ?? '';

  let fred = null;
  let globalPanel = null;
  let news = null;
  let loadError = null;
  let activeThreadId = 'briefing';
  let selectedReport = 'modeling';
  let route = 'chat';
  let promptText = '';
  let sending = false;

  const threads = [
    {
      id: 'briefing',
      title: 'Hackathon briefing',
      subtitle: 'Investor-ready synthesis',
      status: 'Live',
      unread: 0
    },
    {
      id: 'economist',
      title: 'Economist review',
      subtitle: 'Data, labels, baselines',
      status: 'Ready',
      unread: 2
    },
    {
      id: 'news',
      title: 'News-model run',
      subtitle: 'Marginal macro information',
      status: 'Queued',
      unread: 1
    },
    {
      id: 'analyst',
      title: 'Analyst memo',
      subtitle: 'Artifact-grounded answer',
      status: 'Draft',
      unread: 0
    }
  ];

  const agents = [
    {
      id: 'economic-modeling-agent',
      label: 'Modeling',
      state: 'benchmarks ready',
      accent: 'blue'
    },
    {
      id: 'news-agent',
      label: 'News',
      state: 'feed snapshot ready',
      accent: 'teal'
    },
    {
      id: 'analyst-agent',
      label: 'Analyst',
      state: 'waiting on synthesis',
      accent: 'amber'
    }
  ];

  let messagesByThread = {
    briefing: [
      {
        role: 'assistant',
        eyebrow: 'Marco synthesis',
        body:
          'Marco is now framed as an agent workbench: economic modeling, news intake, and analyst synthesis publish artifacts that the chat layer can read and route against.',
        context: ['docs/agents/chat-and-agent-interface-strategy.md', 'cmd/marco-agentd/main.go']
      },
      {
        role: 'user',
        body: 'What can we show a partner without overselling the alpha?'
      },
      {
        role: 'assistant',
        eyebrow: 'Grounded answer',
        body:
          'Show the research machine, not a trading claim. The committed FRED run says simple no-change style baselines still dominate most FX/rate contests, which is useful because the system exposes the noise floor before adding more complex models.',
        context: ['./artifacts/fred-fx-rate-lab-summary.json']
      }
    ],
    economist: [
      {
        role: 'assistant',
        eyebrow: 'Economist context',
        body:
          'The current macro panel is a starter haul, not all global economic data. It has FRED FX/rate work plus ECB/World Bank starter coverage, and it labels latest-revised snapshots separately from vintage-safe evidence.',
        context: ['./artifacts/global-macro-panel-summary.json']
      }
    ],
    news: [
      {
        role: 'assistant',
        eyebrow: 'News context',
        body:
          'The news agent should treat each fetch as a provenance-bearing update, then compress marginal information into model.md before it reaches the token limit.',
        context: ['./artifacts/macro-news-summary.json']
      }
    ],
    analyst: [
      {
        role: 'assistant',
        eyebrow: 'Analyst context',
        body:
          'The analyst endpoint should answer from accumulated reports first, then call modeling or news agents only when the prompt requires fresh specialist work.',
        context: ['docs/agents/api-and-cli.md']
      }
    ]
  };

  Promise.all([
    loadArtifact('fred'),
    loadArtifact('global'),
    loadArtifact('news')
  ]).catch((error) => {
    loadError = error.message;
  });

  async function loadArtifact(key) {
    const response = await fetch(artifactSpecs[key].path);
    if (!response.ok) {
      throw new Error(`${artifactSpecs[key].label} failed to load: ${response.status}`);
    }

    const payload = await response.json();
    if (key === 'fred') fred = payload;
    if (key === 'global') globalPanel = payload;
    if (key === 'news') news = payload;
  }

  $: activeThread = threads.find((thread) => thread.id === activeThreadId) ?? threads[0];
  $: activeMessages = messagesByThread[activeThreadId] ?? [];
  $: baselineWins = fred
    ? fred.best_by_rmse.filter((row) => ['random_walk', 'no_change'].includes(row.best_model)).length
    : 0;
  $: contestCount = fred ? fred.best_by_rmse.length : 0;
  $: modelWins = fred ? contestCount - baselineWins : 0;
  $: latestVintage = fred?.vintage_policy?.replaceAll('_', ' ') ?? 'loading';
  $: newsSources = news?.source_count ?? 0;
  $: newsItems = news?.item_count ?? 0;
  $: globalCountries = globalPanel?.country_count ?? 0;
  $: sourceLeaders = news
    ? Object.entries(news.source_counts ?? {})
        .sort((a, b) => b[1] - a[1])
        .slice(0, 6)
    : [];
  $: regionRows = news
    ? Object.entries(news.region_counts ?? {}).sort((a, b) => b[1] - a[1])
    : [];
  $: verticalRows = news
    ? Object.entries(news.vertical_counts ?? {})
        .sort((a, b) => b[1] - a[1])
        .slice(0, 8)
    : [];

  const reportTabs = [
    { id: 'modeling', label: 'Modeling' },
    { id: 'news', label: 'News' },
    { id: 'data', label: 'Data' }
  ];

  const promptRoutes = [
    { id: 'chat', label: 'Chat' },
    { id: 'economic-modeling-agent', label: 'Modeling' },
    { id: 'news-agent', label: 'News' },
    { id: 'analyst-agent', label: 'Analyst' }
  ];

  function activateThread(id) {
    activeThreadId = id;
  }

  function startThread() {
    const id = `thread-${Date.now()}`;
    threads.unshift({
      id,
      title: 'New investigation',
      subtitle: 'Prompt the Marco agents',
      status: 'New',
      unread: 0
    });
    messagesByThread = {
      ...messagesByThread,
      [id]: [
        {
          role: 'assistant',
          eyebrow: 'New thread',
          body:
            'Ask a question about the macro artifacts, news snapshot, or model results. With VITE_MARCO_AGENT_API set, this panel can call the deployed agent API.',
          context: []
        }
      ]
    };
    activeThreadId = id;
  }

  async function sendPrompt() {
    const text = promptText.trim();
    if (!text || sending) return;

    appendMessage(activeThreadId, { role: 'user', body: text });
    promptText = '';
    sending = true;

    try {
      const answer = apiBase ? await callAgentApi(text) : localAnswer(text);
      appendMessage(activeThreadId, answer);
    } catch (error) {
      appendMessage(activeThreadId, {
        role: 'assistant',
        eyebrow: 'Local fallback',
        body: `${localAnswer(text).body} The live agent API was unavailable: ${error.message}`,
        context: ['./artifacts/fred-fx-rate-lab-summary.json', './artifacts/macro-news-summary.json']
      });
    } finally {
      sending = false;
    }
  }

  async function callAgentApi(text) {
    const endpoint = route === 'chat' ? '/v1/chat' : `/v1/agents/${route}/prompt`;
    const response = await fetch(`${apiBase}${endpoint}`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ prompt: text })
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    return {
      role: 'assistant',
      eyebrow: route === 'chat' ? 'Chat agent' : labelForRoute(route),
      body: payload.response ?? payload.answer ?? payload.text ?? JSON.stringify(payload, null, 2),
      context: payload.artifacts ?? payload.context ?? []
    };
  }

  function localAnswer(text) {
    const lower = text.toLowerCase();
    if (lower.includes('news') || route === 'news-agent') {
      return {
        role: 'assistant',
        eyebrow: 'News agent preview',
        body: `Current committed snapshot has ${formatNumber(newsItems)} macro/news records from ${newsSources} sources. The next agent job is to record each fetch, summarize only marginal information, and update model.md with pruning at the token threshold.`,
        context: ['./artifacts/macro-news-summary.json']
      };
    }

    if (lower.includes('model') || lower.includes('backtest') || route === 'economic-modeling-agent') {
      return {
        role: 'assistant',
        eyebrow: 'Modeling agent preview',
        body: `The latest FRED FX/rate lab has ${formatNumber(fred?.headline?.prediction_rows)} predictions across ${fred?.pairs?.length ?? 0} pairs and ${fred?.horizons?.length ?? 0} horizons. Baselines win ${baselineWins}/${contestCount} RMSE contests, so the honest claim is benchmark discipline plus extensible data plumbing.`,
        context: ['./artifacts/fred-fx-rate-lab-summary.json']
      };
    }

    if (lower.includes('data') || lower.includes('coverage')) {
      return {
        role: 'assistant',
        eyebrow: 'Data coverage',
        body: `The global macro panel currently covers ${globalCountries} countries and ${globalPanel?.feature_count ?? 0} normalized features. It is useful as a schema and ingestion proof, not a complete global macro warehouse yet.`,
        context: ['./artifacts/global-macro-panel-summary.json']
      };
    }

    return {
      role: 'assistant',
      eyebrow: 'Chat agent preview',
      body:
        'The strongest demo story is a four-agent Marco workbench: three specialist agents publish auditable reports, and the chat agent uses those artifacts as context while routing specialist prompts back to the worker APIs.',
      context: [
        './artifacts/fred-fx-rate-lab-summary.json',
        './artifacts/macro-news-summary.json',
        './artifacts/global-macro-panel-summary.json'
      ]
    };
  }

  function appendMessage(threadId, message) {
    messagesByThread = {
      ...messagesByThread,
      [threadId]: [...(messagesByThread[threadId] ?? []), message]
    };
  }

  function labelForRoute(id) {
    return promptRoutes.find((item) => item.id === id)?.label ?? id;
  }

  function formatNumber(value) {
    if (value === null || value === undefined || Number.isNaN(value)) return 'n/a';
    return Number(value).toLocaleString();
  }

  function handleComposerKeydown(event) {
    if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
      event.preventDefault();
      sendPrompt();
    }
  }
</script>

<main class="workbench" aria-label="Marco agent workbench">
  <aside class="thread-rail" aria-label="Chat threads">
    <div class="brand-block">
      <div>
        <p class="eyebrow">Marco</p>
        <h1>Macro agent workbench</h1>
      </div>
      <span class="live-dot">Node A ready</span>
    </div>

    <button class="new-thread" type="button" on:click={startThread}>New Thread</button>

    <nav class="thread-list" aria-label="Available threads">
      {#each threads as thread}
        <button
          class:active={thread.id === activeThreadId}
          class="thread-button"
          type="button"
          on:click={() => activateThread(thread.id)}
        >
          <span>
            <strong>{thread.title}</strong>
            <small>{thread.subtitle}</small>
          </span>
          <em>{thread.unread ? thread.unread : thread.status}</em>
        </button>
      {/each}
    </nav>

    <div class="agent-stack" aria-label="Worker agents">
      <p class="section-label">Worker APIs</p>
      {#each agents as agent}
        <button
          class={`agent-row ${agent.accent}`}
          type="button"
          on:click={() => {
            route = agent.id;
            promptText = `Ask the ${agent.label.toLowerCase()} agent for a current status report.`;
          }}
        >
          <span>{agent.label}</span>
          <small>{agent.state}</small>
        </button>
      {/each}
    </div>
  </aside>

  <section class="conversation-panel" aria-label="Open conversation">
    <header class="conversation-header">
      <div>
        <p class="eyebrow">Open session</p>
        <h2>{activeThread.title}</h2>
        <p>{activeThread.subtitle}</p>
      </div>
      <div class="route-actions" aria-label="Quick agent routes">
        {#each promptRoutes.slice(1) as item}
          <button
            type="button"
            class:active={route === item.id}
            on:click={() => (route = item.id)}
          >
            {item.label}
          </button>
        {/each}
      </div>
    </header>

    <div class="metrics-strip" aria-label="Current artifact metrics">
      <div>
        <span>News</span>
        <strong>{formatNumber(newsItems)}</strong>
        <small>{newsSources} sources</small>
      </div>
      <div>
        <span>Backtests</span>
        <strong>{baselineWins}/{contestCount}</strong>
        <small>baseline wins</small>
      </div>
      <div>
        <span>Macro panel</span>
        <strong>{globalCountries}</strong>
        <small>countries</small>
      </div>
      <div>
        <span>Vintage</span>
        <strong>{latestVintage}</strong>
        <small>{fred?.lookahead_status?.replaceAll('_', ' ') ?? 'loading'}</small>
      </div>
    </div>

    {#if loadError}
      <div class="load-error">{loadError}</div>
    {/if}

    <div class="message-stream" aria-live="polite">
      {#each activeMessages as message}
        <article class={`message ${message.role}`}>
          {#if message.eyebrow}
            <p class="message-eyebrow">{message.eyebrow}</p>
          {/if}
          <p>{message.body}</p>
          {#if message.context?.length}
            <div class="context-row" aria-label="Evidence">
              {#each message.context as item}
                <span>{item}</span>
              {/each}
            </div>
          {/if}
        </article>
      {/each}
      {#if sending}
        <article class="message assistant pending">
          <p class="message-eyebrow">Working</p>
          <p>Routing prompt to {labelForRoute(route)}...</p>
        </article>
      {/if}
    </div>

    <form
      class="composer"
      on:submit|preventDefault={sendPrompt}
      aria-label="Prompt Marco agents"
    >
      <label>
        <span>Route</span>
        <select bind:value={route}>
          {#each promptRoutes as item}
            <option value={item.id}>{item.label}</option>
          {/each}
        </select>
      </label>
      <textarea
        bind:value={promptText}
        rows="2"
        placeholder="Ask what changed in the macro news, request a model status, or draft an investor explanation..."
        on:keydown={handleComposerKeydown}
      />
      <button type="submit" disabled={!promptText.trim() || sending}>Send</button>
    </form>
  </section>

  <aside class="artifact-panel" aria-label="Reports and artifacts">
    <header>
      <div>
        <p class="eyebrow">Evidence</p>
        <h2>Reports & artifacts</h2>
      </div>
      <span>{apiBase ? 'API connected' : 'static preview'}</span>
    </header>

    <div class="tab-row" role="tablist" aria-label="Report sections">
      {#each reportTabs as tab}
        <button
          type="button"
          role="tab"
          aria-selected={selectedReport === tab.id}
          class:active={selectedReport === tab.id}
          on:click={() => (selectedReport = tab.id)}
        >
          {tab.label}
        </button>
      {/each}
    </div>

    {#if selectedReport === 'modeling'}
      <section class="report-block">
        <p class="section-label">FRED FX/rate lab</p>
        <h3>{fred?.headline?.status ?? 'loading'} benchmark checkpoint</h3>
        <p>{fred?.headline?.model_result ?? 'Loading modeling artifact...'}</p>
        <dl class="compact-dl">
          <div>
            <dt>Pairs</dt>
            <dd>{fred?.pairs?.join(', ') ?? 'n/a'}</dd>
          </div>
          <div>
            <dt>Horizons</dt>
            <dd>{fred?.horizons?.map((item) => `${item}M`).join(', ') ?? 'n/a'}</dd>
          </div>
          <div>
            <dt>Rows</dt>
            <dd>{formatNumber(fred?.headline?.prediction_rows)} predictions</dd>
          </div>
          <div>
            <dt>Non-baseline wins</dt>
            <dd>{modelWins}</dd>
          </div>
        </dl>
      </section>
    {:else if selectedReport === 'news'}
      <section class="report-block">
        <p class="section-label">Macro news agent</p>
        <h3>{formatNumber(newsItems)} committed records</h3>
        <p>
          Current news scope emphasizes central banks, financial stability, India,
          Japan, Europe, the UK, and US policy material. The next runtime job is
          marginal information compression into model.md.
        </p>
        <div class="rank-list">
          {#each regionRows as [region, count]}
            <div>
              <span>{region}</span>
              <strong>{count}</strong>
            </div>
          {/each}
        </div>
        <div class="tag-cloud" aria-label="Top news verticals">
          {#each verticalRows as [vertical, count]}
            <span>{vertical.replaceAll('_', ' ')} · {count}</span>
          {/each}
        </div>
      </section>
    {:else}
      <section class="report-block">
        <p class="section-label">Global macro panel</p>
        <h3>{globalCountries} countries, {globalPanel?.feature_count ?? 0} features</h3>
        <p>
          This is the normalized starter shape for official macro data expansion.
          It proves source ingestion and mapping before coupling anything to
          uploads or the experiment runner.
        </p>
        <div class="country-grid" aria-label="Countries in panel">
          {#each globalPanel?.countries ?? [] as country}
            <span>{country}</span>
          {/each}
        </div>
        <div class="tag-cloud" aria-label="Panel features">
          {#each globalPanel?.features ?? [] as feature}
            <span>{feature.replaceAll('_', ' ')}</span>
          {/each}
        </div>
      </section>
    {/if}

    <section class="artifact-links">
      <p class="section-label">Committed JSON</p>
      {#each Object.values(artifactSpecs) as artifact}
        <a href={artifact.path}>{artifact.label}</a>
      {/each}
    </section>

    {#if sourceLeaders.length}
      <section class="report-block source-block">
        <p class="section-label">Largest news sources</p>
        {#each sourceLeaders as [source, count]}
          <div class="source-row">
            <span>{source}</span>
            <strong>{count}</strong>
          </div>
        {/each}
      </section>
    {/if}
  </aside>
</main>
