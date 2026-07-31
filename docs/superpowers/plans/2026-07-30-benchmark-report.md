# Benchmark Report on gh-benchmarks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist the cog and mosaic workflows' benchmark JSON to the existing `gh-benchmarks` branch on every push to `main`, and serve a static, client-side-rendered HTML dashboard from that branch (via GitHub Pages).

**Architecture:** Both workflows already produce `benchmark.json` (pytest-benchmark stats) and `siege_results.json` (load-test stats). Two small jq shape fixes make that data self-describing (service name as its own field; commit/datetime preserved). New workflow steps checkout `gh-benchmarks` into a subdirectory, copy the job's two JSON files into `cog/` or `mosaic/`, and push with a hand-rolled fetch+rebase+retry script (plus a per-workflow `concurrency:` group) — gated to `push` events only. A single static `index.html`, committed once to `gh-benchmarks`, fetches those four JSON files client-side and renders grouped bar charts + tables. No build step, no server-side templating, no history — always shows the latest run.

**Tech Stack:** GitHub Actions (YAML), jq, plain HTML/CSS/JS (no framework), git.

**Spec:** `docs/superpowers/specs/2026-07-30-benchmark-report-design.md`

---

## File Structure

- Modify: `.gitignore` — ignore generated benchmark artifacts at repo root
- Modify: `.github/workflows/benchmark-cog.yml` — jq shape fixes + publish-to-gh-benchmarks steps
- Modify: `.github/workflows/benchmark-mosaic.yml` — same
- Create (on the `gh-benchmarks` branch, via a git worktree, not on `main`): `index.html`

---

### Task 1: Ignore generated benchmark artifacts on `main`

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Add the generated filenames to `.gitignore`**

These four files are produced at the repo root by both workflows (and by
running the benchmarks locally) and must never be committed to `main` — they
only ever live on `gh-benchmarks`.

Edit `.gitignore`, appending after the `.superpowers/` line added during
brainstorming:

```gitignore
.superpowers/

# Generated benchmark artifacts (published to gh-benchmarks, not main)
/benchmark.json
/output.json
/results.json
/siege_results.json
```

- [ ] **Step 2: Verify the untracked local files are now ignored**

Run: `git status --porcelain`
Expected: `benchmark.json` and `output.json` (currently untracked, left over
from a local run) no longer appear in the output.

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: ignore generated benchmark artifacts on main"
```

---

### Task 2: Preserve commit/datetime in `benchmark-cog.yml`'s benchmark.json

**Files:**
- Modify: `.github/workflows/benchmark-cog.yml`

The current jq reduces pytest-benchmark's output to a bare array, discarding
`commit_info` and `datetime` — but the report header needs both. Fix by
wrapping the array and keeping those two fields, in one jq call instead of
two.

- [ ] **Step 1: Verify the jq transform locally against a real fixture**

Run this to reproduce the exact transform in isolation, using the actual
sample pytest-benchmark output already sitting in the repo root:

```bash
cat /Users/vincentsarago/Dev/Devseed/titiler-benchmark/benchmark.json \
  | jq '.benchmarks[0]' > /dev/null # sanity: confirms .benchmarks[] exists
jq '{commit_info: .commit_info, datetime: .datetime, benchmarks: [.benchmarks[] | {name: .name, group: .group, stats: .stats}]}' \
  /Users/vincentsarago/Dev/Devseed/titiler-benchmark/benchmark.json \
  | jq 'keys, (.benchmarks[0] | keys)'
```

Expected output:

```
[
  "benchmarks",
  "commit_info",
  "datetime"
]
[
  "group",
  "name",
  "stats"
]
```

- [ ] **Step 2: Edit the workflow**

In `.github/workflows/benchmark-cog.yml`, replace:

```yaml
      - name: Run Benchmark
        run: |
          uv run pytest ./cog/benchmarks.py --benchmark-sort name --benchmark-columns 'min, max, mean, median' --benchmark-json output.json
          cat output.json | jq '.benchmarks[] | {"name": .name, "group": .group, "stats": .stats}' | jq '[inputs]' > benchmark.json
```

with:

```yaml
      - name: Run Benchmark
        run: |
          uv run pytest ./cog/benchmarks.py --benchmark-sort name --benchmark-columns 'min, max, mean, median' --benchmark-json output.json
          cat output.json | jq '{commit_info: .commit_info, datetime: .datetime, benchmarks: [.benchmarks[] | {name: .name, group: .group, stats: .stats}]}' > benchmark.json
```

- [ ] **Step 3: Validate YAML syntax**

Run: `uv run --with pyyaml python -c "import yaml; yaml.safe_load(open('.github/workflows/benchmark-cog.yml')); print('valid')"`
Expected: `valid`

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/benchmark-cog.yml
git commit -m "fix: preserve commit_info/datetime in cog benchmark.json"
```

