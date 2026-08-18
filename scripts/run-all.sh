#!/usr/bin/env bash
# =============================================================================
# scripts/run-all.sh
# Full-automated experiment orchestrator for ms-jwt-research.
#
# Usage:
#   ./scripts/run-all.sh [OPTIONS]
#
# Options:
#   -n, --runs       N      Number of runs per scenario  (default: 5)
#   -c, --cooldown   S      Cool-down seconds between runs  (default: 45)
#   -s, --scenario   NAME   Run a single scenario instead of all four.
#                           Choices: normal-no-security | normal-with-security
#                                    burst-no-security  | burst-with-security
#   -h, --help              Show this help message and exit.
#
# Prerequisites:
#   - k6 installed and in PATH
#   - Node.js v18+
#   - npm install:all already run once
# =============================================================================

set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
RUNS=5
COOLDOWN=45
ONLY_SCENARIO=""
STARTUP_WAIT=6      # seconds to wait after starting services before k6

# ── Colours ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

log_info()    { echo -e "${CYAN}[INFO]${RESET}  $*"; }
log_ok()      { echo -e "${GREEN}[OK]${RESET}    $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
log_error()   { echo -e "${RED}[ERROR]${RESET} $*"; }
log_section() { echo -e "\n${BOLD}════════════════════════════════════════${RESET}"; echo -e "${BOLD} $* ${RESET}"; echo -e "${BOLD}════════════════════════════════════════${RESET}"; }

# ── Argument parsing ──────────────────────────────────────────────────────────
usage() {
  sed -n '/^# Usage/,/^# Prerequisites/p' "$0" | grep -v '^#$' | sed 's/^# \?//'
  exit 0
}

while [[ $# -gt 0 ]]; do
  case $1 in
    -n|--runs)       RUNS="$2";          shift 2 ;;
    -c|--cooldown)   COOLDOWN="$2";      shift 2 ;;
    -s|--scenario)   ONLY_SCENARIO="$2"; shift 2 ;;
    -h|--help)       usage ;;
    *) log_error "Unknown argument: $1"; usage ;;
  esac
done

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOAD_DIR="$ROOT_DIR/load-testing"
RESULTS_DIR="$LOAD_DIR/results"

# ── Dependency checks ─────────────────────────────────────────────────────────
if ! command -v k6 &>/dev/null; then
  log_error "k6 not found in PATH. Install from https://k6.io/docs/getting-started/installation/"
  exit 1
fi
if ! command -v node &>/dev/null; then
  log_error "node not found in PATH."
  exit 1
fi

# ── Scenario definitions ──────────────────────────────────────────────────────
# Format: "scenario-name|k6-script|SECURITY_ENABLED"
ALL_SCENARIOS=(
  "normal-no-security|normal-traffic.js|false"
  "normal-with-security|normal-traffic.js|true"
  "burst-no-security|burst-traffic.js|false"
  "burst-with-security|burst-traffic.js|true"
)

# Filter to single scenario if requested
if [[ -n "$ONLY_SCENARIO" ]]; then
  VALID_NAMES=("normal-no-security" "normal-with-security" "burst-no-security" "burst-with-security")
  if [[ ! " ${VALID_NAMES[*]} " =~ " ${ONLY_SCENARIO} " ]]; then
    log_error "Invalid scenario '${ONLY_SCENARIO}'. Choose from: ${VALID_NAMES[*]}"
    exit 1
  fi
  SCENARIOS=()
  for entry in "${ALL_SCENARIOS[@]}"; do
    name="${entry%%|*}"
    [[ "$name" == "$ONLY_SCENARIO" ]] && SCENARIOS+=("$entry")
  done
else
  SCENARIOS=("${ALL_SCENARIOS[@]}")
fi

# ── Process-group helpers ─────────────────────────────────────────────────────
SERVER_PGID=""
SERVER_PID=""

start_services() {
  local security="$1"
  log_info "Starting microservices (SECURITY_ENABLED=${security})..."

  # Launch in its own process group so we can kill the whole tree cleanly
  set -m
  SECURITY_ENABLED="$security" npm --prefix "$ROOT_DIR" run start \
    2>>"$LOG_DIR/services.stderr.log" \
    1>>"$LOG_DIR/services.stdout.log" &
  SERVER_PID=$!
  SERVER_PGID=$(ps -o pgid= -p "$SERVER_PID" 2>/dev/null | tr -d ' ' || echo "")
  set +m

  log_info "Services PID=$SERVER_PID PGID=$SERVER_PGID — waiting ${STARTUP_WAIT}s for startup..."
  sleep "$STARTUP_WAIT"

  # Quick health-check on gateway port 3000 (up to 10s extra)
  local retries=10
  while ! curl -sf http://localhost:3000/ &>/dev/null && [[ $retries -gt 0 ]]; do
    sleep 1
    (( retries-- )) || true
  done
  if [[ $retries -eq 0 ]]; then
    log_warn "Gateway did not respond on port 3000 — proceeding anyway (check services.stderr.log)."
  else
    log_ok "Gateway is up."
  fi
}

