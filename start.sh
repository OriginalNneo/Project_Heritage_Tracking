#!/usr/bin/env bash
set -euo pipefail

SESSION="heritage_trail"
BACKEND_PORT="${BACKEND_PORT:-8000}"
ENV_FILE="$(cd "$(dirname "$0")" && pwd)/.env"

tmux kill-session -t "$SESSION" 2>/dev/null || true

tmux new-session -d -s "$SESSION" -c "$(pwd)"

tmux rename-window -t "$SESSION:0" "Ngrok"
tmux send-keys -t "$SESSION:0" "ngrok http $BACKEND_PORT" C-m

tmux new-window -t "$SESSION:1" -c "$(pwd)/backend"
tmux rename-window -t "$SESSION:1" "Setup"
tmux send-keys -t "$SESSION:1" "sleep 3" C-m
tmux send-keys -t "$SESSION:1" "NGROK_URL=\$(curl -s http://127.0.0.1:4040/api/tunnels | python3 -c 'import sys,json;print(json.load(sys.stdin)[\"tunnels\"][0][\"public_url\"])') && sed -i \"s|TELEGRAM_WEBHOOK_URL=.*|TELEGRAM_WEBHOOK_URL=\${NGROK_URL}/webhook/telegram|\" \"$ENV_FILE\" && echo \"Webhook URL set to \${NGROK_URL}/webhook/telegram\"" C-m

tmux new-window -t "$SESSION:2" -c "$(pwd)/backend"
tmux rename-window -t "$SESSION:2" "Backend"
tmux send-keys -t "$SESSION:2" "sleep 5 && python3 -m uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload" C-m

tmux new-window -t "$SESSION:3" -c "$(pwd)"
tmux rename-window -t "$SESSION:3" "Shell"

tmux select-window -t "$SESSION:2"
tmux attach-session -t "$SESSION"