---

### Task 3: Split service name into its own field in `benchmark-cog.yml`'s siege output

**Files:**
- Modify: `.github/workflows/benchmark-cog.yml`

- [ ] **Step 1: Verify the jq transform locally**

```bash
echo '{"elapsed_time": 87.10, "concurrency": 7.10, "response_time": 309.08, "transaction_rate": 22.96}' \
  | jq '{"service": "titiler", "name": "elapsed_time", "unit": "s", "value": .elapsed_time}, {"service": "titiler", "name": "concurrency", "unit": "Count", "value": .concurrency}, {"service": "titiler", "name": "response_time", "unit": "s", "value": .response_time}, {"service": "titiler", "name": "transaction_rate", "unit": "trans/sec", "value": .transaction_rate}'
```

Expected output (4 objects, each with `service`, `name`, `unit`, `value`):

```json
{
  "service": "titiler",
  "name": "elapsed_time",
  "unit": "s",
  "value": 87.1
}
{
  "service": "titiler",
  "name": "concurrency",
  "unit": "Count",
  "value": 7.1
}
{
  "service": "titiler",
  "name": "response_time",
  "unit": "s",
  "value": 309.08
}
{
  "service": "titiler",
  "name": "transaction_rate",
  "unit": "trans/sec",
  "value": 22.96
}
```

- [ ] **Step 2: Edit the "Run siege (titiler)" step**

Replace:

```yaml
      - name: Run siege (titiler)
        run: |
          siege --file ./cog/urls.txt -b -c 10 -r 200 --json-output 2>&1 | jq -c > results.json
          echo "Benchmark Results"
          cat results.json | jq
          cat results.json | jq '{"name": "titiler elapsed_time", "unit": "s", "value": .elapsed_time}, {"name": "titiler concurrency", "unit": "Count", "value": .concurrency}, {"name": "titiler response_time", "unit": "s", "value": .response_time}, {"name": "titiler transaction_rate", "unit": "trans/sec", "value": .transaction_rate}' > output.json
        env:
          URLPATH: cog/tiles/WebMercatorQuad/
          PORT: 8080
          HOST: 127.0.0.1
```

with:

```yaml
      - name: Run siege (titiler)
        run: |
          siege --file ./cog/urls.txt -b -c 10 -r 200 --json-output 2>&1 | jq -c > results.json
          echo "Benchmark Results"
          cat results.json | jq
          cat results.json | jq '{"service": "titiler", "name": "elapsed_time", "unit": "s", "value": .elapsed_time}, {"service": "titiler", "name": "concurrency", "unit": "Count", "value": .concurrency}, {"service": "titiler", "name": "response_time", "unit": "s", "value": .response_time}, {"service": "titiler", "name": "transaction_rate", "unit": "trans/sec", "value": .transaction_rate}' > output.json
        env:
          URLPATH: cog/tiles/WebMercatorQuad/
          PORT: 8080
          HOST: 127.0.0.1
```

- [ ] **Step 3: Edit the "Run siege (async-titiler)" step**

Replace:

```yaml
      - name: Run siege (async-titiler)
        run: |
          siege --file ./cog/urls.txt -b -c 10 -r 200 --json-output 2>&1 | jq -c > results.json
          echo "Benchmark Results"
          cat results.json | jq
          cat results.json | jq '{"name": "async-titiler elapsed_time", "unit": "s", "value": .elapsed_time}, {"name": "async-titiler concurrency", "unit": "Count", "value": .concurrency}, {"name": "async-titiler response_time", "unit": "s", "value": .response_time}, {"name": "async-titiler transaction_rate", "unit": "trans/sec", "value": .transaction_rate}' >> output.json
        env:
          URLPATH: geotiff/tiles/WebMercatorQuad/
          PORT: 8081
          HOST: 127.0.0.1          
```

with:

```yaml
      - name: Run siege (async-titiler)
        run: |
          siege --file ./cog/urls.txt -b -c 10 -r 200 --json-output 2>&1 | jq -c > results.json
          echo "Benchmark Results"
          cat results.json | jq
          cat results.json | jq '{"service": "async-titiler", "name": "elapsed_time", "unit": "s", "value": .elapsed_time}, {"service": "async-titiler", "name": "concurrency", "unit": "Count", "value": .concurrency}, {"service": "async-titiler", "name": "response_time", "unit": "s", "value": .response_time}, {"service": "async-titiler", "name": "transaction_rate", "unit": "trans/sec", "value": .transaction_rate}' >> output.json
        env:
          URLPATH: geotiff/tiles/WebMercatorQuad/
          PORT: 8081
          HOST: 127.0.0.1          
```

