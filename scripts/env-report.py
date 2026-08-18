#!/usr/bin/env python3
"""
scripts/env-report.py
=====================
Auto-detects the actual test environment and generates a specification table
ready for insertion into an IEEE paper (Markdown + LaTeX + CSV + terminal).

Usage:
  python scripts/env-report.py [OPTIONS]

Options:
  -o, --output  DIR   Output directory for generated files  (default: docs/)
  -h, --help          Show this help and exit.

Output files (in --output dir):
  environment-spec.md         Markdown table
  environment-spec.tex        LaTeX table (IEEE two-column ready)
  environment-spec.csv        CSV (spreadsheet / BibTeX import)
  environment-spec-report.txt Full plain-text report
"""

import argparse
import csv
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

# ── ANSI colours (terminal only) ──────────────────────────────────────────────
GREEN  = "\033[0;32m"
CYAN   = "\033[0;36m"
YELLOW = "\033[1;33m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):   print(f"{GREEN}[OK]{RESET}    {msg}")
def info(msg): print(f"{CYAN}[INFO]{RESET}  {msg}")
def warn(msg): print(f"{YELLOW}[WARN]{RESET}  {msg}")


# ─────────────────────────────────────────────────────────────────────────────
# Detection helpers
# ─────────────────────────────────────────────────────────────────────────────

