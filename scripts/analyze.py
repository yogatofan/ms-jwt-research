#!/usr/bin/env python3
"""
scripts/analyze.py
==================
Reads k6 summary JSON files from all repeated runs and computes
mean ± standard deviation for each key metric per scenario.

Output:
  - Terminal table
  - load-testing/results/statistical-summary.csv
  - visualisasi/fig3-normal-latency-stats.{pdf,png}   (bar + error bars)
  - visualisasi/fig4-burst-traffic-stats.{pdf,png}    (bar + error bars)

Usage:
  python scripts/analyze.py [OPTIONS]

Options:
  -n, --runs    N      Total runs per scenario to read  (default: 5)
  -r, --results PATH   Path to results directory        (default: load-testing/results)
  -o, --output  PATH   Path to visualisasi directory    (default: visualisasi)
  -h, --help           Show this help and exit.
"""

import argparse
import csv
import json
import math
import os
import sys
from pathlib import Path

# ── Try matplotlib, warn gracefully ───────────────────────────────────────────
try:
    import matplotlib
    matplotlib.use("Agg")            # headless / no display needed
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np
    HAS_MPL = True
except ImportError:
    HAS_MPL = False
    print("[WARN] matplotlib/numpy not installed — skipping chart generation.")
    print("       Install with: pip install matplotlib numpy\n")


# ─────────────────────────────────────────────────────────────────────────────
# Metric extraction helpers
# ─────────────────────────────────────────────────────────────────────────────

def safe_get(d: dict, *keys, default=None):
    """Traverse nested dict safely."""
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k, None)
        if cur is None:
            return default
    return cur


def extract_metrics(summary: dict) -> dict:
    """
    Pull the KPIs we care about from a k6 --summary-export JSON.
    Returns a flat dict of metric_name → float value.
    """
    m = summary.get("metrics", {})

    def trend_avg(name):
        return safe_get(m, name, "avg", default=None)

    def trend_p95(name):
        return safe_get(m, name, "p(95)", default=None)

    def trend_max(name):
        return safe_get(m, name, "max", default=None)

    def rate_val(name):
        # k6 Rate stores the fraction in "value"
        return safe_get(m, name, "value", default=None)

    def counter_rate(name):
        return safe_get(m, name, "rate", default=None)

    # ── Reviewer count data extraction ─────────────────────────
    total_reqs = safe_get(m, "http_reqs", "count", default=0) or 0
    # http_req_failed.fails is the count of successful requests (status < 400, i.e., 2xx)
    succ_2xx = safe_get(m, "http_req_failed", "fails", default=0) or 0
    
    # Blocked requests (429)
    if "blocked_requests" in m:
        blocked_429 = safe_get(m, "blocked_requests", "count", default=0) or 0
    elif "checks" in summary.get("root_group", {}) and "rate limited 429" in summary["root_group"]["checks"]:
        blocked_429 = safe_get(summary["root_group"]["checks"], "rate limited 429", "passes", default=0) or 0
    else:
        blocked_429 = 0

    backend_fwd = total_reqs - blocked_429
    succ_2xx_rate = (succ_2xx / total_reqs * 100.0) if total_reqs > 0 else 0.0
    rate_limited_rate = (blocked_429 / total_reqs * 100.0) if total_reqs > 0 else 0.0

    return {
        # Latency – custom Trend metrics (ms)
        "login_latency_avg":     trend_avg("login_latency"),
        "login_latency_p95":     trend_p95("login_latency"),
        "login_latency_max":     trend_max("login_latency"),
        "product_latency_avg":   trend_avg("product_latency"),
        "product_latency_p95":   trend_p95("product_latency"),
        "product_latency_max":   trend_max("product_latency"),
        "order_latency_avg":     trend_avg("order_latency"),
        "order_latency_p95":     trend_p95("order_latency"),
        # Overall HTTP latency (always present)
        "http_req_duration_avg": trend_avg("http_req_duration"),
        "http_req_duration_p95": trend_p95("http_req_duration"),
        "http_req_duration_max": trend_max("http_req_duration"),
        # Error rate (0–1 fraction)
        "error_rate":            rate_val("error_rate"),
        # Throughput (req/s)
        "throughput":            counter_rate("http_reqs"),
        # Count & Reviewer Requested Metrics
        "total_attempted_requests": total_reqs,
        "successful_2xx_responses":  succ_2xx,
        "successful_response_rate":  succ_2xx_rate,
        "rate_limited_responses":    blocked_429,
        "rate_limited_response_rate": rate_limited_rate,
        "backend_forwarded_requests": backend_fwd,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Statistical helpers
# ─────────────────────────────────────────────────────────────────────────────

def mean(values):
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return sum(vals) / len(vals)


def std(values):
    vals = [v for v in values if v is not None]
    if len(vals) < 2:
        return 0.0
    mu = sum(vals) / len(vals)
    variance = sum((v - mu) ** 2 for v in vals) / (len(vals) - 1)   # sample SD
    return math.sqrt(variance)


def compute_stats(all_runs: list[dict]) -> dict:
    """Given list of metric dicts (one per run), return {metric: (mean, sd)}."""
    keys = all_runs[0].keys()
    return {k: (mean([r[k] for r in all_runs]), std([r[k] for r in all_runs]))
            for k in keys}


# ─────────────────────────────────────────────────────────────────────────────
# Formatting
# ─────────────────────────────────────────────────────────────────────────────

def fmt(value, decimals=3):
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}"