- [ ] **Step 4: Validate YAML syntax**

Run: `uv run --with pyyaml python -c "import yaml; yaml.safe_load(open('.github/workflows/benchmark-cog.yml')); print('valid')"`
Expected: `valid`

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/benchmark-cog.yml
git commit -m "fix: split service name into its own field in cog siege output"
```

---

### Task 4: Preserve commit/datetime in `benchmark-mosaic.yml`'s benchmark.json

**Files:**
- Modify: `.github/workflows/benchmark-mosaic.yml`

- [ ] **Step 1: Edit the workflow**

Replace:

```yaml
      - name: Run Benchmark
        run: |
          uv run pytest ./mosaic/benchmarks.py --benchmark-sort name --benchmark-columns 'min, max, mean, median' --benchmark-json output.json
          cat output.json | jq '.benchmarks[] | {"name": .name, "group": .group, "stats": .stats}' | jq '[inputs]' > benchmark.json
```

with:

```yaml
      - name: Run Benchmark
        run: |
          uv run pytest ./mosaic/benchmarks.py --benchmark-sort name --benchmark-columns 'min, max, mean, median' --benchmark-json output.json
          cat output.json | jq '{commit_info: .commit_info, datetime: .datetime, benchmarks: [.benchmarks[] | {name: .name, group: .group, stats: .stats}]}' > benchmark.json
```

- [ ] **Step 2: Validate YAML syntax**

Run: `uv run --with pyyaml python -c "import yaml; yaml.safe_load(open('.github/workflows/benchmark-mosaic.yml')); print('valid')"`
Expected: `valid`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/benchmark-mosaic.yml
git commit -m "fix: preserve commit_info/datetime in mosaic benchmark.json"
```

---

### Task 5: Split service name into its own field in `benchmark-mosaic.yml`'s siege output

**Files:**
- Modify: `.github/workflows/benchmark-mosaic.yml`

- [ ] **Step 1: Edit the "Run siege (titiler-pgstac)" step**

Replace:

```yaml
      - name: Run siege (titiler-pgstac)
        run: |
          siege --file ./mosaic/urls.txt -b -c 10 -r 200 --json-output 2>&1 | jq -c > results.json
          echo "Benchmark Results"
          cat results.json | jq
          cat results.json | jq '{"name": "titiler-pgstac elapsed_time", "unit": "s", "value": .elapsed_time}, {"name": "titiler-pgstac concurrency", "unit": "Count", "value": .concurrency}, {"name": "titiler-pgstac response_time", "unit": "s", "value": .response_time}, {"name": "titiler-pgstac transaction_rate", "unit": "trans/sec", "value": .transaction_rate}' > output.json
        env:
          PORT: 8080
          HOST: 127.0.0.1
```

with:

```yaml
      - name: Run siege (titiler-pgstac)
        run: |
          siege --file ./mosaic/urls.txt -b -c 10 -r 200 --json-output 2>&1 | jq -c > results.json
          echo "Benchmark Results"
          cat results.json | jq
          cat results.json | jq '{"service": "titiler-pgstac", "name": "elapsed_time", "unit": "s", "value": .elapsed_time}, {"service": "titiler-pgstac", "name": "concurrency", "unit": "Count", "value": .concurrency}, {"service": "titiler-pgstac", "name": "response_time", "unit": "s", "value": .response_time}, {"service": "titiler-pgstac", "name": "transaction_rate", "unit": "trans/sec", "value": .transaction_rate}' > output.json
        env:
          PORT: 8080
          HOST: 127.0.0.1
```

- [ ] **Step 2: Edit the "Run siege (titiler-stacapi)" step**

Replace:

```yaml
      - name: Run siege (titiler-stacapi)
        run: |
          siege --file ./mosaic/urls.txt -b -c 10 -r 200 --json-output 2>&1 | jq -c > results.json
          echo "Benchmark Results"
          cat results.json | jq
          cat results.json | jq '{"name": "titiler-stacapi elapsed_time", "unit": "s", "value": .elapsed_time}, {"name": "titiler-stacapi concurrency", "unit": "Count", "value": .concurrency}, {"name": "titiler-stacapi response_time", "unit": "s", "value": .response_time}, {"name": "titiler-stacapi transaction_rate", "unit": "trans/sec", "value": .transaction_rate}' >> output.json
        env:
          PORT: 8081
          HOST: 127.0.0.1          
```

with:

