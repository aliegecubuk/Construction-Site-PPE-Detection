#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
RUNTIME_DIR="$ROOT_DIR/.runtime"
LOG_DIR="$RUNTIME_DIR/logs"
PID_DIR="$RUNTIME_DIR/pids"

PYTHON_APP_DIR="$ROOT_DIR/ai-service"
DOTNET_APP_DIR="$ROOT_DIR/backend/ReportAi.Orchestrator.Api"
ANGULAR_APP_DIR="$ROOT_DIR/frontend"

mkdir -p "$LOG_DIR" "$PID_DIR"

# Eski stack artıkları varsa temizle.
bash "$SCRIPT_DIR/stop_report_ai_stack.sh" >/dev/null 2>&1 || true

require_file() {
  local path="$1"
  local message="$2"
  if [[ ! -e "$path" ]]; then
    echo "Eksik: $message ($path)" >&2
    exit 1
  fi
}

ensure_not_running() {
  local name="$1"
  local pid_file="$PID_DIR/$name.pid"

  if [[ -f "$pid_file" ]]; then
    local pid
    pid="$(cat "$pid_file")"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      echo "$name zaten çalışıyor (pid: $pid). Önce 'bash stop.sh' çalıştırın." >&2
      exit 1
    fi
    rm -f "$pid_file"
  fi
}

wait_for_pid() {
  local pattern="$1"
  local pid_file="$2"

  for _ in {1..20}; do
    local pid
    pid="$(pgrep -n -f "$pattern" || true)"
    if [[ -n "$pid" ]]; then
      printf '%s\n' "$pid" >"$pid_file"
      return 0
    fi
    sleep 1
  done

  echo "Süreç bulunamadı: $pattern" >&2
  return 1
}

start_python() {
  local pid_file="$PID_DIR/python.pid"
  local log_file="$LOG_DIR/python.log"

  ensure_not_running "python"
  require_file "$PYTHON_APP_DIR/venv/bin/python" "Python venv"
  require_file "$PYTHON_APP_DIR/main.py" "FastAPI uygulaması"

  (
    cd "$PYTHON_APP_DIR"
    # Python FastAPI
    # Swagger: http://localhost:8000/docs
    # MJPEG:   http://localhost:8000/api/v1/stream/mjpeg/{camera_id}
    setsid -f bash -lc \
      "exec venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000 >'$log_file' 2>&1 < /dev/null"
  )
  wait_for_pid "python -m uvicorn main:app --host 127.0.0.1 --port 8000" "$pid_file"
}

start_dotnet() {
  local pid_file="$PID_DIR/dotnet.pid"
  local log_file="$LOG_DIR/dotnet.log"

  ensure_not_running "dotnet"
  require_file "$DOTNET_APP_DIR/ReportAi.Orchestrator.Api.csproj" ".NET proje dosyası"

  (
    cd "$DOTNET_APP_DIR"
    # .NET Orchestrator API
    # HTTP API: http://localhost:8080/api/cameras
    # SignalR:  http://localhost:8080/hubs/alerts
    # .NET 8 hedefi olan uygulama, makinede yalnızca .NET 9 runtime varsa da açılabilsin.
    setsid -f bash -lc \
      "exec env DOTNET_ROLL_FORWARD=Major dotnet run --no-launch-profile --urls http://127.0.0.1:8080 >'$log_file' 2>&1 < /dev/null"
  )
  wait_for_pid "ReportAi.Orchestrator.Api" "$pid_file"
}

start_angular() {
  local pid_file="$PID_DIR/angular.pid"
  local log_file="$LOG_DIR/angular.log"

  ensure_not_running "angular"
  require_file "$ANGULAR_APP_DIR/package.json" "Angular package.json"
  require_file "$ANGULAR_APP_DIR/node_modules/.bin/ng" "Angular node_modules"

  (
    cd "$ANGULAR_APP_DIR"
    # Angular UI
    # Frontend: http://localhost:4200
    setsid -f bash -lc \
      "exec ./node_modules/.bin/ng serve --host 127.0.0.1 --port 4200 >'$log_file' 2>&1 < /dev/null"
  )
  wait_for_pid "ng serve --host 127.0.0.1 --port 4200" "$pid_file"
}

print_summary() {
  cat <<EOF
REPORT-AI stack başlatıldı.

Uygulamalar
- Angular UI:         http://localhost:4200
- .NET Orchestrator:  http://localhost:8080/api/cameras
- SignalR Hub:        http://localhost:8080/hubs/alerts
- Python FastAPI:     http://localhost:8000/docs
- Python MJPEG:       http://localhost:8000/api/v1/stream/mjpeg/camera_1

Log dosyaları
- Python:  $LOG_DIR/python.log
- .NET:    $LOG_DIR/dotnet.log
- Angular: $LOG_DIR/angular.log

Durdurmak için:
- bash stop.sh
- bash infrastructure/scripts/stop_report_ai_stack.sh
EOF
}

start_python
start_dotnet
start_angular
sleep 2
print_summary
