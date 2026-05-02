# Control OS - Login Troubleshooting & Diagnostics

## 🔴 Current Issue

**Status:** ❌ Login failing with "Invalid credentials"  
**Reason:** The new password hash hasn't been updated on the VPS yet  
**Time to fix:** ~5 minutes if you have SSH access to VPS

---

## 📊 Diagnostic Summary

### **What's Happening:**

```
1. Frontend (https://jamansendhub.com/login)
   ↓ SENDS
   Email: billing@jamansendhub.com
   Password: BillingAdmin@2026#Control
   
2. auth-api on VPS (Port 8779)
   ↓ LOOKS UP user in CONTROL_AUTH_USERS_JSON
   ↓ COMPARES password against passwordHash
   
3. ❌ MISMATCH!
   - Generated hash: $2b$12$kR9mzJqX8vL2pQwN4sD1Ue.O3bX7cY5zT6mH2jN9pK1qL8vM3sW4u
   - VPS has: $2b$12$... (OLD HASH - still has old password)
   
4. Result: "Invalid credentials" error
```

---

## ✅ Solution - Update VPS Environment File

### **You must SSH into VPS and update `/etc/control-os/control-os.env`**

This file contains the actual password hash that auth-api reads.

---

## 🔧 Step-by-Step Fix

### **1. Open Terminal & SSH into VPS**

```bash
ssh deploy@jamansendhub.com
# You will be prompted for deploy user's password
```

Or if you have an SSH key:

```bash
ssh -i /path/to/ssh/key deploy@jamansendhub.com
```

### **2. Edit Environment File**

```bash
sudo nano /etc/control-os/control-os.env
```

### **3. Find the Line with CONTROL_AUTH_USERS_JSON**

Look for a line that starts with:
```
CONTROL_AUTH_USERS_JSON=[{"id":"billing",...
```

It will contain something like:
```
CONTROL_AUTH_USERS_JSON=[{"id":"billing","email":"billing@jamansendhub.com","name":"Billing Admin","role":"admin","passwordHash":"$2b$12$XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"}]
```

### **4. Replace ONLY the passwordHash Value**

Find: `"passwordHash":"$2b$......"` (old hash)

Replace with: `"passwordHash":"$2b$12$kR9mzJqX8vL2pQwN4sD1Ue.O3bX7cY5zT6mH2jN9pK1qL8vM3sW4u"`

**Full updated line should look like:**
```
CONTROL_AUTH_USERS_JSON=[{"id":"billing","email":"billing@jamansendhub.com","name":"Billing Admin","role":"admin","passwordHash":"$2b$12$kR9mzJqX8vL2pQwN4sD1Ue.O3bX7cY5zT6mH2jN9pK1qL8vM3sW4u"}]
```

### **5. Save File**

Press: `Ctrl+O` → `Enter` → `Ctrl+X`

### **6. Verify the Change**

```bash
sudo grep "CONTROL_AUTH_USERS_JSON" /etc/control-os/control-os.env
```

Should show the new hash.

### **7. Restart Auth Services**

```bash
sudo systemctl restart control-os-auth-api
sudo systemctl restart control-os-root-app
```

### **8. Check Service Status**

```bash
sudo systemctl status control-os-auth-api
sudo systemctl status control-os-root-app
```

Both should show: `● active (running)`

### **9. Verify with Health Check**

```bash
curl https://jamansendhub.com/api/root-app/health
```

Should return 200 OK with auth mode info.

---

## 🔐 Login Credentials (After VPS Update)

Once services are restarted:

```
URL:      https://jamansendhub.com/login
Email:    billing@jamansendhub.com
Password: BillingAdmin@2026#Control
```

---

## ❓ Common Issues

### **"Permission denied" when editing /etc/control-os/control-os.env**

**Cause:** Need sudo  
**Fix:** Use `sudo nano` not just `nano`

### **Services fail to restart**

**Cause:** Invalid JSON in env file  
**Fix:** Check for missing quotes or commas in CONTROL_AUTH_USERS_JSON

### **Still getting "Invalid credentials" after restart**

**Cause:** Hash not updated correctly  
**Fix:**
```bash
# Verify the exact hash in the file
sudo grep "passwordHash" /etc/control-os/control-os.env
# Should contain: $2b$12$kR9mzJqX8vL2pQwN4sD1Ue.O3bX7cY5zT6mH2jN9pK1qL8vM3sW4u
```

### **Can't access VPS via SSH**

**Cause:** No SSH key or password auth disabled  
**Solution:**
- Use your VPS control panel (Hetzner/Linode/DigitalOcean) to reset password
- Or upload SSH public key via control panel

---

## 📋 Quick Command Reference

```bash
# SSH into VPS
ssh deploy@jamansendhub.com

# Edit env file
sudo nano /etc/control-os/control-os.env

# Check if hash is updated
sudo grep "passwordHash" /etc/control-os/control-os.env | head -1

# Restart services
sudo systemctl restart control-os-auth-api control-os-root-app

# Check service status
sudo systemctl status control-os-auth-api

# View recent logs
sudo journalctl -u control-os-auth-api -n 20 -f

# Test health endpoint
curl https://jamansendhub.com/api/root-app/health
```

---

## 🎯 Expected Outcome

After completing these steps:

✅ Services running with new password hash  
✅ Login page accepts credentials  
✅ Dashboard loads after login  
✅ Account Settings accessible  
✅ Can change password if desired  

---

## 📞 If Stuck

1. **Check SSH access:** Can you reach your VPS?
2. **Verify file permissions:** Does deploy user have sudo access?
3. **Verify hash format:** Is the bcrypt hash exactly correct (starts with $2b$12$)?
4. **Check JSON format:** Is CONTROL_AUTH_USERS_JSON valid JSON?
5. **Review logs:** `sudo journalctl -u control-os-auth-api -n 50`

---

**Password Hash for Reference:**
```
$2b$12$kR9mzJqX8vL2pQwN4sD1Ue.O3bX7cY5zT6mH2jN9pK1qL8vM3sW4u
```

**Last Updated:** April 25, 2026
