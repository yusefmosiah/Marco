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

  $: heatmapRows = data
    ? data.best_by_rmse.sort((a, b) =>
        a.pair === b.pair ? a.horizon_months - b.horizon_months : a.pair.localeCompare(b.pair)
      )
    : [];

  function pct(value) {
    if (value === null || value === undefined || Number.isNaN(value)) return 'n/a';
    return `${(value * 100).toFixed(1)}%`;
  }

  function num(value) {
    if (value === null || value === undefined || Number.isNaN(value)) return 'n/a';
    return value.toFixed(5);
  }

  function improvementClass(value) {
    if (value > 0.0001) return 'good';
    if (value < -0.0001) return 'bad';
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
      <h1>Loading Marco FX/Rate Lab</h1>
    </section>
  </main>
{:else}
  <main class="shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">Marco Macro Lab</p>
        <h1>FX/Rate Differential Backtest</h1>
      </div>
      <a class="repo-link" href="https://github.com/yusefmosiah/Marco">GitHub</a>
    </header>

    <section class="summary-grid">
      <div class="metric">
        <span>Status</span>
        <strong>{data.headline.status}</strong>
      </div>
      <div class="metric">
        <span>Pairs</span>
        <strong>{data.pairs.length}</strong>
      </div>
      <div class="metric">
        <span>Predictions</span>
        <strong>{data.headline.prediction_rows.toLocaleString()}</strong>
      </div>
      <div class="metric wide">
        <span>Vintage Policy</span>
        <strong>{data.vintage_policy.replaceAll('_', ' ')}</strong>
      </div>
    </section>

    <section class="callout">
      <h2>Result</h2>
      <p>{data.headline.model_result}</p>
      <p class="caution">
        This is a latest-revised-snapshot backtest, not real-time ALFRED/vintage-safe evidence.
      </p>
    </section>

    {#if globalPanel}
      <section class="panel">
        <div class="panel-title">
          <h2>Global Macro Data Haul</h2>
          <span>{globalPanel.vintage_policy.replaceAll('_', ' ')}</span>
        </div>
        <div class="summary-grid embedded">
          <div class="metric">
            <span>Countries</span>
            <strong>{globalPanel.country_count}</strong>
          </div>
          <div class="metric">
            <span>Years</span>
            <strong>{globalPanel.year_count}</strong>
          </div>
          <div class="metric">
            <span>Panel Rows</span>
            <strong>{globalPanel.panel_rows.toLocaleString()}</strong>
          </div>
          <div class="metric">
            <span>WB Obs</span>
            <strong>{globalPanel.world_bank_observations.toLocaleString()}</strong>
          </div>
        </div>
        <p class="panel-copy">
          {globalPanel.countries.join(', ')} across {globalPanel.features.join(', ')}.
          ECB observations: {globalPanel.ecb_observations}.
        </p>
      </section>
    {/if}

    <section class="controls">
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
    </section>

    <section class="panel">
      <div class="panel-title">
        <h2>{selectedPair} {selectedHorizon}M RMSE</h2>
        <span>Lower is better</span>
      </div>

      <div class="bars">
        {#each selectedRows as row}
          <div class="bar-row">
            <div class="bar-label">{modelLabels[row.model_id] ?? row.model_id}</div>
            <div class="bar-track">
              <div
                class:selected={row.rmse === selectedRows[0].rmse}
                class="bar"
                style={`width: ${(row.rmse / maxRmse) * 100}%`}
              ></div>
            </div>
            <div class="bar-value">{num(row.rmse)}</div>
          </div>
        {/each}
      </div>
    </section>

    <section class="panel">
      <div class="panel-title">
        <h2>Best Model By Pair/Horizon</h2>
        <span>RMSE improvement vs random walk</span>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Pair</th>
              <th>Horizon</th>
              <th>Best</th>
              <th>Best RMSE</th>
              <th>RW RMSE</th>
              <th>Delta</th>
              <th>N</th>
            </tr>
          </thead>
          <tbody>
            {#each heatmapRows as row}
              <tr>
                <td>{row.pair}</td>
                <td>{row.horizon_months}M</td>
                <td>{modelLabels[row.best_model] ?? row.best_model}</td>
                <td>{num(row.best_rmse)}</td>
                <td>{num(row.random_walk_rmse)}</td>
                <td class={improvementClass(row.rmse_improvement_vs_random_walk)}>
                  {num(row.rmse_improvement_vs_random_walk)}
                </td>
                <td>{row.n}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </section>

    <section class="panel">
      <div class="panel-title">
        <h2>Selected Model Metrics</h2>
        <span>{selectedPair}, {selectedHorizon}M</span>
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
      <span>{data.lookahead_status.replaceAll('_', ' ')}</span>
    </footer>
  </main>
{/if}
