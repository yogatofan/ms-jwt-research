# Microservices JWT Research

Experimental implementation for the paper:
**"Enhancing Microservices API Security using JWT and Rate Limiting: A Performance Evaluation"**

## Project Structure
```
ms-jwt-research/
├── gateway/          # API Gateway (port 3000)
├── user-service/     # Authentication service (port 3001)
├── product-service/  # Product service (port 3002)
├── order-service/    # Order service (port 3003)
├── load-testing/     # k6 test scripts
│   └── results/      # Per-run summary JSON files
├── docs/             # LaTeX tables, environment specs, and reports
├── scripts/          # Experiment automation scripts
│   ├── run-all.sh    # Orchestrator: run all scenarios N times
│   ├── analyze.py    # Statistical analysis: mean ± SD, charts
│   └── env-report.py # Auto-detect environment specifications
└── visualisasi/      # Python visualization output figures
```

## Requirements
- Node.js v18+
- k6 v1.6+
- Python 3.x + matplotlib + numpy

```bash
# Install Python dependencies (one-time)
pip install matplotlib numpy
```

---

## Quick Start (One-time Setup)

```bash
# Install all Node.js dependencies
npm run install:all
```

---

## Running the Project (Manual)

```bash
# With security
npm run start:with-security

# Without security (baseline)
npm run start:no-security
```

---

## Repeated Experiments (for Statistical Validity)

> **Reviewer recommendation**: Run each scenario ≥ 3–5 times,
> then report **mean ± standard deviation** for all key metrics.

### Step 1 — Run all scenarios N times (automated)

```bash
# Default: 5 runs × 4 scenarios = 20 total runs
./scripts/run-all.sh

# Custom number of runs (e.g., 10)
./scripts/run-all.sh --runs 10

# Extra options
./scripts/run-all.sh --runs 5 --cooldown 60   # 60s cool-down between runs

# Run a single scenario only
./scripts/run-all.sh --runs 5 --scenario normal-no-security
# Available scenario names:
#   normal-no-security | normal-with-security
#   burst-no-security  | burst-with-security

# Show help
./scripts/run-all.sh --help
```

Results are saved to:
```
load-testing/results/
├── normal-no-security/
│   ├── run-1/summary.json
│   ├── run-2/summary.json
│   └── ...
├── normal-with-security/ ...
├── burst-no-security/ ...
└── burst-with-security/ ...
```

### Step 2 — Analyze & generate statistical figures

```bash
# Default: reads 5 runs per scenario
python scripts/analyze.py

# Match the number of runs you used
python scripts/analyze.py --runs 10

# Custom paths
python scripts/analyze.py --runs 5 \
  --results load-testing/results \
  --output visualisasi

# Show help
python scripts/analyze.py --help
```

Outputs:
| File | Description |
|---|---|
| `load-testing/results/statistical-summary.csv` | Full mean ± SD table (all metrics) |
| `visualisasi/fig3-normal-latency-stats.{pdf,png}` | Normal traffic latency with error bars |
| `visualisasi/fig4-burst-traffic-stats.{pdf,png}` | Burst traffic error rate & max latency with error bars |
| `visualisasi/fig5-throughput-stats.{pdf,png}` | Throughput comparison across all scenarios |

---

## Individual Load Testing (Manual)

```bash
cd load-testing
k6 run normal-traffic.js
k6 run burst-traffic.js
```

---

## Environment Specification Report

Generate an auto-detected spec table for insertion into a paper:

```bash
# Auto-detect all specs and generate output to docs/
python scripts/env-report.py

# Custom output directory
python scripts/env-report.py --output my-output-dir/
```

Outputs (in `docs/`):
| File | Description |
|---|---|
| `environment-spec.md` | Markdown table |
| `environment-spec.tex` | **LaTeX table (IEEE two-column ready)** |
| `environment-spec.csv` | CSV for spreadsheet import |
| `environment-spec-report.txt` | Plain text archive |

> **Tip**: Every time you change Node.js, package versions, or switch machines,
> re-run this script to keep the spec table accurate for the paper revision.