#!/usr/bin/env bash
set -euo pipefail

APP_NAME="Auto-Crypto"
DESKTOP_COMMAND_NAME="Auto-Crypto.command"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${HOME}/Desktop/Auto-Crypto.log"
PORT=8004
HOST_NAME="127.0.0.1"
DB_PATH="${ROOT_DIR}/data/auto_crypto.sqlite3"
INSTALL_DEPS=0
EXCHANGE_DEPS=0
START_DISCORD=0
NO_BROWSER=0
LAUNCH=0
PREPARE_ONLY=0

usage() {
  cat <<USAGE
Usage:
  ./install-macos.sh                 Install dependencies and create a Desktop launcher
  ./install-macos.sh --launch        Start ${APP_NAME}

Options:
  --port PORT        FastAPI port (default: ${PORT})
  --host HOST        Bind host (default: ${HOST_NAME})
  --db-path PATH     SQLite database path
  --exchange-deps    Install optional CCXT exchange dependencies
  --start-discord    Start the Discord bot; requires DISCORD_BOT_TOKEN
  --install-deps     Reinstall Python dependencies before launch
  --no-browser       Do not open the browser automatically
  --prepare-only     Install dependencies without starting the app
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --launch) LAUNCH=1 ;;
    --install-deps) INSTALL_DEPS=1 ;;
    --exchange-deps) EXCHANGE_DEPS=1 ;;
    --start-discord) START_DISCORD=1 ;;
    --no-browser) NO_BROWSER=1 ;;
    --prepare-only) PREPARE_ONLY=1 ;;
    --port)
      PORT="${2:?Missing value for --port}"
      shift
      ;;
    --port=*) PORT="${1#*=}" ;;
    --host)
      HOST_NAME="${2:?Missing value for --host}"
      shift
      ;;
    --host=*) HOST_NAME="${1#*=}" ;;
    --db-path)
      DB_PATH="${2:?Missing value for --db-path}"
      shift
      ;;
    --db-path=*) DB_PATH="${1#*=}" ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 2
      ;;
  esac
  shift
done

log() {
  mkdir -p "$(dirname "$LOG_FILE")"
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" | tee -a "$LOG_FILE"
}

require_macos() {
  if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "This installer is intended for macOS." >&2
    exit 1
  fi
}

find_python() {
  for candidate in python3.13 python3.12 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY
    then
      command -v "$candidate"
      return 0
    fi
  done
  return 1
}

prepare_runtime() {
  local python_bin
  python_bin="$(find_python)" || {
    echo "Python 3.11+ is required." >&2
    exit 1
  }

  local venv_dir="${ROOT_DIR}/.venv"
  local venv_python="${venv_dir}/bin/python"
  if [[ ! -x "$venv_python" ]]; then
    log "Creating Python virtual environment"
    "$python_bin" -m venv "$venv_dir"
    INSTALL_DEPS=1
  fi

  if [[ "$INSTALL_DEPS" -eq 1 || ! -d "${venv_dir}/lib" ]]; then
    log "Installing Python dependencies"
    "$venv_python" -m pip install --upgrade pip
    if [[ "$EXCHANGE_DEPS" -eq 1 ]]; then
      (cd "$ROOT_DIR" && "$venv_python" -m pip install -e ".[exchange]")
    else
      (cd "$ROOT_DIR" && "$venv_python" -m pip install -e ".")
    fi
  fi
}

create_desktop_launcher() {
  local desktop_dir="${HOME}/Desktop"
  local command_path="${desktop_dir}/${DESKTOP_COMMAND_NAME}"
  mkdir -p "$desktop_dir"
  cat > "$command_path" <<EOF
#!/usr/bin/env bash
cd "$ROOT_DIR"
exec "$ROOT_DIR/install-macos.sh" --launch
EOF
  chmod +x "$command_path"
  log "Desktop launcher created: ${command_path}"
}

wait_url() {
  local url="$1"
  local seconds="${2:-60}"
  local start
  start="$(date +%s)"
  while (( "$(date +%s)" - start < seconds )); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  return 1
}

launch_app() {
  prepare_runtime
  if [[ "$PREPARE_ONLY" -eq 1 ]]; then
    log "Preparation complete"
    return 0
  fi

  if [[ "$START_DISCORD" -eq 1 && -z "${DISCORD_BOT_TOKEN:-}" ]]; then
    echo "DISCORD_BOT_TOKEN is required when --start-discord is used." >&2
    exit 1
  fi

  local venv_python="${ROOT_DIR}/.venv/bin/python"
  local base_url="http://${HOST_NAME}:${PORT}"
  local pids=()

  mkdir -p "$(dirname "$DB_PATH")"
  export AUTO_CRYPTO_DB_PATH="$DB_PATH"
  export PYTHONPATH="${ROOT_DIR}/src"

  log "Starting API on ${base_url}"
  (cd "$ROOT_DIR" && "$venv_python" -m uvicorn autocrypto.app:create_app_from_env --factory --host "$HOST_NAME" --port "$PORT") >> "$LOG_FILE" 2>&1 &
  pids+=("$!")

  if [[ "$START_DISCORD" -eq 1 ]]; then
    log "Starting Discord bot"
    (cd "$ROOT_DIR" && "$venv_python" -c "from autocrypto.discord_bot import run_from_env; run_from_env()") >> "$LOG_FILE" 2>&1 &
    pids+=("$!")
  fi

  cleanup() {
    for pid in "${pids[@]}"; do
      kill "$pid" >/dev/null 2>&1 || true
    done
  }
  trap cleanup EXIT INT TERM

  if ! wait_url "${base_url}/health" 75; then
    log "API did not become healthy. Recent log output:"
    tail -n 100 "$LOG_FILE" || true
    exit 1
  fi

  log "Ready: ${base_url}/ui"
  log "Database: ${DB_PATH}"
  if [[ "$NO_BROWSER" -eq 0 ]]; then
    open "${base_url}/ui"
  fi
  wait "${pids[@]}"
}

require_macos
if [[ "$LAUNCH" -eq 1 ]]; then
  launch_app
else
  INSTALL_DEPS=1
  PREPARE_ONLY=1
  prepare_runtime
  create_desktop_launcher
  log "Install complete. Double-click '${DESKTOP_COMMAND_NAME}' on the Desktop to start ${APP_NAME}."
fi