def run(cmd: list[str], default: str = "N/A") -> str:
    """Run a shell command and return stdout, stripped."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=10
        )
        out = result.stdout.strip()
        return out if out else default
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return default


def detect_machine() -> str:
    """Return human-readable machine model (macOS only, falls back gracefully)."""
    raw = run(["system_profiler", "SPHardwareDataType"])
    for line in raw.splitlines():
        if "Model Name:" in line:
            model = line.split(":", 1)[1].strip()
            # Try to append chip info for a richer label
            for l2 in raw.splitlines():
                if "Chip:" in l2:
                    chip = l2.split(":", 1)[1].strip()
                    return f"{model} ({chip})"
            return model
    return platform.machine() or "N/A"


def detect_cpu() -> str:
    """Return CPU description with core breakdown (macOS)."""
    raw = run(["system_profiler", "SPHardwareDataType"])
    chip = cores = None
    for line in raw.splitlines():
        if "Chip:" in line:
            chip = line.split(":", 1)[1].strip()
        if "Total Number of Cores:" in line:
            cores = line.split(":", 1)[1].strip()
            # Reformat: "10 (4 Performance and 6 Efficiency)" → "10-core: 4P+6E"
            m = re.match(r"(\d+)\s*\((\d+) Performance and (\d+) Efficiency\)", cores)
            if m:
                total, perf, eff = m.group(1), m.group(2), m.group(3)
                cores = f"{total}-core: {perf}P+{eff}E"
    if chip and cores:
        return f"{chip} ({cores})"
    if chip:
        return chip
    # Fallback: sysctl
    return run(["sysctl", "-n", "machdep.cpu.brand_string"])


def detect_ram() -> str:
    """Return RAM size in human-readable form."""
    raw = run(["system_profiler", "SPHardwareDataType"])
    for line in raw.splitlines():
        if "Memory:" in line:
            val = line.split(":", 1)[1].strip()
            # Check if it's Apple Silicon (unified memory)
            chip_raw = run(["system_profiler", "SPHardwareDataType"])
            is_apple_silicon = any(
                "Apple M" in l for l in chip_raw.splitlines()
            )
            suffix = " unified memory" if is_apple_silicon else ""
            return val + suffix
    # Fallback: sysctl
    try:
        bytes_str = run(["sysctl", "-n", "hw.memsize"])
        if bytes_str.isdigit():
            gb = int(bytes_str) // (1024 ** 3)
            return f"{gb} GB"
    except Exception:
        pass
    return "N/A"


def detect_os() -> str:
    """Return OS name + version."""
    # macOS: sw_vers gives the real marketing name & version
    name    = run(["sw_vers", "-productName"],    "macOS")
    version = run(["sw_vers", "-productVersion"], "")
    build   = run(["sw_vers", "-buildVersion"],   "")
    if version:
        label = f"{name} {version}"
        if build:
            label += f" (Build {build})"
        return label
    return platform.platform()


def detect_node() -> str:
    out = run(["node", "--version"])
    # Strip leading 'v'
    return out.lstrip("v") if out != "N/A" else "N/A"


def detect_npm() -> str:
    out = run(["npm", "--version"])
    return out if out != "N/A" else "N/A"


def detect_python() -> str:
    v = platform.python_version()
    impl = platform.python_implementation()
    return f"{impl} {v}" if impl else v


def detect_k6() -> str:
    raw = run(["k6", "version"])
    # "k6 v2.2.0 (commit/devel, go1.26.5, darwin/arm64)"
    m = re.search(r"k6\s+v?([\d.]+)", raw)
    if m:
        return m.group(1)
    return raw.split()[1].lstrip("v") if " " in raw else raw


def detect_npm_package(pkg_name: str, search_dirs: list[Path]) -> str:
    """Find an npm package version from node_modules across multiple service dirs."""
    for base in search_dirs:
        pkg_json = base / "node_modules" / pkg_name / "package.json"
        if pkg_json.exists():
            try:
                with open(pkg_json) as f:
                    data = json.load(f)
                return data.get("version", "N/A")
            except Exception:
                continue
    # Fallback: ask node directly
    for base in search_dirs:
        try:
            result = subprocess.run(
                ["node", "-e", f"console.log(require('{pkg_name}/package.json').version)"],
                capture_output=True, text=True, timeout=10, cwd=str(base)
            )
            v = result.stdout.strip()
            if v and "Error" not in v:
                return v
        except Exception:
            continue
    return "N/A"


def detect_arch() -> str:
    raw = run(["uname", "-m"])
    mapping = {"arm64": "ARM64 (Apple Silicon)", "x86_64": "x86-64 (Intel)"}
    return mapping.get(raw, raw)


# ─────────────────────────────────────────────────────────────────────────────
# Build the spec table
# ─────────────────────────────────────────────────────────────────────────────

def collect_specs(project_root: Path) -> list[tuple[str, str, str]]:
    """
    Return list of (component, specification, detected_value) tuples.
    'component' groups rows for the LaTeX multirow.
    """
    service_dirs = [
        project_root / "gateway",
        project_root / "user-service",
        project_root / "product-service",
        project_root / "order-service",
    ]

    info("Detecting hardware...")
    machine = detect_machine()
    cpu     = detect_cpu()
    ram     = detect_ram()

    info("Detecting OS...")
    os_str  = detect_os()
    arch    = detect_arch()

    info("Detecting runtimes...")
    node_v  = detect_node()
    npm_v   = detect_npm()
    python_v = detect_python()

    info("Detecting k6...")
    k6_v = detect_k6()

    info("Detecting npm packages...")
    express_v      = detect_npm_package("express",            service_dirs)
    jwt_v          = detect_npm_package("jsonwebtoken",       service_dirs)
    rate_limit_v   = detect_npm_package("express-rate-limit", service_dirs)
    proxy_v        = detect_npm_package("http-proxy-middleware", service_dirs)

    # ── Build rows ────────────────────────────────────────────────────────────
    # (group, label, value)
    rows = [
        # Hardware
        ("Hardware", "Machine",   machine),
        ("Hardware", "CPU",       cpu),
        ("Hardware", "RAM",       ram),
        ("Hardware", "Architecture", arch),
        # OS & Runtime
        ("Environment", "Operating System", os_str),
        ("Environment", "Node.js",          node_v),
        ("Environment", "npm",              npm_v),
        ("Environment", "Python",           python_v),
        # Framework & Libraries
        ("Software", "Express",              express_v),
        ("Software", "jsonwebtoken",         jwt_v),
        ("Software", "express-rate-limit",   rate_limit_v),
        ("Software", "http-proxy-middleware", proxy_v),
        # Load testing
        ("Load Testing", "Tool",    "k6"),
        ("Load Testing", "Version", k6_v),
        # Network
        ("Network", "Interface", "localhost (loopback)"),
        ("Network", "Protocol",  "HTTP/1.1"),
    ]

    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Renderers
# ─────────────────────────────────────────────────────────────────────────────

def render_terminal(rows: list[tuple[str, str, str]]):
    """Pretty-print a grouped table to stdout."""
    COL1, COL2, COL3 = 18, 28, 46
    TOTAL = COL1 + COL2 + COL3 + 10

    print(f"\n{BOLD}{'═' * TOTAL}{RESET}")
    print(f"{BOLD}  Test Environment Specification{RESET}")
    print(f"{BOLD}{'═' * TOTAL}{RESET}")
    fmt = f"  {{:<{COL1}}}  {{:<{COL2}}}  {{:<{COL3}}}"
    print(fmt.format("Group", "Component", "Detected Value"))
    print("  " + "─" * (TOTAL - 2))

    current_group = None
    for group, label, value in rows:
        grp_display = group if group != current_group else ""
        current_group = group
        print(fmt.format(grp_display, label, value))

    print(f"{BOLD}{'═' * TOTAL}{RESET}\n")


def render_markdown(rows: list[tuple[str, str, str]]) -> str:
    lines = [
        "## Test Environment Specification\n",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n",
        "",
        "| Group | Component | Value |",
        "|---|---|---|",
    ]
    for group, label, value in rows:
        lines.append(f"| {group} | {label} | `{value}` |")
    return "\n".join(lines) + "\n"


def render_csv(rows: list[tuple[str, str, str]]) -> list[dict]:
    return [{"group": g, "component": l, "value": v} for g, l, v in rows]


def render_latex(rows: list[tuple[str, str, str]]) -> str:
    """
    Generate a LaTeX table compatible with IEEE two-column format.
    Uses booktabs + multirow.  Add \\usepackage{booktabs,multirow} in preamble.
    """
    # Group consecutive same-group rows for multirow
    from itertools import groupby

    grouped = []
    for group, members in groupby(rows, key=lambda r: r[0]):
        members = list(members)
        grouped.append((group, members))

    lines = [
        r"% ── Preamble: \usepackage{booktabs,multirow,array} ──────────────────",
        r"\begin{table}[!ht]",
        r"  \centering",
        r"  \caption{Test Environment Specification}",
        r"  \label{tab:env-spec}",
        r"  \begin{tabular}{@{}llp{5cm}@{}}",
        r"    \toprule",
        r"    \textbf{Group} & \textbf{Component} & \textbf{Value} \\",
        r"    \midrule",
    ]

    for i, (group, members) in enumerate(grouped):
        n = len(members)
        for j, (_, label, value) in enumerate(members):
            # Escape special LaTeX characters
            val_esc = (value
                       .replace("_", r"\_")
                       .replace("&", r"\&")
                       .replace("%", r"\%")
                       .replace("#", r"\#")
                       .replace("$", r"\$")
                       .replace("{", r"\{")
                       .replace("}", r"\}")
                       .replace("~", r"\textasciitilde{}")
                       .replace("^", r"\textasciicircum{}"))
            lbl_esc = label.replace("_", r"\_")

            if j == 0:
                grp_cell = (
                    f"    \\multirow{{{n}}}{{*}}{{{group}}}"
                    if n > 1
                    else f"    {group}"
                )
                lines.append(f"{grp_cell} & {lbl_esc} & {val_esc} \\\\")
            else:
                lines.append(f"     & {lbl_esc} & {val_esc} \\\\")

        # Separator between groups (except last)
        if i < len(grouped) - 1:
            lines.append(r"    \midrule")

    lines += [
        r"    \bottomrule",
        r"  \end{tabular}",
        r"\end{table}",
    ]
    return "\n".join(lines) + "\n"


def render_txt(rows: list[tuple[str, str, str]], generated_at: str) -> str:
    """Plain text report for archival."""
    lines = [
        "TEST ENVIRONMENT SPECIFICATION",
        "=" * 60,
        f"Generated : {generated_at}",
        "=" * 60,
        "",
    ]
    current_group = None
    for group, label, value in rows:
        if group != current_group:
            lines.append(f"[{group}]")
            current_group = group
        lines.append(f"  {label:<28}{value}")
    lines.append("")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-o", "--output", type=str, default=None,
        help="Output directory for generated files (default: docs/)"
    )
    args = parser.parse_args()

    script_dir   = Path(__file__).resolve().parent
    project_root = script_dir.parent

    out_dir = Path(args.output) if args.output else project_root / "docs"
    out_dir.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now(tz=timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")

    print(f"\n{'='*60}")
    print("  ms-jwt-research — Environment Spec Reporter")
    print(f"  Output → {out_dir}")
    print(f"{'='*60}\n")

    # ── Collect ────────────────────────────────────────────────────────────────
    rows = collect_specs(project_root)

    # ── Terminal ───────────────────────────────────────────────────────────────
    render_terminal(rows)

    # ── Markdown ───────────────────────────────────────────────────────────────
    md_path = out_dir / "environment-spec.md"
    md_path.write_text(render_markdown(rows), encoding="utf-8")
    ok(f"Markdown  → {md_path}")

    # ── LaTeX ──────────────────────────────────────────────────────────────────
    tex_path = out_dir / "environment-spec.tex"
    tex_path.write_text(render_latex(rows), encoding="utf-8")
    ok(f"LaTeX     → {tex_path}")

    # ── CSV ────────────────────────────────────────────────────────────────────
    csv_path = out_dir / "environment-spec.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["group", "component", "value"])
        writer.writeheader()
        writer.writerows(render_csv(rows))
    ok(f"CSV       → {csv_path}")

    # ── Plain text ─────────────────────────────────────────────────────────────
    txt_path = out_dir / "environment-spec-report.txt"
    txt_path.write_text(render_txt(rows, generated_at), encoding="utf-8")
    ok(f"Text      → {txt_path}")

    print(f"\n{'='*60}")
    print("  Done! Copy the LaTeX snippet directly into your IEEE paper.")
    print(f"  File: {tex_path}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
