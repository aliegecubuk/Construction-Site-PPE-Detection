#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PID_DIR="$ROOT_DIR/.runtime/pids"

stop_from_pid_file() {
  local name="$1"
  local pid_file="$PID_DIR/$name.pid"

  if [[ ! -f "$pid_file" ]]; then
    echo "$name için pid dosyası yok."
    return
  fi

  local pid
  pid="$(cat "$pid_file")"
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    echo "$name durduruldu (pid: $pid)."
  else
    echo "$name zaten durmuş görünüyor."
  fi

  rm -f "$pid_file"
}

stop_matching_process() {
  local label="$1"
  local pattern="$2"

  mapfile -t pids < <(pgrep -f "$pattern" || true)
  if [[ "${#pids[@]}" -eq 0 ]]; then
    return
  fi

  for pid in "${pids[@]}"; do
    kill "$pid" 2>/dev/null || true
    echo "$label durduruldu (pid: $pid)."
  done
}

stop_from_pid_file "angular"
stop_from_pid_file "dotnet"
stop_from_pid_file "python"

# PID dosyası kalmamış ama süreç çalışıyorsa yine temizle.
stop_matching_process "angular" "ng serve .*--port 4200"
stop_matching_process "dotnet" "ReportAi.Orchestrator.Api"
stop_matching_process "python" "uvicorn main:app --host 127.0.0.1 --port 8000"
