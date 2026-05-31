<script>
  const artifactUrl = './artifacts/fred-fx-rate-lab-summary.json';
  const globalPanelUrl = './artifacts/global-macro-panel-summary.json';

  let data = null;
  let globalPanel = null;
  let error = null;
  let selectedPair = 'USD_CAD';
  let selectedHorizon = 6;

  const modelLabels = {
    random_walk: 'Random walk',
    no_change: 'No change',
    rolling_mean_36m: 'Rolling mean',
    carry_diff: 'Carry diff',
    real_rate_diff: 'Real-rate diff',
    ridge: 'Ridge'
  };

  const audienceLanes = [
    {
      role: 'Investor',
      title: 'Not an alpha claim yet',
      body: 'The honest baselines still win nearly everywhere. The asset here is a clean research machine, not a cherry-picked strategy.'
    },
    {
      role: 'Economist',
      title: 'Rate differentials need stronger structure',
      body: 'Simple nominal, real-rate, and carry-style signals are being tested against random-walk/no-change targets before more theory is layered in.'
    },
    {
      role: 'Neuroscientist',
      title: 'Noise floor is visible',
      body: 'The dashboard makes the benchmark failure mode obvious: weak directional signal can look plausible until RMSE is compared against inertia.'
    },
    {
      role: 'Data Engineering',
      title: 'Artifacts are inspectable',
      body: 'Committed JSON summaries, CLI commands, API routes, hashes, source IDs, and vintage labels keep the research surface reproducible.'
    }
  ];

  fetch(artifactUrl)
    .then((response) => {
      if (!response.ok) throw new Error(`artifact fetch failed: ${response.status}`);
      return response.json();
    })
    .then((payload) => {
      data = payload;
      selectedPair = payload.pairs.includes(selectedPair) ? selectedPair : payload.pairs[0];
      selectedHorizon = payload.horizons.includes(selectedHorizon)
        ? selectedHorizon
        : payload.horizons[0];
    })
    .catch((err) => {
      error = err.message;
    });

  fetch(globalPanelUrl)
    .then((response) => {
      if (!response.ok) throw new Error(`global panel artifact fetch failed: ${response.status}`);
      return response.json();
    })
    .then((payload) => {
      globalPanel = payload;
    })
    .catch(() => {
      globalPanel = null;
    });

  $: selectedRows = data
    ? data.metrics
        .filter((row) => row.pair === selectedPair && row.horizon_months === selectedHorizon)
        .sort((a, b) => a.rmse - b.rmse)
    : [];

  $: maxRmse = selectedRows.length ? Math.max(...selectedRows.map((row) => row.rmse)) : 0;
  $: minRmse = selectedRows.length ? Math.min(...selectedRows.map((row) => row.rmse)) : 0;
  $: bestSelected = selectedRows[0] ?? null;
  $: baselineSelected =
    selectedRows.find((row) => row.model_id === 'random_walk') ??
    selectedRows.find((row) => row.model_id === 'no_change') ??
    null;
  $: selectedLift = bestSelected && baselineSelected ? baselineSelected.rmse - bestSelected.rmse : 0;

  $: heatmapRows = data
    ? [...data.best_by_rmse].sort((a, b) =>
        a.pair === b.pair ? a.horizon_months - b.horizon_months : a.pair.localeCompare(b.pair)
      )
    : [];

  $: baselineWins = data
    ? data.best_by_rmse.filter((row) => ['random_walk', 'no_change'].includes(row.best_model)).length
    : 0;
  $: totalContests = data ? data.best_by_rmse.length : 0;
  $: modelWins = data ? modelWinRows(data.best_by_rmse) : [];
  $: maxModelWins = modelWins.length ? Math.max(...modelWins.map((row) => row.count)) : 0;
  $: bestNonBaseline = data
    ? data.best_by_rmse
        .filter((row) => !['random_walk', 'no_change'].includes(row.best_model))
        .sort((a, b) => b.rmse_improvement_vs_random_walk - a.rmse_improvement_vs_random_walk)[0]
    : null;
  $: coverageFeatures = globalPanel ? globalPanel.features : [];
  $: sourceRows = globalPanel ? globalPanel.sources.filter((row) => row.source_id === 'world_bank_indicators') : [];

  function modelWinRows(rows) {
    const counts = new Map();
    rows.forEach((row) => counts.set(row.best_model, (counts.get(row.best_model) ?? 0) + 1));
    return Array.from(counts, ([model_id, count]) => ({ model_id, count })).sort((a, b) => b.count - a.count);
  }

  function pct(value) {
    if (value === null || value === undefined || Number.isNaN(value)) return 'n/a';
    return `${(value * 100).toFixed(1)}%`;
  }

  function num(value) {
    if (value === null || value === undefined || Number.isNaN(value)) return 'n/a';
    return value.toFixed(5);
  }

  function signedNum(value) {
    if (value === null || value === undefined || Number.isNaN(value)) return 'n/a';
    const sign = value > 0 ? '+' : '';
    return `${sign}${value.toFixed(5)}`;
  }

  function compactFeature(value) {
    return value.replaceAll('_', ' ');
  }

  function improvementClass(value) {
    if (value > 0.0001) return 'good';
    if (value < -0.0001) return 'bad';
    return 'flat';
  }

  function heatClass(row) {
    if (['random_walk', 'no_change'].includes(row.best_model)) return 'baseline';
    if (row.rmse_improvement_vs_random_walk > 0.0001) return 'model';
    return 'flat';
  }
