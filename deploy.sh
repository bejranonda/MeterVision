#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

SERVICE_NAME="metervision"
SERVICE_FILE="metervision.service"
INSTALL_DIR="/home/ogema/MeterReading"

echo "🚀 Starting deployment of $SERVICE_NAME..."

# 1. Create/Overwrite the service file to ensure it's correct
echo "📝 Generating systemd service file..."
cat > $SERVICE_FILE <<EOL
[Unit]
Description=MeterVision API
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
EnvironmentFile=$INSTALL_DIR/.env.local
ExecStart=$INSTALL_DIR/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
EOL

# 2. Copy to systemd directory
echo "jm Copying service file to /etc/systemd/system/..."
cp $SERVICE_FILE /etc/systemd/system/$SERVICE_FILE

# 3. Reload systemd to recognize new service
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload

# 4. Enable service on boot
echo "🔌 Enabling service on boot..."
systemctl enable $SERVICE_NAME

# 5. Restart the service (stops if running, starts if stopped)
echo "▶️  Starting service..."
systemctl restart $SERVICE_NAME

# 6. Show status
echo "✅ Deployment complete! Checking status..."
systemctl status $SERVICE_NAME --no-pager

echo ""
echo "🌍 Application should be accessible at: http://$(curl -s ifconfig.me):8000"