```yaml
      - name: Run siege (titiler-stacapi)
        run: |
          siege --file ./mosaic/urls.txt -b -c 10 -r 200 --json-output 2>&1 | jq -c > results.json
          echo "Benchmark Results"
          cat results.json | jq
          cat results.json | jq '{"service": "titiler-stacapi", "name": "elapsed_time", "unit": "s", "value": .elapsed_time}, {"service": "titiler-stacapi", "name": "concurrency", "unit": "Count", "value": .concurrency}, {"service": "titiler-stacapi", "name": "response_time", "unit": "s", "value": .response_time}, {"service": "titiler-stacapi", "name": "transaction_rate", "unit": "trans/sec", "value": .transaction_rate}' >> output.json
        env:
          PORT: 8081
          HOST: 127.0.0.1          
```

- [ ] **Step 3: Edit the "Run siege (async-titiler-stacapi)" step**

Replace:

```yaml
      - name: Run siege (async-titiler-stacapi)
        run: |
          siege --file ./mosaic/urls.txt -b -c 10 -r 200 --json-output 2>&1 | jq -c > results.json
          echo "Benchmark Results"
          cat results.json | jq
          echo "Parse Results"
          cat results.json | jq '{"name": "async-titiler-stacapi elapsed_time", "unit": "s", "value": .elapsed_time}, {"name": "async-titiler-stacapi concurrency", "unit": "Count", "value": .concurrency}, {"name": "async-titiler-stacapi response_time", "unit": "s", "value": .response_time}, {"name": "async-titiler-stacapi transaction_rate", "unit": "trans/sec", "value": .transaction_rate}' >> output.json
        env:
          PORT: 8082
          HOST: 127.0.0.1          
```

with:

```yaml
      - name: Run siege (async-titiler-stacapi)
        run: |
          siege --file ./mosaic/urls.txt -b -c 10 -r 200 --json-output 2>&1 | jq -c > results.json
          echo "Benchmark Results"
          cat results.json | jq
          echo "Parse Results"
          cat results.json | jq '{"service": "async-titiler-stacapi", "name": "elapsed_time", "unit": "s", "value": .elapsed_time}, {"service": "async-titiler-stacapi", "name": "concurrency", "unit": "Count", "value": .concurrency}, {"service": "async-titiler-stacapi", "name": "response_time", "unit": "s", "value": .response_time}, {"service": "async-titiler-stacapi", "name": "transaction_rate", "unit": "trans/sec", "value": .transaction_rate}' >> output.json
        env:
          PORT: 8082
          HOST: 127.0.0.1          
```

- [ ] **Step 4: Validate YAML syntax**

