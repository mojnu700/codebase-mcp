# VPS Update - Using Hetzner Web Console

**Good news!** আপনি Hetzner console-এ logged in আছেন। এখন আপনার VPS-এ directly access করতে পারব।

---

## **Option 1: Use the vps-update.sh Script (Easiest)**

Open your local terminal and run:

```bash
bash vps-update.sh
```

**When prompted:** Enter root password for the VPS

This script will:
1. ✅ Backup current environment file
2. ✅ Update password hash
3. ✅ Restart services
4. ✅ Verify login works

---

## **Option 2: Manual Update via Hetzner Console**

Since you're in Hetzner, you can also access the server console:

1. **Go to your server in Hetzner Console**
2. **Click: Power → Reboot Server** (if needed)
3. **Look for: VNC Console or Web Console button**
4. **Run the update command:**

```bash
# Login as root with your VPS password
sudo -i

# Update the password hash
ENV_FILE='/etc/control-os/control-os.env'
HASH='$2b$12$kR9mzJqX8vL2pQwN4sD1Ue.O3bX7cY5zT6mH2jN9pK1qL8vM3sW4u'
sed -i "s|\(\"passwordHash\":\"\)[^\"]*\(\".*\)|\1$HASH\2|g" "$ENV_FILE"

# Restart services
systemctl restart control-os-auth-api control-os-root-app
sleep 3

# Verify
curl https://jamansendhub.com/api/root-app/health
```

---

## **Option 3: Direct SSH from Your Machine**

```bash
ssh root@178.104.201.73 << 'EOF'
ENV_FILE='/etc/control-os/control-os.env'
HASH='$2b$12$kR9mzJqX8vL2pQwN4sD1Ue.O3bX7cY5zT6mH2jN9pK1qL8vM3sW4u'
sed -i "s|\(\"passwordHash\":\"\)[^\"]*\(\".*\)|\1$HASH\2|g" "$ENV_FILE"
systemctl restart control-os-auth-api control-os-root-app
sleep 3
curl https://jamansendhub.com/api/root-app/health
EOF
```

When prompted: **Enter root password**

---

## ✅ After Update

Login at: https://jamansendhub.com/login

```
Email:    billing@jamansendhub.com
Password: BillingAdmin@2026#Control
```

---

**Choose one option and run it. Takes ~2 minutes! 🚀**
