#!/usr/bin/env bash
set -euo pipefail

SESSION="heritage_trail"
BACKEND_PORT="${BACKEND_PORT:-8000}"
PRODUCTION_URL="https://finflowfx.biz"
ENV_FILE="$(cd "$(dirname "$0")" && pwd)/.env"

tmux kill-session -t "$SESSION" 2>/dev/null || true

tmux new-session -d -s "$SESSION" -c "$(pwd)"

tmux rename-window -t "$SESSION:0" "Setup"
tmux send-keys -t "$SESSION:0" "sed -i \"s|TELEGRAM_WEBHOOK_URL=.*|TELEGRAM_WEBHOOK_URL=${PRODUCTION_URL}/webhook/telegram|\" \"$ENV_FILE\" && echo \"Webhook URL set to ${PRODUCTION_URL}/webhook/telegram\"" C-m

tmux new-window -t "$SESSION:1" -c "$(pwd)/backend"
tmux rename-window -t "$SESSION:1" "Backend"
tmux send-keys -t "$SESSION:1" "sleep 1 && python3 -m uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload" C-m

tmux new-window -t "$SESSION:2" -c "$(pwd)"
tmux rename-window -t "$SESSION:2" "Shell"

tmux select-window -t "$SESSION:1"
tmux attach-session -t "$SESSION"
