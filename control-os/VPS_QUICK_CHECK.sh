#!/bin/bash
# Quick VPS Diagnostic - Run this to see current config

echo "🔍 Checking VPS Configuration..."
echo ""

# Check if we can reach the VPS
echo "1️⃣ Testing SSH connection to VPS..."
ssh -o ConnectTimeout=5 deploy@jamansendhub.com "echo 'SSH connection successful'" 2>&1

echo ""
echo "2️⃣ Current password hash on VPS:"
ssh deploy@jamansendhub.com "sudo grep 'passwordHash' /etc/control-os/control-os.env" 2>&1 | head -1

echo ""
echo "3️⃣ Current auth mode:"
ssh deploy@jamansendhub.com "sudo grep 'CONTROL_AUTH_MODE' /etc/control-os/control-os.env" 2>&1

echo ""
echo "4️⃣ Service status:"
ssh deploy@jamansendhub.com "sudo systemctl is-active control-os-auth-api" 2>&1

echo ""
echo "5️⃣ Recent auth logs (last 5 lines):"
ssh deploy@jamansendhub.com "sudo journalctl -u control-os-auth-api -n 5 --no-pager" 2>&1

echo ""
echo "✅ Diagnostic complete"