Run: `uv run --with pyyaml python -c "import yaml; yaml.safe_load(open('.github/workflows/benchmark-mosaic.yml')); print('valid')"`
Expected: `valid`

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/benchmark-mosaic.yml
git commit -m "fix: split service name into its own field in mosaic siege output"
```

---

### Task 6: Publish cog results to gh-benchmarks — DONE (revised during execution)

**Files:**
- Modify: `.github/workflows/benchmark-cog.yml`

**Revision note:** the original draft below used
`stefanzweifel/git-auto-commit-action` for the push step. Code review during
execution found that action does a single fetch+push with **no real
retry/rebase-on-conflict** — it doesn't deliver the concurrency safety this
plan originally claimed. It was replaced with a hand-rolled fetch+rebase+retry
`run:` step (see "Push results to gh-benchmarks" below), and a workflow-level
`concurrency:` group was added to close the residual same-workflow race
entirely. Both changes are already implemented and reviewed on
`feat/gh-benchmarks-report`; Task 7 (mosaic) should use this same corrected
pattern from the start rather than repeating the original draft.

Adds three steps after "Merge Outputs" and before "Stop services", gated to
`push` events only (PR runs, including from forks, must not get write access
to shared benchmark history). Also adds a `concurrency:` group at the
workflow level so two runs of this same workflow can't race on the same
`gh-benchmarks/cog/*.json` files.

- [x] **Step 1: Add a concurrency group**

After the `on:` block, before `env:`:

```yaml
concurrency:
  group: benchmark-cog-${{ github.ref }}
```

- [x] **Step 2: Edit the workflow — add the publish steps**

Replace:

```yaml
      - name: Merge Outputs
        run: |
          cat output.json | jq '[inputs]' > siege_results.json

      - name: Stop services
        if: always()
        run: docker compose stop
```

with:

```yaml
      - name: Merge Outputs
        run: |
          cat output.json | jq '[inputs]' > siege_results.json

      - name: Checkout gh-benchmarks
        if: github.event_name == 'push'
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          ref: gh-benchmarks
          path: gh-benchmarks

      - name: Copy results into gh-benchmarks/cog
        if: github.event_name == 'push'
        run: |
          mkdir -p gh-benchmarks/cog
          cp benchmark.json gh-benchmarks/cog/benchmark.json
          cp siege_results.json gh-benchmarks/cog/siege_results.json

      - name: Push results to gh-benchmarks
        if: github.event_name == 'push'
        working-directory: gh-benchmarks
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add cog/benchmark.json cog/siege_results.json
          if git diff --cached --quiet; then
            echo "No changes to commit"
            exit 0
          fi
          git commit -m "chore: update cog benchmark results"
          for attempt in 1 2 3 4 5; do
            if git push origin HEAD:gh-benchmarks; then
              echo "Pushed on attempt $attempt"
              exit 0
            fi
            echo "Push rejected (attempt $attempt), fetching and rebasing before retry..."
            sleep $((RANDOM % 5 + 1))
            git fetch origin gh-benchmarks
            git rebase origin/gh-benchmarks
          done
          echo "Failed to push to gh-benchmarks after 5 attempts"
          exit 1

      - name: Stop services
        if: always()
        run: docker compose stop
```

No third-party action is used for the push — this removes the need to track
a SHA pin for `git-auto-commit-action` entirely.

- [x] **Step 3: Validate YAML syntax**

Run: `uv run --with pyyaml python -c "import yaml; yaml.safe_load(open('.github/workflows/benchmark-cog.yml')); print('valid')"`
Expected: `valid`

- [x] **Step 4: Commit**

Landed as three commits during execution (concurrency group split out
separately from the push-step fix for a clean history):
`f85d5ea` (initial publish steps with the since-replaced action),
`4e99fc0` (replace action with retry-loop push),
`63ac1cd` (add concurrency group).

---

### Task 7: Publish mosaic results to gh-benchmarks

**Files:**
- Modify: `.github/workflows/benchmark-mosaic.yml`

Use the corrected pattern from Task 6 directly — do not use
`git-auto-commit-action`.

- [ ] **Step 1: Add a concurrency group**

After the `on:` block, before `env:`:

```yaml
concurrency:
  group: benchmark-mosaic-${{ github.ref }}
```

- [ ] **Step 2: Edit the workflow — add the publish steps**

In `.github/workflows/benchmark-mosaic.yml`, replace:

```yaml
      - name: Merge Outputs
        run: |
          cat output.json | jq '[inputs]' > siege_results.json

      - name: Stop services
        if: always()
        run: docker compose -f docker-compose.mosaic.yml stop
```

with:

```yaml
      - name: Merge Outputs
        run: |
          cat output.json | jq '[inputs]' > siege_results.json

      - name: Checkout gh-benchmarks
        if: github.event_name == 'push'
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          ref: gh-benchmarks
          path: gh-benchmarks

      - name: Copy results into gh-benchmarks/mosaic
        if: github.event_name == 'push'
        run: |
          mkdir -p gh-benchmarks/mosaic
          cp benchmark.json gh-benchmarks/mosaic/benchmark.json
          cp siege_results.json gh-benchmarks/mosaic/siege_results.json

      - name: Push results to gh-benchmarks
        if: github.event_name == 'push'
        working-directory: gh-benchmarks
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add mosaic/benchmark.json mosaic/siege_results.json
          if git diff --cached --quiet; then
            echo "No changes to commit"
            exit 0
          fi
          git commit -m "chore: update mosaic benchmark results"
          for attempt in 1 2 3 4 5; do
            if git push origin HEAD:gh-benchmarks; then
              echo "Pushed on attempt $attempt"
              exit 0
            fi
            echo "Push rejected (attempt $attempt), fetching and rebasing before retry..."
            sleep $((RANDOM % 5 + 1))
            git fetch origin gh-benchmarks
            git rebase origin/gh-benchmarks
          done
          echo "Failed to push to gh-benchmarks after 5 attempts"
          exit 1

      - name: Stop services
        if: always()
        run: docker compose -f docker-compose.mosaic.yml stop
```

- [ ] **Step 3: Validate YAML syntax**

Run: `uv run --with pyyaml python -c "import yaml; yaml.safe_load(open('.github/workflows/benchmark-mosaic.yml')); print('valid')"`
Expected: `valid`

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/benchmark-mosaic.yml
git commit -m "feat: publish mosaic benchmark results to gh-benchmarks"
```

---

### Task 8: Build the report page and seed the gh-benchmarks branch

**Files:**
- Create (on `gh-benchmarks`, via worktree at `.worktrees/gh-benchmarks`): `index.html`
- Modify: `.gitignore` (ignore the worktree directory on `main`)

`gh-benchmarks` is an orphan branch unrelated to `main`'s history, so
`index.html` is authored and committed there directly via a git worktree —
not through a PR against `main`.

- [ ] **Step 1: Confirm `.worktrees/` is already ignored**

Already added to `.gitignore` (commit `a170c48`, done as part of setting up
the isolated workspace for this plan's own execution). Confirm:

Run: `git check-ignore -q .worktrees && echo ignored`
Expected: `ignored`

- [ ] **Step 2: Add the worktree for gh-benchmarks**

```bash
git worktree add --track -b gh-benchmarks .worktrees/gh-benchmarks origin/gh-benchmarks
```

Expected: a new directory `.worktrees/gh-benchmarks` checked out at the
(empty) `gh-benchmarks` branch, tracking `origin/gh-benchmarks`.

- [ ] **Step 3: Write `index.html`**

Create `.worktrees/gh-benchmarks/index.html`:

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>titiler-benchmark report</title>
<style>
:root {
  color-scheme: light;
  --page: #f9f9f7;
  --surface-1: #fcfcfb;
  --text-primary: #0b0b0b;
  --text-secondary: #52514e;
  --muted: #898781;
  --grid: #e1e0d9;
  --border: rgba(11,11,11,0.10);
  --s1: #2a78d6;
  --s2: #eb6834;
  --s3: #1baf7a;
  --s4: #eda100;
  --s5: #e87ba4;
}
@media (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --page: #0d0d0d;
    --surface-1: #1a1a19;
    --text-primary: #ffffff;
    --text-secondary: #c3c2b7;
    --muted: #898781;
    --grid: #2c2c2a;
    --border: rgba(255,255,255,0.10);
    --s1: #3987e5;
    --s2: #d95926;
    --s3: #199e70;
    --s4: #c98500;
    --s5: #d55181;
  }
}
* { box-sizing: border-box; }
body {
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  color: var(--text-primary);
  background: var(--page);
  margin: 0;
  padding: 24px;
}
.wrap { max-width: 900px; margin: 0 auto; }
.report-head { margin-bottom: 20px; }
.report-head h1 { font-size: 20px; margin: 0 0 4px; }
.report-head .meta { color: var(--text-secondary); font-size: 13px; }
.section { background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px; padding: 20px; margin-bottom: 20px; }
.section h2 { font-size: 15px; margin: 0 0 14px; text-transform: uppercase; letter-spacing: .04em; color: var(--text-secondary); }
.placeholder { color: var(--muted); font-size: 13px; }
.legend { display: flex; gap: 16px; margin-bottom: 12px; font-size: 12px; color: var(--text-secondary); flex-wrap: wrap; }
.legend span { display: inline-flex; align-items: center; gap: 6px; }
.swatch { width: 10px; height: 10px; border-radius: 2px; display: inline-block; }
.s1 { background: var(--s1); }
.s2 { background: var(--s2); }
.s3 { background: var(--s3); }
.s4 { background: var(--s4); }
.s5 { background: var(--s5); }
.chart { display: flex; align-items: flex-end; gap: 22px; height: 160px; padding: 24px 4px 0; border-bottom: 1px solid var(--grid); overflow-x: auto; }
.group { display: flex; flex-direction: column; align-items: center; gap: 8px; min-width: 40px; height: 100%; justify-content: flex-end; }
.bars { display: flex; align-items: flex-end; gap: 2px; height: 100%; }
.bar { width: 20px; border-radius: 4px 4px 0 0; position: relative; }
.bar .val { position: absolute; top: -16px; left: 50%; transform: translateX(-50%); font-size: 10px; color: var(--text-secondary); white-space: nowrap; }
.group .label { font-size: 11px; color: var(--muted); white-space: nowrap; }
table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 16px; }
th, td { text-align: right; padding: 8px 10px; }
th:first-child, td:first-child { text-align: left; color: var(--text-secondary); }
th { color: var(--muted); font-weight: 500; font-size: 11px; text-transform: uppercase; letter-spacing: .03em; border-bottom: 1px solid var(--grid); }
td { font-variant-numeric: tabular-nums; border-bottom: 1px solid var(--grid); }
tr:last-child td { border-bottom: none; }
</style>
</head>
<body>
<div class="wrap">
  <div class="report-head">
    <h1>titiler-benchmark</h1>
    <div class="meta" id="meta">Loading&hellip;</div>
  </div>

  <div class="section">
    <h2>COG &mdash; single tile latency</h2>
    <div id="cog-content"><p class="placeholder">Loading&hellip;</p></div>
  </div>

  <div class="section">
    <h2>Mosaic &mdash; single tile latency</h2>
    <div id="mosaic-content"><p class="placeholder">Loading&hellip;</p></div>
  </div>
</div>

<script>
const PALETTE_CLASSES = ['s1', 's2', 's3', 's4', 's5'];

const METRIC_LABELS = {
  elapsed_time: 'Elapsed time (s)',
  response_time: 'Response time (s)',
  transaction_rate: 'Transaction rate (trans/sec)',
  concurrency: 'Concurrency',
};

async function fetchJSON(path) {
  try {
    const res = await fetch(path, { cache: 'no-store' });
    if (!res.ok) return null;
    return await res.json();
  } catch (e) {
    return null;
  }
}

function firstSeen(items, key) {
  const seen = [];
  for (const item of items) {
    if (!seen.includes(item[key])) seen.push(item[key]);
  }
  return seen;
}

function extractZoom(group) {
  const m = group.match(/Zoom (\d+)/);
  return m ? parseInt(m[1], 10) : 0;
}

function renderBarChart(benchmarks) {
  const services = firstSeen(benchmarks, 'name');
  const groups = [...new Set(benchmarks.map((b) => b.group))].sort(
    (a, b) => extractZoom(a) - extractZoom(b)
  );
  const maxMean = Math.max(...benchmarks.map((b) => b.stats.mean), 0.0001);

  const legend = services
    .map((s, i) => `<span><span class="swatch ${PALETTE_CLASSES[i % PALETTE_CLASSES.length]}"></span>${s}</span>`)
    .join('');

  const groupsHtml = groups
    .map((g) => {
      const bars = services
        .map((s, i) => {
          const b = benchmarks.find((x) => x.group === g && x.name === s);
          if (!b) return '';
          const pct = Math.round((b.stats.mean / maxMean) * 100);
          return `<div class="bar ${PALETTE_CLASSES[i % PALETTE_CLASSES.length]}" style="height:${pct}%"><span class="val">${b.stats.mean.toFixed(2)}s</span></div>`;
        })
        .join('');
      return `<div class="group"><div class="bars">${bars}</div><div class="label">${g}</div></div>`;
    })
    .join('');

  return `<div class="legend">${legend}</div><div class="chart">${groupsHtml}</div>`;
}

function renderSiegeTable(siege) {
  const services = firstSeen(siege, 'service');
  const metrics = firstSeen(siege, 'name');

  const header = `<tr><th>siege metric</th>${services.map((s) => `<th>${s}</th>`).join('')}</tr>`;
  const rows = metrics
    .map((m) => {
      const cells = services
        .map((s) => {
          const row = siege.find((r) => r.service === s && r.name === m);
          return `<td>${row ? row.value : '&ndash;'}</td>`;
        })
        .join('');
      return `<tr><td>${METRIC_LABELS[m] || m}</td>${cells}</tr>`;
    })
    .join('');

  return `<table><thead>${header}</thead><tbody>${rows}</tbody></table>`;
}

function renderSection(containerId, benchmarks, siege) {
  const el = document.getElementById(containerId);
  if (!benchmarks && !siege) {
    el.innerHTML = '<p class="placeholder">No data yet.</p>';
    return;
  }
  let html = '';
  html += benchmarks ? renderBarChart(benchmarks) : '<p class="placeholder">No latency data yet.</p>';
  html += siege ? renderSiegeTable(siege) : '<p class="placeholder">No siege data yet.</p>';
  el.innerHTML = html;
}

async function main() {
  const [cogBench, cogSiege, mosaicBench, mosaicSiege] = await Promise.all([
    fetchJSON('cog/benchmark.json'),
    fetchJSON('cog/siege_results.json'),
    fetchJSON('mosaic/benchmark.json'),
    fetchJSON('mosaic/siege_results.json'),
  ]);

  const meta = document.getElementById('meta');
  const info = cogBench || mosaicBench;
  if (info) {
    const shortSha = info.commit_info.id.slice(0, 7);
    const date = new Date(info.datetime).toLocaleString();
    meta.textContent = `Commit ${shortSha} · ${date}`;
  } else {
    meta.textContent = 'No benchmark data yet.';
  }

  renderSection('cog-content', cogBench ? cogBench.benchmarks : null, cogSiege);
  renderSection('mosaic-content', mosaicBench ? mosaicBench.benchmarks : null, mosaicSiege);
}

main();
</script>
</body>
</html>
```

- [ ] **Step 4: Commit and push to gh-benchmarks**

```bash
cd .worktrees/gh-benchmarks
git add index.html
git commit -m "feat: add static benchmark report page"
git push -u origin gh-benchmarks
cd -
```

---

### Task 9: End-to-end local verification with fixture data

**Files:** none (uses temporary fixtures in the worktree; not committed)

- [ ] **Step 1: Drop in fixture data matching the new schemas**

```bash
mkdir -p .worktrees/gh-benchmarks/cog .worktrees/gh-benchmarks/mosaic
cat > .worktrees/gh-benchmarks/cog/benchmark.json <<'EOF'
{
  "commit_info": {"id": "542c2a8d1314b7395d1b497689fe9cf13b42fea2", "branch": "main"},
  "datetime": "2026-07-30T17:56:01.129047+00:00",
  "benchmarks": [
    {"name": "titiler", "group": "Zoom 3", "stats": {"mean": 0.41}},
    {"name": "async", "group": "Zoom 3", "stats": {"mean": 0.35}},
    {"name": "titiler", "group": "Zoom 12", "stats": {"mean": 0.61}},
    {"name": "async", "group": "Zoom 12", "stats": {"mean": 0.50}}
  ]
}
EOF
cat > .worktrees/gh-benchmarks/cog/siege_results.json <<'EOF'
[
  {"service": "titiler", "name": "elapsed_time", "unit": "s", "value": 87.10},
  {"service": "titiler", "name": "response_time", "unit": "s", "value": 0.309},
  {"service": "async-titiler", "name": "elapsed_time", "unit": "s", "value": 80.95},
  {"service": "async-titiler", "name": "response_time", "unit": "s", "value": 0.360}
]
EOF
```

Deliberately leave `mosaic/benchmark.json` and `mosaic/siege_results.json`
absent, to exercise the "no data yet" fallback.

- [ ] **Step 2: Serve the worktree locally**

```bash
cd .worktrees/gh-benchmarks && python3 -m http.server 8123
```

- [ ] **Step 3: Manually verify in a browser**

Open `http://localhost:8123/` and confirm:
- Header shows `Commit 542c2a8 · <formatted date>`
- COG section shows a bar chart with two bars per zoom group (titiler,
  async), zoom 3 and zoom 12, and a table with elapsed_time/response_time
  rows for both `titiler` and `async-titiler` columns
- Mosaic section shows "No data yet."
- Toggling OS/browser dark mode swaps the page colors (background, text,
  bars) without any layout breakage

- [ ] **Step 4: Stop the server and remove the fixture files (not committed)**

```bash
# Ctrl-C the http.server process, then:
rm -rf .worktrees/gh-benchmarks/cog .worktrees/gh-benchmarks/mosaic
cd - 2>/dev/null || true
```

Confirm nothing fixture-related was committed:

Run: `git -C .worktrees/gh-benchmarks status --porcelain`
Expected: empty output.

---

### Task 10: Land the changes

**Files:** none (git/GitHub operations only)

- [ ] **Step 1: Push the main-branch changes and open a PR**

The workflow/`.gitignore` changes from Tasks 1&ndash;7 belong on `main` through
normal review; confirm with the user before pushing/opening the PR.

```bash
git push -u origin HEAD
gh pr create --title "Publish benchmark results to gh-benchmarks" --body "$(cat <<'EOF'
## Summary
- Preserve commit_info/datetime and split service into its own field in both workflows' JSON output
- Push cog/mosaic benchmark results to the gh-benchmarks branch on every push to main
- Add a static index.html report to gh-benchmarks that renders the latest results client-side

## Test plan
- [x] jq transforms verified locally against fixtures (Tasks 2-5)
- [x] YAML syntax validated after each edit
- [x] Report page verified against fixture data in a browser, including the "no data yet" fallback (Task 9)
- [ ] First real workflow run after merge: confirm gh-benchmarks receives cog/*.json and mosaic/*.json
EOF
)"
```

- [ ] **Step 2: Enable GitHub Pages (manual, requires explicit confirmation)**

This is a repo-settings change — confirm with the user before doing it. Either
via the UI (Settings → Pages → Source: Deploy from a branch → `gh-benchmarks`
/ `/ (root)`), or via `gh api`:

```bash
gh api -X POST repos/{owner}/{repo}/pages -f "source[branch]=gh-benchmarks" -f "source[path]=/"
```

- [ ] **Step 3: After the PR merges, verify the first real run**

Once merged and the next push to `main` runs the workflows:

```bash
git -C .worktrees/gh-benchmarks fetch origin gh-benchmarks
git -C .worktrees/gh-benchmarks log origin/gh-benchmarks --oneline -5
git -C .worktrees/gh-benchmarks show origin/gh-benchmarks:cog/benchmark.json | jq 'keys'
```

Expected: recent commits authored by `github-actions[bot]` (from the
retry-loop push script), and `benchmark.json` with top-level keys
`commit_info`, `datetime`, `benchmarks`.

Then open the Pages URL and confirm the report renders real data for both
sections.

---

## Self-Review Notes

- **Spec coverage:** branch reuse (Task 8), latest-only overwrite semantics
  (Tasks 6-7 `cp`, no history path), unified stacked-section page (Task 8
  `index.html`), static client-fetch report (Task 8), siege `service`/`name`
  split (Tasks 3, 5), `benchmark.json` commit/datetime wrapping (Tasks 2, 4),
  push-only gating (Tasks 6-7 `if:`), Pages setup (Task 10) — all covered.
- **Out of scope confirmed:** no trend/history charts, no PR-triggered
  publishing, no regression-alert comments — none of the tasks above add
  these.
