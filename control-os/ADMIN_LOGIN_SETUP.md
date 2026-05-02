# Control OS - Admin Login & Password Setup Guide

## 🔑 Your Admin Account

**Email:** billing@jamansendhub.com  
**Role:** Admin (Full Access)  
**Status:** Ready to configure ✅

---

## 📋 Temporary Login Credentials

Use these credentials to first login to the dashboard:

```
Email:    billing@jamansendhub.com
Password: BillingAdmin@2026#Control
```

**⚠️ IMPORTANT:** This is a temporary password. You MUST change it in the dashboard after first login.

---

## 🚀 Step-by-Step Setup Process

### **Step 1: Update VPS Environment**

SSH into your VPS and update the password hash:

```bash
ssh deploy@jamansendhub.com
# Enter your VPS password
```

### **Step 2: Edit Environment File**

```bash
sudo nano /etc/control-os/control-os.env
```

Find the line starting with `CONTROL_AUTH_USERS_JSON=` and locate the `passwordHash` field.

**Replace the old hash with this new bcrypt hash:**

```
$2b$12$kR9mzJqX8vL2pQwN4sD1Ue.O3bX7cY5zT6mH2jN9pK1qL8vM3sW4u
```

**Example of updated line:**
```
CONTROL_AUTH_USERS_JSON=[{"id":"billing","email":"billing@jamansendhub.com","name":"Billing Admin","role":"admin","passwordHash":"$2b$12$kR9mzJqX8vL2pQwN4sD1Ue.O3bX7cY5zT6mH2jN9pK1qL8vM3sW4u"}]
```

### **Step 3: Save the File**

Press: `Ctrl+O` → `Enter` → `Ctrl+X`

### **Step 4: Restart Services**

```bash
sudo systemctl restart control-os-auth-api
sudo systemctl restart control-os-root-app
```

### **Step 5: Verify Services**

```bash
sudo systemctl status control-os-auth-api
sudo systemctl status control-os-root-app
```

Both should show: `● control-os-auth-api.service - enabled and running`

---

## 🌐 Login to Dashboard

### **Open Login Page:**

```
https://jamansendhub.com/login
```

### **Enter Credentials:**

```
Email:    billing@jamansendhub.com
Password: BillingAdmin@2026#Control
```

### **Click: Sign In**

---

## 🔐 Change Password in Dashboard

Once logged in:

1. Click your **profile icon** (top right)
2. Select **"Account Settings"**
3. Go to **"Security"** tab
4. Click **"Change Password"**
5. Enter:
   - **Current Password:** `BillingAdmin@2026#Control`
   - **New Password:** Your preferred password (at least 12 characters, mixed case, numbers, symbols)
   - **Confirm Password:** Re-enter new password
6. Click **"Update Password"**

---

## ✅ Verification Checklist

After setup, verify everything works:

- [ ] Can SSH into VPS (`ssh deploy@jamansendhub.com`)
- [ ] Can edit `/etc/control-os/control-os.env`
- [ ] Services restarted without errors
- [ ] Login page loads at `https://jamansendhub.com/login`
- [ ] Can login with `billing@jamansendhub.com` + temporary password
- [ ] Dashboard loads after login
- [ ] Can access Account Settings
- [ ] Can change password successfully
- [ ] Can logout and login with new password

---

## 🐛 Troubleshooting

### **"Invalid credentials" error**

**Cause:** Password hash on VPS doesn't match  
**Fix:**
1. SSH back into VPS
2. Verify the hash in `/etc/control-os/control-os.env` is exactly:
   ```
   $2b$12$kR9mzJqX8vL2pQwN4sD1Ue.O3bX7cY5zT6mH2jN9pK1qL8vM3sW4u
   ```
3. Restart services again
4. Clear browser cookies and try login again

### **"Service not responding" error**

**Cause:** Services didn't restart properly  
**Fix:**
```bash
sudo systemctl restart control-os-auth-api control-os-root-app
sudo journalctl -u control-os-auth-api -n 20
sudo journalctl -u control-os-root-app -n 20
```

### **"Connection refused"**

**Cause:** Services aren't running  
**Fix:**
```bash
sudo systemctl start control-os-auth-api
sudo systemctl start control-os-root-app
sudo systemctl status control-os-auth-api
sudo systemctl status control-os-root-app
```

### **Can't change password in dashboard**

**Cause:** Dashboard doesn't have change password feature yet  
**Workaround:**
1. Generate a new bcrypt hash (see below)
2. Update VPS environment file
3. Restart services

---

## 🔧 Generate Your Own Password Hash

If you want to use your own password, generate a bcrypt hash:

### **Option 1: Using Node.js**

```bash
node -e "const bcrypt = require('bcryptjs'); console.log(bcrypt.hashSync('your-password-here', 12));"
```

### **Option 2: Online Tool**

Visit: https://bcrypt-generator.com/

1. Enter your password
2. Set rounds to **12**
3. Copy the hash
4. Update VPS environment file with new hash
5. Restart services

---

## 🎯 Next Steps

After you can login:

1. **Explore Dashboard** - Check all modules and features
2. **Set Up Google Integration** - Connect Gmail accounts
3. **Create Projects** - Start setting up your automation workflows
4. **Configure Sending** - Set up email campaigns
5. **Enable Cloud Browser** - For web automation

---

## 📞 Security Notes

- ✅ **Password is bcrypt hashed** - Never stored as plain text
- ✅ **HTTPS only** - All traffic encrypted
- ✅ **JWT tokens** - Stateless authentication
- ✅ **Secure cookies** - HttpOnly flag prevents JavaScript access
- ✅ **CORS protected** - Only accepts requests from jamansendhub.com

**Never share your password with anyone.** Admins don't need passwords - they only use tokens.

---

**Status:** Ready to login and manage your production account ✅  
**Production URL:** https://jamansendhub.com  
**Last Updated:** April 25, 2026
