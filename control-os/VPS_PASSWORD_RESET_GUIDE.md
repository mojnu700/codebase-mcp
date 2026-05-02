# VPS Password Reset Guide - billing@jamansendhub.com

## 📋 Current Status

**Production URL:** https://jamansendhub.com  
**Admin Email:** billing@jamansendhub.com  
**Password Hash:** Currently in bcrypt format (encrypted, cannot be reversed)  
**Issue:** Password needs to be reset with actual secure password before production use

---

## 🔐 Step 1: Generate New Bcrypt Password Hash

### Option A: Using Node.js (Recommended)

1. SSH into your VPS:
```bash
ssh user@your-vps-ip
```

2. Generate a secure bcrypt hash:
```bash
node -e "const bcrypt = require('bcrypt'); const pwd = process.argv[1]; bcrypt.hash(pwd, 12, (err, hash) => { if(err) throw err; console.log(hash); });" "YOUR_SECURE_PASSWORD_HERE"
```

Replace `YOUR_SECURE_PASSWORD_HERE` with your actual strong password.

**Example:**
```bash
node -e "const bcrypt = require('bcrypt'); const pwd = process.argv[1]; bcrypt.hash(pwd, 12, (err, hash) => { if(err) throw err; console.log(hash); });" "MySecureP@ssw0rd2026!"
```

**Output:** You'll get a hash like:
```
$2b$12$abc123def456...xyz789
```

### Option B: Using Online Tool (Less Secure - Only for Testing)
Visit: https://bcrypt-generator.com/
- Enter your password
- Click "Hash"
- Copy the generated hash

---

## 🔧 Step 2: Update VPS Environment File

SSH into VPS and edit the production environment:

```bash
# Connect to VPS
ssh user@your-vps-ip

# Edit production environment
sudo nano /etc/control-os/control-os.env
```

**Find this line:**
```
CONTROL_AUTH_USERS_JSON=[{"id":"billing","email":"billing@jamansendhub.com","name":"Billing Admin","role":"admin","passwordHash":"$2b$12$R9h7cIPxPgSJlUzyWIitem5XWO5o5o5o5PkLm8vBvBPk0k1k1K1K1"}]
```

**Replace the passwordHash value with your new hash:**
```
CONTROL_AUTH_USERS_JSON=[{"id":"billing","email":"billing@jamansendhub.com","name":"Billing Admin","role":"admin","passwordHash":"$2b$12$YOUR_NEW_HASH_HERE"}]
```

**Save the file:**
- Press `Ctrl+X`
- Press `Y` (yes)
- Press `Enter`

---

## 🔄 Step 3: Restart Services

After updating the environment file, restart the auth service:

```bash
# Restart root app API
sudo systemctl restart control-os-root-app

# Restart auth API
sudo systemctl restart control-os-auth-api

# Optional: Check service status
sudo systemctl status control-os-root-app
sudo systemctl status control-os-auth-api
```

**Wait 10-15 seconds for services to fully restart.**

---

## ✅ Step 4: Verify Login

Test the new credentials:

1. **Open browser:** https://jamansendhub.com
2. **Click:** "Sign In"
3. **Enter:**
   - Email: `billing@jamansendhub.com`
   - Password: `YOUR_SECURE_PASSWORD_HERE` (the actual password you used in Step 1)
4. **Expected Result:** ✅ Successful login to admin panel

---

## 🐛 Troubleshooting

### "Login Failed" Error
- **Check:** Password hash was copied completely (no missing characters)
- **Check:** Environment file syntax is valid JSON
- **Check:** Services restarted successfully
- **Fix:** Review logs:
  ```bash
  sudo journalctl -u control-os-auth-api -n 50
  ```

### "Connection Refused"
- **Check:** Services are running:
  ```bash
  sudo systemctl status control-os-root-app
  sudo systemctl status control-os-auth-api
  ```
- **Fix:** Restart both services
  ```bash
  sudo systemctl restart control-os-root-app control-os-auth-api
  ```

### "authMode: dev_local" in Health Endpoint
- **Issue:** Old environment not loaded
- **Fix:** 
  1. Confirm changes saved in `/etc/control-os/control-os.env`
  2. Restart services again
  3. Wait 15 seconds
  4. Check health: `curl https://jamansendhub.com/api/root-app/health`

---

## 📊 Repository Configuration

The password hash is stored **ONLY on VPS**, not in GitHub:

- ✅ `/etc/control-os/control-os.env` — VPS-managed (production passwords)
- ❌ `deploy/production/env/control-os.generated.env` — Example only (in repo)

This separation keeps production credentials safe.

---

## 🔒 Security Best Practices

1. **Strong Password Required:**
   - ✅ 12+ characters
   - ✅ Mix of uppercase, lowercase, numbers, symbols
   - ✅ Example: `MyBilling@Admin2026!`

2. **Never Commit Passwords:**
   - ✅ Keep actual passwords on VPS only
   - ❌ Don't add to GitHub repository

3. **Rotate Regularly:**
   - Recommend: Every 90 days
   - Process: Same as this guide, new password → new hash → update VPS → restart

4. **Access Control:**
   - Restrict VPS SSH access to authorized users only
   - Use SSH keys, not passwords for VPS login

---

## 📞 Support

If you encounter issues:
1. Check service logs: `sudo journalctl -u control-os-auth-api`
2. Verify environment file: `sudo cat /etc/control-os/control-os.env`
3. Test health endpoint: `curl https://jamansendhub.com/api/root-app/health`

---

**Status:** Production is ready to accept traffic once password is reset on VPS.  
**Timeline:** ~5-10 minutes to complete this guide.

Last Updated: April 25, 2026
