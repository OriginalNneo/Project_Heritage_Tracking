#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/amk_heritage"
SERVICE_NAME="amk-heritage"

echo "=== AMK Heritage Trail - Deploy to finflowfx.biz ==="
echo ""

if [ ! -f "$APP_DIR/.env" ]; then
  echo "[!] No .env found. Copying .env.example..."
  cp "$APP_DIR/.env.example" "$APP_DIR/.env"
  echo "[!] Edit $APP_DIR/.env with your TELEGRAM_BOT_TOKEN and other settings"
fi

echo "[1/4] Installing Python dependencies..."
cd "$APP_DIR/backend"
pip3 install -r requirements.txt

echo "[2/4] Installing dashboard Node dependencies..."
cd "$APP_DIR/dashboard"
npm install

echo "[3/4] Creating systemd services..."

sudo tee /etc/systemd/system/${SERVICE_NAME}-backend.service > /dev/null <<'EOF'
[Unit]
Description=AMK Heritage Trail - FastAPI Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/amk_heritage/backend
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

echo "[4/4] Setting up Nginx..."
echo "Copy nginx-amk-heritage.conf to your VPS and run:"
echo "  sudo cp nginx-amk-heritage.conf /etc/nginx/sites-available/finflow"
echo "  sudo nginx -t && sudo systemctl reload nginx"

echo ""
echo "=== Deployment files ready ==="
echo ""
echo "Next steps on the VPS:"
echo "  1. Edit $APP_DIR/.env with your settings"
echo "  2. Copy and enable the nginx config"
echo "  3. sudo systemctl daemon-reload"
echo "  4. sudo systemctl enable ${SERVICE_NAME}-backend"
echo "  5. sudo systemctl start ${SERVICE_NAME}-backend"
echo "  6. Set Telegram webhook: https://finflowfx.biz/webhook/telegram"