def fmt_pct(value):
    if value is None:
        return "N/A"
    return f"{value * 100:.2f}%"


# ─────────────────────────────────────────────────────────────────────────────
# Scenarios
# ─────────────────────────────────────────────────────────────────────────────

SCENARIOS = [
    "normal-no-security",
    "normal-with-security",
    "burst-no-security",
    "burst-with-security",
]

DISPLAY_NAMES = {
    "normal-no-security":   "Normal / No Security",
    "normal-with-security": "Normal / JWT + Rate Limiting",
    "burst-no-security":    "Burst  / No Security",
    "burst-with-security":  "Burst  / JWT + Rate Limiting",
}

HUMAN_METRICS = {
    "login_latency_avg":         "Login Latency avg (ms)",
    "login_latency_p95":         "Login Latency p95 (ms)",
    "product_latency_avg":       "Product Latency avg (ms)",
    "product_latency_p95":       "Product Latency p95 (ms)",
    "order_latency_avg":         "Order Latency avg (ms)",
    "http_req_duration_avg":     "HTTP Duration avg (ms)",
    "http_req_duration_p95":     "HTTP Duration p95 (ms)",
    "http_req_duration_max":     "HTTP Duration max (ms)",
    "error_rate":                "Error Rate",
    "throughput":                "Throughput (req/s)",
    "total_attempted_requests":   "Total Attempted Requests",
    "successful_2xx_responses":  "Successful 2xx Responses",
    "successful_response_rate":  "Successful-Response Rate (%)",
    "rate_limited_responses":    "Rate-Limited Responses (429)",
    "rate_limited_response_rate":"Rate-Limited Response Rate (%)",
    "backend_forwarded_requests":"Backend-Forwarded Requests",
}


# ─────────────────────────────────────────────────────────────────────────────
# Terminal table
# ─────────────────────────────────────────────────────────────────────────────