stop_services() {
  if [[ -n "$SERVER_PGID" && "$SERVER_PGID" != "0" ]]; then
    log_info "Stopping services (PGID=$SERVER_PGID)..."
    kill -- "-$SERVER_PGID" 2>/dev/null || true
    sleep 2
    # Force-kill any lingering node processes on our ports
    for port in 3000 3001 3002 3003; do
      lsof -ti tcp:"$port" 2>/dev/null | xargs kill -9 2>/dev/null || true
    done
    SERVER_PGID=""
    SERVER_PID=""
    log_ok "Services stopped."
  fi
}

# Always stop services on EXIT/interrupt
trap 'stop_services' EXIT INT TERM

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
log_section "ms-jwt-research Experiment Runner"
echo -e "  Scenarios : ${#SCENARIOS[@]}"
echo -e "  Runs/each : ${BOLD}${RUNS}${RESET}"
echo -e "  Cooldown  : ${COOLDOWN}s between runs"
echo -e "  Results   : ${RESULTS_DIR}"
echo ""

TOTAL_RUNS=$(( ${#SCENARIOS[@]} * RUNS ))
COMPLETED=0
FAILED_RUNS=()

# ── Main loop ─────────────────────────────────────────────────────────────────
for scenario_entry in "${SCENARIOS[@]}"; do
  IFS='|' read -r SCENARIO_NAME K6_SCRIPT SECURITY <<< "$scenario_entry"

  log_section "Scenario: ${SCENARIO_NAME}  (${RUNS} runs)"

  SCENARIO_DIR="$RESULTS_DIR/$SCENARIO_NAME"
  LOG_DIR="$SCENARIO_DIR/logs"
  mkdir -p "$SCENARIO_DIR" "$LOG_DIR"

  for i in $(seq 1 "$RUNS"); do
    RUN_DIR="$SCENARIO_DIR/run-${i}"
    mkdir -p "$RUN_DIR"

    echo -e "\n${YELLOW}▶ Run ${i}/${RUNS}${RESET} — ${SCENARIO_NAME}"

    # Start fresh services for every run (avoids TCP state carryover)
    start_services "$SECURITY"

    # Run k6 — save only summary (raw JSON can be several GB)
    K6_LOG="$LOG_DIR/k6-run-${i}.log"
    SUMMARY_FILE="$RUN_DIR/summary.json"

    set +e
    k6 run \
      --summary-export="$SUMMARY_FILE" \
      --log-output="file=${K6_LOG}" \
      "$LOAD_DIR/$K6_SCRIPT" \
      2>&1 | tee "$LOG_DIR/k6-run-${i}.stdout.log"
    K6_EXIT=$?
    set -e

    if [[ -f "$SUMMARY_FILE" ]]; then
      log_ok "Run ${i} complete → ${SUMMARY_FILE}"
    else
      log_warn "Summary file not generated for run ${i}."
      FAILED_RUNS+=("${SCENARIO_NAME}/run-${i}")
    fi
    (( COMPLETED++ )) || true

    # Stop services after this run
    stop_services

    # Cool-down between runs (skip after last run of a scenario)
    if [[ $i -lt $RUNS ]]; then
      log_info "Cooling down for ${COOLDOWN}s (TCP TIME_WAIT drain)..."
      sleep "$COOLDOWN"
    fi
  done

  log_ok "Scenario '${SCENARIO_NAME}' done.  Results → ${SCENARIO_DIR}"
done

# ── Final report ──────────────────────────────────────────────────────────────
echo ""
log_section "All runs complete"
echo -e "  Total scheduled : ${TOTAL_RUNS}"
echo -e "  Completed       : ${COMPLETED}"

if [[ ${#FAILED_RUNS[@]} -gt 0 ]]; then
  log_warn "Runs with missing summary files:"
  for f in "${FAILED_RUNS[@]}"; do echo -e "    ${RED}✗${RESET} $f"; done
else
  log_ok "All summary files captured successfully."
fi

echo ""
log_info "Next step — run the analysis script:"
echo -e "  ${BOLD}python scripts/analyze.py --runs ${RUNS}${RESET}"
echo ""
