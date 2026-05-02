# VPS Update Methods - No Agent Intervention Needed

আপনি নিজেই এই methods গুলো থেকে যেকোনো একটা use করতে পারেন। আমার কোনো password দিতে হবে না।

---

## **Method 1: VPS Web Console (সবচেয়ে সহজ)**

আপনার VPS provider এর control panel এ যান এবং web-based terminal/console খুলুন।

### **Hetzner Cloud এ:**
1. https://console.hetzner.cloud এ login করুন
2. আপনার server select করুন
3. "Console" tab এ click করুন
4. নিচের command paste করুন

### **Linode এ:**
1. https://cloud.linode.com এ login করুন
2. আপনার Linode select করুন
3. "Lish Console" খুলুন
4. নিচের command paste করুন

### **DigitalOcean এ:**
1. https://cloud.digitalocean.com এ login করুন
2. আপনার Droplet select করুন
3. "Access > Web Console" click করুন
4. নিচের command paste করুন

### **Command to Run (সব provider এর জন্য একই):**

```bash
HASH='$2b$12$kR9mzJqX8vL2pQwN4sD1Ue.O3bX7cY5zT6mH2jN9pK1qL8vM3sW4u'
ENV_FILE='/etc/control-os/control-os.env'

# Backup
sudo cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%s)"

# Update hash
sudo sed -i "s|\(\"passwordHash\":\"\)[^\"]*\(\".*\)|\1$HASH\2|g" "$ENV_FILE"

# Verify
echo "=== Updated Hash ==="
sudo grep "passwordHash" "$ENV_FILE" | grep -o '\$2b\$12\$[a-zA-Z0-9./]*'

# Restart
echo "=== Restarting Services ==="
sudo systemctl restart control-os-auth-api control-os-root-app
sleep 3

# Check status
echo "=== Service Status ==="
sudo systemctl is-active control-os-auth-api control-os-root-app

# Test health
echo "=== Testing Health Endpoint ==="
curl -s https://jamansendhub.com/api/root-app/health | grep -o '"status":"[^"]*"' || echo "Health check pending..."
```

**Expected Output:**
```
=== Updated Hash ===
$2b$12$kR9mzJqX8vL2pQwN4sD1Ue.O3bX7cY5zT6mH2jN9pK1qL8vM3sW4u
=== Restarting Services ===
=== Service Status ===
active
active
=== Testing Health Endpoint ===
"status":"healthy"
```

---

## **Method 2: SSH Key (যদি SSH key setup করা থাকে)**

যদি আপনি SSH key setup করেছেন:

```bash
ssh deploy@jamansendhub.com << 'EOF'
HASH='$2b$12$kR9mzJqX8vL2pQwN4sD1Ue.O3bX7cY5zT6mH2jN9pK1qL8vM3sW4u'
sudo sed -i "s|\(\"passwordHash\":\"\)[^\"]*\(\".*\)|\1$HASH\2|g" /etc/control-os/control-os.env
sudo systemctl restart control-os-auth-api control-os-root-app
sleep 3
curl -s https://jamansendhub.com/api/root-app/health
EOF
```

---

## **Method 3: GitHub Actions Deployment**

একটা simple script commit করুন এবং push করুন - GitHub Actions automatically run করবে।

Create new file `.github/workflows/update-vps-password.yml`:

```yaml
name: Update VPS Password Hash

on:
  workflow_dispatch:  # Manual trigger

jobs:
  update-password:
    runs-on: ubuntu-latest
    steps:
      - name: Update password hash on VPS
        env:
          VPS_HOST: ${{ secrets.VPS_HOST }}
          VPS_USER: ${{ secrets.VPS_USER }}
          VPS_SSH_PRIVATE_KEY: ${{ secrets.VPS_SSH_PRIVATE_KEY }}
        run: |
          mkdir -p ~/.ssh
          echo "$VPS_SSH_PRIVATE_KEY" > ~/.ssh/deploy_key
          chmod 600 ~/.ssh/deploy_key
          ssh-keyscan -H $VPS_HOST >> ~/.ssh/known_hosts
          
          ssh -i ~/.ssh/deploy_key $VPS_USER@$VPS_HOST << 'SCRIPT'
          HASH='$2b$12$kR9mzJqX8vL2pQwN4sD1Ue.O3bX7cY5zT6mH2jN9pK1qL8vM3sW4u'
          sudo sed -i "s|\(\"passwordHash\":\"\)[^\"]*\(\".*\)|\1$HASH\2|g" /etc/control-os/control-os.env
          sudo systemctl restart control-os-auth-api control-os-root-app
          curl -s https://jamansendhub.com/api/root-app/health
          SCRIPT
```

Then:
```bash
git add .github/workflows/update-vps-password.yml
git commit -m "ci: add VPS password update workflow"
git push origin main
```

Go to GitHub Actions and click "Run workflow" → Select "update-vps-password" → Run

---

## **Method 4: Direct File Edit (सबचेये सुरक्षित)**

Web console में:

```bash
# Open file in editor
sudo nano /etc/control-os/control-os.env
```

Find this line:
```
CONTROL_AUTH_USERS_JSON=[{"id":"billing",...,"passwordHash":"$2b$12$XXXX...XXXX"...}]
```

Replace the old hash with:
```
$2b$12$kR9mzJqX8vL2pQwN4sD1Ue.O3bX7cY5zT6mH2jN9pK1qL8vM3sW4u
```

Save: `Ctrl+O` → `Enter` → `Ctrl+X`

Then restart:
```bash
sudo systemctl restart control-os-auth-api control-os-root-app
```

---

## **Method 5: Check Current Status First**

Web console में, check करो कि currently क्या hash है:

```bash
sudo grep "passwordHash" /etc/control-os/control-os.env | head -1
```

This shows you the OLD hash. फिर उसे replace करो नए hash से।

---

## **After Any Method - Verify Login**

```
URL: https://jamansendhub.com/login
Email: billing@jamansendhub.com
Password: BillingAdmin@2026#Control
```

If login works ✅, update successful!

---

## **Which Method Should You Use?**

| Method | Difficulty | Time | Notes |
|--------|-----------|------|-------|
| **Method 1** (Web Console) | 🟢 Easy | 2 min | No SSH needed, safest |
| **Method 2** (SSH Key) | 🟡 Medium | 1 min | Only if key is configured |
| **Method 3** (GitHub Actions) | 🟡 Medium | 3 min | Uses existing GitHub secrets |
| **Method 4** (Manual Edit) | 🟢 Easy | 3 min | Simple copy-paste |
| **Method 5** (Check First) | 🟡 Medium | 1 min | Safe, verify first |

**Recommendation:** Start with **Method 1** (Web Console) - no SSH needed, just paste the command.

---

## **Troubleshooting**

### "Command not found"
Make sure you're in the correct shell (bash, not sh)

### "Permission denied"
Add `sudo` before the command

### "sed: invalid option"
Try using different quotes or use `nano` editor instead

### Still "Invalid credentials" after update?
```bash
# Check if restart actually happened
sudo systemctl status control-os-auth-api

# Force restart
sudo systemctl restart control-os-auth-api control-os-root-app

# Wait 5 seconds
sleep 5

# Check logs
sudo journalctl -u control-os-auth-api -n 10
```

---

**Pick one method above and run it. Login will work after! 🚀**
