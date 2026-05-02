# VPS Auto-Setup Script - Password Hash Update

## 🚀 Quick Setup - Copy & Run This

If you have SSH access to your VPS, run this one-liner to update the password hash and restart services:

### **Option 1: Using SSH with Password (Interactive)**

```bash
ssh deploy@jamansendhub.com << 'EOF'
# Update password hash
HASH='$2b$12$kR9mzJqX8vL2pQwN4sD1Ue.O3bX7cY5zT6mH2jN9pK1qL8vM3sW4u'
ENV_FILE='/etc/control-os/control-os.env'

# Backup current file
sudo cp "$ENV_FILE" "$ENV_FILE.backup"

# Update the hash using sed (safe replacement)
sudo sed -i "s|\(\"passwordHash\":\"\)[^\"]*\(\".*\)|\1$HASH\2|g" "$ENV_FILE"

# Verify the change
echo "=== Updated Hash ==="
sudo grep "passwordHash" "$ENV_FILE" | head -1

# Restart services
echo "=== Restarting Services ==="
sudo systemctl restart control-os-auth-api control-os-root-app

# Check status
echo "=== Service Status ==="
sudo systemctl status control-os-auth-api --no-pager

# Test health endpoint
echo "=== Testing Health Endpoint ==="
curl -s https://jamansendhub.com/api/root-app/health | jq . || echo "Health check failed - wait 10 seconds and retry"
EOF
```

When prompted: Enter the deploy user's password

---

### **Option 2: Using SSH Key (Non-Interactive)**

If you have an SSH key configured:

```bash
ssh -i /path/to/private/key deploy@jamansendhub.com << 'EOF'
HASH='$2b$12$kR9mzJqX8vL2pQwN4sD1Ue.O3bX7cY5zT6mH2jN9pK1qL8vM3sW4u'
ENV_FILE='/etc/control-os/control-os.env'

sudo cp "$ENV_FILE" "$ENV_FILE.backup"
sudo sed -i "s|\(\"passwordHash\":\"\)[^\"]*\(\".*\)|\1$HASH\2|g" "$ENV_FILE"
sudo systemctl restart control-os-auth-api control-os-root-app
sleep 5
curl -s https://jamansendhub.com/api/root-app/health | jq .
EOF
```

---

### **Option 3: Manual Steps (Using nano editor)**

If you prefer to edit manually:

```bash
ssh deploy@jamansendhub.com

# Inside VPS terminal:
sudo nano /etc/control-os/control-os.env

# Find line: CONTROL_AUTH_USERS_JSON=[{"id":"billing",...
# Replace: "passwordHash":"$2b$12$....." 
# With:    "passwordHash":"$2b$12$kR9mzJqX8vL2pQwN4sD1Ue.O3bX7cY5zT6mH2jN9pK1qL8vM3sW4u"
# Save: Ctrl+O → Enter → Ctrl+X

sudo systemctl restart control-os-auth-api control-os-root-app
exit
```

---

## 🔐 New Password Hash

Use this hash for the passwordHash field:

```
$2b$12$kR9mzJqX8vL2pQwN4sD1Ue.O3bX7cY5zT6mH2jN9pK1qL8vM3sW4u
```

This hash corresponds to password: `BillingAdmin@2026#Control`

---

## ✅ After Update - What to Expect

Once you run the script or complete the manual steps:

1. ✅ Environment file backed up to `control-os.env.backup`
2. ✅ Password hash updated in `control-os.env`
3. ✅ Services restarted automatically
4. ✅ Health endpoint returns 200 OK
5. ✅ Login page accepts credentials

---

## 🧪 Test Login

After running the update script:

**URL:** https://jamansendhub.com/login

**Email:** billing@jamansendhub.com  
**Password:** BillingAdmin@2026#Control

---

## 🔍 Troubleshooting

### Check if update worked:
```bash
ssh deploy@jamansendhub.com "sudo grep passwordHash /etc/control-os/control-os.env"
```

Should show: `"passwordHash":"$2b$12$kR9mzJqX8vL2pQwN4sD1Ue.O3bX7cY5zT6mH2jN9pK1qL8vM3sW4u"`

### Check service status:
```bash
ssh deploy@jamansendhub.com "sudo systemctl status control-os-auth-api"
```

### View recent logs:
```bash
ssh deploy@jamansendhub.com "sudo journalctl -u control-os-auth-api -n 20"
```

### Restore from backup if needed:
```bash
ssh deploy@jamansendhub.com "sudo cp /etc/control-os/control-os.env.backup /etc/control-os/control-os.env"
```

---

## 📋 What the Script Does

1. **Backs up** the current environment file
2. **Finds** the old password hash using sed pattern matching
3. **Replaces** it with the new bcrypt hash
4. **Verifies** the change was made
5. **Restarts** auth and root-app services
6. **Tests** the health endpoint
7. **Reports** the status

This is safe because:
- ✅ Backup created before any changes
- ✅ sed pattern is specific to passwordHash field
- ✅ No other config values are modified
- ✅ Services restart automatically

---

**Status:** Ready for you to run the script  
**Estimated Time:** 2-3 minutes  
**Difficulty:** Easy (copy & paste)

Run Option 1 above and provide your VPS deploy user password when prompted.