</script>

{#if error}
  <main class="shell">
    <section class="notice">
      <h1>Artifact Load Failed</h1>
      <p>{error}</p>
    </section>
  </main>
{:else if !data}
  <main class="shell">
    <section class="notice">
      <h1>Loading Marco Macro Lab</h1>
    </section>
  </main>
{:else}
  <main class="shell">
    <header class="hero">
      <div class="hero-copy">
        <p class="eyebrow">Marco Macro Lab</p>
        <h1>Macro data foundation, backtesting discipline, and evidence quality in one view.</h1>
        <p class="hero-text">
          Current checkpoint: FX/rate differential baselines over FRED data plus an official
          World Bank/ECB starter panel for global macro expansion.
        </p>
      </div>
      <div class="hero-aside">
        <div class="status-pill">{data.headline.status}</div>
        <div class="signal-score">
          <span>Baseline wins</span>
          <strong>{baselineWins}/{totalContests}</strong>
        </div>
        <p>{data.vintage_policy.replaceAll('_', ' ')}</p>
      </div>
    </header>

    <section class="kpi-band" aria-label="Research artifact summary">
      <div>
        <span>FX pairs</span>
        <strong>{data.pairs.length}</strong>
      </div>
      <div>
        <span>Predictions</span>
        <strong>{data.headline.prediction_rows.toLocaleString()}</strong>
      </div>
      <div>
        <span>Feature rows</span>
        <strong>{data.headline.features_rows.toLocaleString()}</strong>
      </div>
      <div>
        <span>Global panel rows</span>
        <strong>{globalPanel ? globalPanel.panel_rows.toLocaleString() : 'n/a'}</strong>
      </div>
      <div>
        <span>Source policy</span>
        <strong>{data.lookahead_status.replaceAll('_', ' ')}</strong>
      </div>
    </section>

    <section class="verdict-band">
      <div>
        <p class="section-kicker">Main read</p>
        <h2>{data.headline.model_result}</h2>
      </div>
      <p>
        Treat this as infrastructure evidence: the system can ingest, normalize, benchmark,
        and publish comparable artifacts, while clearly labeling that this is not
        real-time vintage-safe evidence.
      </p>
    </section>

    <section class="audience-grid" aria-label="Audience interpretation">
      {#each audienceLanes as lane}
        <article class="audience-card">
          <span>{lane.role}</span>
          <h2>{lane.title}</h2>
          <p>{lane.body}</p>
        </article>
      {/each}
    </section>

    {#if globalPanel}
      <section class="section-block">
        <div class="section-heading">
          <div>
            <p class="section-kicker">Official source coverage</p>
            <h2>Global macro starter panel</h2>
          </div>
          <a class="text-link" href="./artifacts/global-macro-panel-summary.json">JSON artifact</a>
        </div>

        <div class="coverage-layout">
          <div class="coverage-map" aria-label="Country feature coverage">
            <div class="coverage-head country-label">Country</div>
            {#each coverageFeatures as feature}
              <div class="coverage-head">{compactFeature(feature)}</div>
            {/each}
            {#each globalPanel.countries as country}
              <div class="country-label">{country}</div>
              {#each coverageFeatures as feature}
                <div class="coverage-cell" title={`${country} ${compactFeature(feature)}`}>
                  <span></span>
                </div>
              {/each}
            {/each}
          </div>

          <div class="source-panel">
            <h2>Data haul</h2>
            <dl>
              <div>
                <dt>Countries</dt>
                <dd>{globalPanel.country_count}</dd>
              </div>
              <div>
                <dt>Years</dt>
                <dd>{globalPanel.years[0]}-{globalPanel.years[globalPanel.years.length - 1]}</dd>
              </div>
              <div>
                <dt>World Bank obs</dt>
                <dd>{globalPanel.world_bank_observations.toLocaleString()}</dd>
              </div>
              <div>
                <dt>ECB smoke obs</dt>
                <dd>{globalPanel.ecb_observations}</dd>
              </div>
            </dl>
            <div class="source-list">
              {#each sourceRows as row}
                <span>{row.indicator_code}</span>
              {/each}
            </div>
            <div class="artifact-links">
              <span>CLI: emf-macro global-panel-summary</span>
              <span>API: /v1/global-panel</span>
            </div>
          </div>
        </div>
      </section>
    {/if}

    <section class="section-block">
      <div class="section-heading">
        <div>
          <p class="section-kicker">Backtest result shape</p>
          <h2>Baseline dominance by pair and horizon</h2>
        </div>
        {#if bestNonBaseline}
          <span class="annotation">
            Best non-baseline: {bestNonBaseline.pair} {bestNonBaseline.horizon_months}M,
            {modelLabels[bestNonBaseline.best_model] ?? bestNonBaseline.best_model}
          </span>
        {/if}
      </div>

      <div class="matrix">
        {#each heatmapRows as row}
          <button
            class={`matrix-cell ${heatClass(row)}`}
            type="button"
            on:click={() => {
              selectedPair = row.pair;
              selectedHorizon = row.horizon_months;
            }}
          >
            <span>{row.pair} {row.horizon_months}M</span>
            <strong>{modelLabels[row.best_model] ?? row.best_model}</strong>
            <em>{signedNum(row.rmse_improvement_vs_random_walk)}</em>
          </button>
        {/each}
      </div>
    </section>

    <section class="analysis-layout">
      <div class="section-block">
        <div class="section-heading compact">
          <div>
            <p class="section-kicker">Interactive slice</p>
            <h2>{selectedPair} at {selectedHorizon}M</h2>
          </div>
          <div class="controls">
            <label>
              Pair
              <select bind:value={selectedPair}>
                {#each data.pairs as pair}
                  <option value={pair}>{pair}</option>
                {/each}
              </select>
            </label>
            <label>
              Horizon
              <select bind:value={selectedHorizon}>
                {#each data.horizons as horizon}
                  <option value={horizon}>{horizon}M</option>
                {/each}
              </select>
            </label>
          </div>
        </div>

        <div class="chart-summary">
          <div>
            <span>Best model</span>
            <strong>{bestSelected ? modelLabels[bestSelected.model_id] ?? bestSelected.model_id : 'n/a'}</strong>
          </div>
          <div>
            <span>RMSE lift vs random walk</span>
            <strong class={improvementClass(selectedLift)}>{signedNum(selectedLift)}</strong>
          </div>
        </div>

        <div class="bars">
          {#each selectedRows as row}
            <div class="bar-row">
              <div class="bar-label">{modelLabels[row.model_id] ?? row.model_id}</div>
              <div class="bar-track">
                <div
                  class:selected={row.rmse === minRmse}
                  class="bar"
                  style={`width: ${(row.rmse / maxRmse) * 100}%`}
                ></div>
              </div>
              <div class="bar-value">{num(row.rmse)}</div>
            </div>
          {/each}
        </div>
      </div>

      <div class="section-block">
        <div class="section-heading compact">
          <div>
            <p class="section-kicker">Model scoreboard</p>
            <h2>Wins by RMSE</h2>
          </div>
        </div>
        <div class="win-bars">
          {#each modelWins as row}
            <div>
              <span>{modelLabels[row.model_id] ?? row.model_id}</span>
              <strong>{row.count}</strong>
              <div class="mini-track">
                <i style={`width: ${(row.count / maxModelWins) * 100}%`}></i>
              </div>
            </div>
          {/each}
        </div>
      </div>
    </section>

    <section class="section-block">
      <div class="section-heading">
        <div>
          <p class="section-kicker">Audit table</p>
          <h2>Selected model metrics</h2>
        </div>
        <span class="annotation">{selectedPair}, {selectedHorizon}M</span>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Model</th>
              <th>MAE</th>
              <th>RMSE</th>
              <th>Direction</th>
              <th>N</th>
            </tr>
          </thead>
          <tbody>
            {#each selectedRows as row}
              <tr>
                <td>{modelLabels[row.model_id] ?? row.model_id}</td>
                <td>{num(row.mae)}</td>
                <td>{num(row.rmse)}</td>
                <td>{pct(row.directional_accuracy)}</td>
                <td>{row.n}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </section>

    <footer>
      <span>Run {data.run_id}</span>
      <a href="https://github.com/yusefmosiah/Marco">GitHub</a>
    </footer>
  </main>
{/if}
