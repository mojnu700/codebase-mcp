#!/bin/bash
# Direct VPS Update Script
# Run this on your local machine to update the VPS password hash

VPS_IP="178.104.201.73"
VPS_USER="root"
HASH='$2b$12$kR9mzJqX8vL2pQwN4sD1Ue.O3bX7cY5zT6mH2jN9pK1qL8vM3sW4u'

echo "🔧 Connecting to VPS at $VPS_IP..."
echo "🔐 Enter your root password when prompted"
echo ""

ssh root@$VPS_IP << 'COMMANDS'
#!/bin/bash

ENV_FILE='/etc/control-os/control-os.env'

echo "📄 Backing up environment file..."
sudo cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%s)"

echo "🔄 Updating password hash..."
HASH='$2b$12$kR9mzJqX8vL2pQwN4sD1Ue.O3bX7cY5zT6mH2jN9pK1qL8vM3sW4u'
sudo sed -i "s|\(\"passwordHash\":\"\)[^\"]*\(\".*\)|\1$HASH\2|g" "$ENV_FILE"

echo "✅ Verifying update..."
sudo grep "passwordHash" "$ENV_FILE" | grep -o 'kR9mzJqX8vL2pQwN4sD1Ue' && echo "Hash updated successfully!" || echo "Hash update FAILED"

echo "🔄 Restarting services..."
sudo systemctl restart control-os-auth-api control-os-root-app
sleep 3

echo "📊 Checking service status..."
sudo systemctl is-active control-os-auth-api && echo "✅ auth-api is running"
sudo systemctl is-active control-os-root-app && echo "✅ root-app is running"

echo ""
echo "🧪 Testing health endpoint..."
curl -s https://jamansendhub.com/api/root-app/health | grep -o '"status":"[^"]*"' || echo "Health check pending..."

echo ""
echo "✅ VPS Update Complete!"
echo "You can now login at: https://jamansendhub.com/login"
echo "Email: billing@jamansendhub.com"
echo "Password: BillingAdmin@2026#Control"

COMMANDS

echo ""
echo "✨ Done!"