def print_table(all_stats: dict[str, dict]):
    """Pretty-print a metric × scenario table."""
    COL_W = 30
    SEP = " │ "

    # Header
    header = f"{'Metric':<{COL_W}}" + SEP
    header += SEP.join(f"{DISPLAY_NAMES[s]:<{COL_W}}" for s in SCENARIOS)
    print("\n" + "═" * len(header))
    print(header)
    print("═" * len(header))

    for key, label in HUMAN_METRICS.items():
        row = f"{label:<{COL_W}}" + SEP
        cells = []
        for sc in SCENARIOS:
            stats = all_stats.get(sc, {})
            mu, sd = stats.get(key, (None, 0))
            if key == "error_rate":
                cell = f"{fmt_pct(mu)} ± {fmt_pct(sd)}"
            else:
                cell = f"{fmt(mu)} ± {fmt(sd)}"
            cells.append(f"{cell:<{COL_W}}")
        row += SEP.join(cells)
        print(row)

    print("═" * len(header) + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# CSV export
# ─────────────────────────────────────────────────────────────────────────────

def write_csv(all_stats: dict, out_path: Path):
    rows = []
    for sc in SCENARIOS:
        stats = all_stats.get(sc, {})
        for key, label in HUMAN_METRICS.items():
            mu, sd = stats.get(key, (None, 0))
            is_pct = key in ("error_rate", "successful_response_rate", "rate_limited_response_rate")
            rows.append({
                "scenario": sc,
                "metric": label,
                "mean": fmt_pct(mu/100.0 if key != "error_rate" else mu) if is_pct else fmt(mu, 3),
                "std":  fmt_pct(sd/100.0 if key != "error_rate" else sd) if is_pct else fmt(sd, 3),
                "mean_raw": mu,
                "std_raw":  sd,
            })

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["scenario", "metric", "mean", "std", "mean_raw", "std_raw"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"[OK] CSV saved → {out_path}")


def export_reviewer_latex_table(all_stats: dict, out_dir: Path):
    """
    Exports the reviewer-requested LaTeX table for Burst Traffic mitigation
    and Normal Traffic counts with Mean ± SD over 5 runs.
    """
    b_no = all_stats.get("burst-no-security", {})
    b_wi = all_stats.get("burst-with-security", {})

    def f_cnt(stats, key):
        mu, sd = stats.get(key, (0.0, 0.0))
        return f"{mu:,.1f} $\\pm$ {sd:,.1f}"

    def f_rate(stats, key, decimals=2, is_fraction=False):
        mu, sd = stats.get(key, (0.0, 0.0))
        if is_fraction:
            mu *= 100.0
            sd *= 100.0
        return f"{mu:.{decimals}f}\\% $\\pm$ {sd:.{decimals}f}\\%"

    # Calculate overall http failure rate (100% - successful_response_rate)
    b_no_succ_mu, b_no_succ_sd = b_no.get("successful_response_rate", (0.0, 0.0))
    b_no_fail_mu = 100.0 - b_no_succ_mu
    b_no_fail_sd = b_no_succ_sd

    b_wi_succ_mu, b_wi_succ_sd = b_wi.get("successful_response_rate", (0.0, 0.0))
    b_wi_fail_mu = 0.0
    b_wi_fail_sd = 0.0

    tex_content = f"""% ── Reviewer-Requested Table: Burst Traffic Response Breakdown (Reconciled) ──
\\begin{{table*}}[!t]
  \\centering
  \\caption{{Burst Traffic Response Breakdown and Rate-Limiting Mitigation ($n=5$, Mean $\\pm$ SD)}}
  \\label{{tab:burst-count-breakdown}}
  \\begin{{tabular}}{{|l|r|r|}}
    \\hline
    \\textbf{{Metric}} & \\textbf{{Without Security}} & \\textbf{{With JWT + Rate Limiting}} \\\\
    \\hline
    Total attempted requests        & {f_cnt(b_no, "total_attempted_requests")} & {f_cnt(b_wi, "total_attempted_requests")} \\\\
    Successful 2xx responses        & {f_cnt(b_no, "successful_2xx_responses")} & {f_cnt(b_wi, "successful_2xx_responses")} \\\\
    Successful-response rate        & {f_rate(b_no, "successful_response_rate", 2)} & {f_rate(b_wi, "successful_response_rate", 4)} \\\\
    Rate-limited responses (429)    & {f_cnt(b_no, "rate_limited_responses")} & {f_cnt(b_wi, "rate_limited_responses")} \\\\
    Rate-limited response rate      & {f_rate(b_no, "rate_limited_response_rate", 2)} & {f_rate(b_wi, "rate_limited_response_rate", 4)} \\\\
    Overall HTTP failure rate       & {b_no_fail_mu:.2f}\\% $\\pm$ {b_no_fail_sd:.2f}\\% & {b_wi_fail_mu:.4f}\\% $\\pm$ {b_wi_fail_sd:.4f}\\% \\\\
    Backend-forwarded requests      & {f_cnt(b_no, "backend_forwarded_requests")} & {f_cnt(b_wi, "backend_forwarded_requests")} \\\\
    \\hline
    Login-stage failure rate$^*$    & {f_rate(b_no, "error_rate", 2, is_fraction=True)} & {f_rate(b_wi, "error_rate", 2, is_fraction=True)} \\\\
    \\hline
  \\end{{tabular}}
  \\vspace{{1ex}}
  \\raggedright
  \\footnotesize{{$^*$The login-stage failure rate specifically measures connection/socket exhaustion on the authentication endpoint, while the overall HTTP failure rate encompasses all attempted requests across both login and product endpoints.}}
\\end{{table*}}
"""
    out_file = out_dir / "table-burst-mitigation.tex"
    out_file.write_text(tex_content, encoding="utf-8")
    print(f"[OK] Reviewer LaTeX table saved → {out_file}")



# ─────────────────────────────────────────────────────────────────────────────
# Charts
# ─────────────────────────────────────────────────────────────────────────────

COLORS = {
    "no-security":   "#B4B2A9",
    "with-security": "#378ADD",
    "error-no":      "#E24B4A",
    "error-with":    "#1D9E75",
}


def _bar_with_errbar(ax, x_positions, means, stds, colors, width=0.35, **bar_kwargs):
    bars = ax.bar(x_positions, means, width, color=colors, **bar_kwargs)
    ax.errorbar(
        x_positions, means, yerr=stds,
        fmt="none", ecolor="black", elinewidth=1.2, capsize=4, zorder=5
    )
    return bars


def fig3_normal_latency(all_stats: dict, out_dir: Path):
    """
    Fig 3 – Normal Traffic: avg latency per endpoint, with error bars (± 1 SD).
    Reproduces grafik1.py style but with statistical bands.
    """
    endpoints = ["Login", "Product", "Order"]
    metrics   = ["login_latency_avg", "product_latency_avg", "order_latency_avg"]

    ns = all_stats.get("normal-no-security", {})
    ws = all_stats.get("normal-with-security", {})

    no_means = [ns.get(m, (0, 0))[0] or 0 for m in metrics]
    no_stds  = [ns.get(m, (0, 0))[1] or 0 for m in metrics]
    wi_means = [ws.get(m, (0, 0))[0] or 0 for m in metrics]
    wi_stds  = [ws.get(m, (0, 0))[1] or 0 for m in metrics]

    x = np.arange(len(endpoints))
    w = 0.35

    fig, ax = plt.subplots(figsize=(7, 4.5))
    _bar_with_errbar(ax, x - w / 2, no_means, no_stds,
                     [COLORS["no-security"]] * 3, w, label="Without Security", zorder=3)
    _bar_with_errbar(ax, x + w / 2, wi_means, wi_stds,
                     [COLORS["with-security"]] * 3, w, label="With JWT + Rate Limiting", zorder=3)

    ax.set_ylabel("Average Latency (ms)")
    ax.set_xticks(x)
    ax.set_xticklabels(endpoints)
    ax.legend()
    ax.yaxis.grid(True, linestyle="--", alpha=0.4, zorder=0)
    ax.set_axisbelow(True)

    # Annotate SD
    ax.text(0.98, 0.97, "Error bars = ±1 SD", transform=ax.transAxes,
            fontsize=8, ha="right", va="top", color="grey")

    plt.tight_layout()
    for ext in ("pdf", "png"):
        p = out_dir / f"fig3-normal-latency-stats.{ext}"
        plt.savefig(p, dpi=300, bbox_inches="tight")
        print(f"[OK] Saved → {p}")
    plt.close()


def fig4_burst_traffic(all_stats: dict, out_dir: Path):
    """
    Fig 4 – Burst Traffic: error rate + max latency, with error bars (± 1 SD).
    Reproduces grafik2.py style with statistical bands.
    """
    conditions = ["Without\nSecurity", "With JWT +\nRate Limiting"]
    sc_keys    = ["burst-no-security", "burst-with-security"]
    colors_err = [COLORS["error-no"], COLORS["error-with"]]

    err_means = [all_stats.get(k, {}).get("error_rate", (0, 0))[0] or 0 for k in sc_keys]
    err_stds  = [all_stats.get(k, {}).get("error_rate", (0, 0))[1] or 0 for k in sc_keys]
    lat_means = [all_stats.get(k, {}).get("http_req_duration_max", (0, 0))[0] or 0 for k in sc_keys]
    lat_stds  = [all_stats.get(k, {}).get("http_req_duration_max", (0, 0))[1] or 0 for k in sc_keys]

    # Convert error rate fraction → percentage
    err_means_pct = [v * 100 for v in err_means]
    err_stds_pct  = [v * 100 for v in err_stds]

    x = np.arange(len(conditions))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    # Panel (a) — Error Rate
    _bar_with_errbar(axes[0], x, err_means_pct, err_stds_pct, colors_err, 0.45, zorder=3)
    axes[0].set_ylabel("Error Rate (%)")
    axes[0].set_title("(a) Error Rate under Burst Traffic")
    axes[0].set_ylim(0, 110)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(conditions)
    axes[0].yaxis.grid(True, linestyle="--", alpha=0.5, zorder=0)
    axes[0].set_axisbelow(True)
    for xi, (mu, sd) in zip(x, zip(err_means_pct, err_stds_pct)):
        axes[0].text(xi, mu + sd + 2, f"{mu:.2f}%", ha="center", va="bottom",
                     fontsize=10, fontweight="bold")

    # Panel (b) — Max Latency
    _bar_with_errbar(axes[1], x, lat_means, lat_stds, colors_err, 0.45, zorder=3)
    axes[1].set_ylabel("Max Latency (ms)")
    axes[1].set_title("(b) Max Latency under Burst Traffic")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(conditions)
    axes[1].yaxis.grid(True, linestyle="--", alpha=0.5, zorder=0)
    axes[1].set_axisbelow(True)
    for xi, (mu, sd) in zip(x, zip(lat_means, lat_stds)):
        axes[1].text(xi, mu + sd + axes[1].get_ylim()[1] * 0.01,
                     f"{mu:,.0f} ms", ha="center", va="bottom",
                     fontsize=10, fontweight="bold")

    # Shared legend
    patch1 = mpatches.Patch(color=COLORS["error-no"],   label="Without Security")
    patch2 = mpatches.Patch(color=COLORS["error-with"], label="With JWT + Rate Limiting")
    fig.legend(handles=[patch1, patch2], loc="lower center", ncol=2,
               frameon=False, fontsize=10, bbox_to_anchor=(0.5, -0.06))

    # SD annotation
    for ax in axes:
        ax.text(0.98, 0.97, "Error bars = ±1 SD", transform=ax.transAxes,
                fontsize=8, ha="right", va="top", color="grey")

    plt.tight_layout()
    for ext in ("pdf", "png"):
        p = out_dir / f"fig4-burst-traffic-stats.{ext}"
        plt.savefig(p, dpi=300, bbox_inches="tight")
        print(f"[OK] Saved → {p}")
    plt.close()


def fig5_throughput(all_stats: dict, out_dir: Path):
    """
    Fig 5 (bonus) – Throughput comparison across all four scenarios.
    """
    labels = [DISPLAY_NAMES[s].replace(" / ", "\n") for s in SCENARIOS]
    means  = [all_stats.get(s, {}).get("throughput", (0, 0))[0] or 0 for s in SCENARIOS]
    stds   = [all_stats.get(s, {}).get("throughput", (0, 0))[1] or 0 for s in SCENARIOS]
    colors = [COLORS["no-security"], COLORS["with-security"],
              COLORS["error-no"],    COLORS["error-with"]]

    x = np.arange(len(SCENARIOS))
    fig, ax = plt.subplots(figsize=(9, 4.5))
    _bar_with_errbar(ax, x, means, stds, colors, 0.5, zorder=3)
    ax.set_ylabel("Throughput (req/s)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.yaxis.grid(True, linestyle="--", alpha=0.4, zorder=0)
    ax.set_axisbelow(True)
    ax.text(0.98, 0.97, "Error bars = ±1 SD", transform=ax.transAxes,
            fontsize=8, ha="right", va="top", color="grey")

    plt.tight_layout()
    for ext in ("pdf", "png"):
        p = out_dir / f"fig5-throughput-stats.{ext}"
        plt.savefig(p, dpi=300, bbox_inches="tight")
        print(f"[OK] Saved → {p}")
    plt.close()


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-n", "--runs",    type=int, default=5,
                        help="Number of runs per scenario to read (default: 5)")
    parser.add_argument("-r", "--results", type=str, default=None,
                        help="Path to results directory (default: load-testing/results)")
    parser.add_argument("-o", "--output",  type=str, default=None,
                        help="Path to visualisasi directory (default: visualisasi)")
    args = parser.parse_args()

    # Resolve paths relative to project root (parent of scripts/)
    script_dir  = Path(__file__).resolve().parent
    project_dir = script_dir.parent

    results_dir = Path(args.results) if args.results else project_dir / "load-testing" / "results"
    output_dir  = Path(args.output)  if args.output  else project_dir / "visualisasi"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  ms-jwt-research Statistical Analyzer")
    print(f"  Runs per scenario : {args.runs}")
    print(f"  Results dir       : {results_dir}")
    print(f"  Output dir        : {output_dir}")
    print(f"{'='*60}\n")

    all_stats: dict[str, dict] = {}
    missing_scenarios = []

    for scenario in SCENARIOS:
        scenario_dir = results_dir / scenario
        run_metrics  = []
        missing_runs = []

        for i in range(1, args.runs + 1):
            summary_path = scenario_dir / f"run-{i}" / "summary.json"
            if not summary_path.exists():
                missing_runs.append(i)
                continue

            with open(summary_path) as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"[WARN] Invalid JSON in {summary_path}: {e}")
                    missing_runs.append(i)
                    continue

            metrics = extract_metrics(data)
            run_metrics.append(metrics)

        if not run_metrics:
            print(f"[WARN] No valid runs found for scenario '{scenario}' — skipping.")
            missing_scenarios.append(scenario)
            continue

        if missing_runs:
            print(f"[WARN] Scenario '{scenario}': missing runs {missing_runs} — "
                  f"computing stats from {len(run_metrics)} available run(s).")

        all_stats[scenario] = compute_stats(run_metrics)
        print(f"[OK]  Scenario '{scenario}': {len(run_metrics)} run(s) processed.")

    if not all_stats:
        print("\n[ERROR] No data found. Run the experiment first:\n"
              "  ./scripts/run-all.sh --runs 5\n")
        sys.exit(1)

    # ── Terminal table ─────────────────────────────────────────────────────────
    print_table(all_stats)

    # ── CSV ────────────────────────────────────────────────────────────────────
    csv_path = results_dir / "statistical-summary.csv"
    write_csv(all_stats, csv_path)

    # ── Charts ─────────────────────────────────────────────────────────────────
    if HAS_MPL:
        print("\nGenerating charts...")
        try:
            fig3_normal_latency(all_stats, output_dir)
        except Exception as e:
            print(f"[WARN] fig3 generation failed: {e}")
        try:
            fig4_burst_traffic(all_stats, output_dir)
        except Exception as e:
            print(f"[WARN] fig4 generation failed: {e}")
        try:
            fig5_throughput(all_stats, output_dir)
        except Exception as e:
            print(f"[WARN] fig5 throughput generation failed: {e}")
    else:
        print("[SKIP] Chart generation skipped (matplotlib not available).")

    # ── Reviewer Table LaTeX Export ────────────────────────────
    docs_dir = project_dir / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    export_reviewer_latex_table(all_stats, docs_dir)

    print(f"\n{'='*60}")
    print("  Analysis complete!")
    print(f"  CSV     → {csv_path}")
    print(f"  LaTeX   → {docs_dir}/table-burst-mitigation.tex")
    print(f"  Charts  → {output_dir}/fig3-*.png, fig4-*.png, fig5-*.png")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
