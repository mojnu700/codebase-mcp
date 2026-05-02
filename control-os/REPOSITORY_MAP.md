# Control OS - Repository Structure Map

## 📍 Project Overview

**Project:** Control OS - Enterprise Operations Control Platform  
**Type:** Full-stack TypeScript + Node.js microservices  
**Production URL:** https://jamansendhub.com  
**Admin Email:** billing@jamansendhub.com  
**Status:** Live & Deployed ✅

---

## 🗂️ Directory Structure

```
control-os-live/
│
├── 📁 .github/
│   └── workflows/
│       ├── auto-deploy-vps.yml          ← MAIN: Deploys to production on git push
│       ├── copilot-*.yml                ← CI/CD workflows
│       └── production-gate.yml           ← Production validation checks
│
├── 📁 src/                              ← FRONTEND (React + TypeScript + Vite)
│   ├── app/
│   │   ├── providers/                   ← Auth provider, theme, state
│   │   └── store/                       ← Global state management
│   ├── components/                      ← Reusable UI components
│   ├── features/                        ← Feature modules
│   │   ├── root-app/                    ← Dashboard, projects, runs
│   │   ├── sending/                     ← Email campaigns
│   │   ├── cloud-browser/               ← Browser automation
│   │   └── workspace/                   ← Collaboration
│   ├── modules/                         ← Module registry & definitions
│   ├── pages/                           ← Page routes
│   │   ├── auth/                        ← Login page
│   │   ├── root-surfaces/               ← Main dashboard routes
│   │   ├── worker-signup/               ← Worker registration
│   │   └── ...
│   ├── lib/                             ← Utilities
│   │   ├── auth-runtime.ts              ← Auth mode detection (local/external)
│   │   ├── api-client.ts                ← Fetch + auth headers
│   │   ├── endpoints.ts                 ← API endpoint constants
│   │   └── permissions.ts               ← RBAC rules
│   └── styles/                          ← Global CSS
│
├── 📁 server/                           ← BACKEND (Node.js APIs)
│   ├── auth-api/
│   │   └── server.mjs                   ← Login, token generation, auth endpoint
│   ├── root-app-api/
│   │   └── server.mjs                   ← Main dashboard API (projects, runs, audit)
│   ├── sending-api/
│   │   └── server.mjs                   ← Email sending service
│   ├── cloud-browser-api/
│   │   └── server.mjs                   ← Browser automation API
│   ├── google-accounts-api/
│   │   └── server.mjs                   ← Gmail/Google integration
│   ├── workspace-api/
│   │   └── server.mjs                   ← Workspace collaboration API
│   ├── task-manager-api/
│   │   └── server.mjs                   ← Task management API
│   ├── session-api/
│   │   └── server.mjs                   ← Session management API
│   ├── batch-workspace-api/
│   │   └── server.mjs                   ← Batch operations API
│   └── shared/
│       ├── auth.mjs                     ← CRITICAL: Password hashing (bcrypt/scrypt)
│       ├── logger.mjs                   ← Logging utilities
│       └── helpers.mjs                  ← Shared utilities
│
├── 📁 deploy/
│   ├── production/env/
│   │   ├── control-os.generated.env     ← EXAMPLE env (on repo)
│   │   ├── control-os.production.env.example
│   │   └── README                       ← Env configuration docs
│   └── systemd/                         ← Systemd unit files (on VPS)
│
├── 📁 scripts/
│   ├── dev/
│   │   └── dev-all.mjs                  ← LOCAL DEV: Starts all services locally
│   ├── smoke/                           ← Integration test scripts
│   ├── e2e/                             ← End-to-end tests
│   └── helpers.mjs                      ← Test utilities
│
├── 📁 docs/
│   ├── DEVELOPER_QUICKSTART.md           ← Getting started locally
│   ├── ARCHITECTURE.md                   ← System design
│   └── API_DOCS.md                       ← API reference
│
├── 📁 .continue/                        ← Continue IDE config
├── 📁 .vscode/                          ← VS Code settings
├── 📁 node_modules/                     ← Dependencies (npm install)
│
├── 📄 package.json                      ← Dependencies & scripts
├── 📄 package-lock.json                 ← Dependency lock file
├── 📄 tsconfig.json                     ← TypeScript configuration
├── 📄 vite.config.ts                    ← Vite bundler config
├── 📄 eslint.config.mjs                 ← Linting rules
├── 📄 README.md                         ← Project overview
├── 📄 LOCAL_RUN.md                      ← Local development guide
├── 📄 VPS_PASSWORD_RESET_GUIDE.md      ← Password management (YOU ARE HERE)
└── 📄 .gitignore                        ← Git ignore rules

```

---

## 🔑 Key Files Explained

### **Frontend Entry Points**
- `src/main.tsx` — React app bootstrap
- `index.html` — HTML template
- `src/app/App.tsx` — Root component with routing

### **Backend Entry Points**
- `server/*/server.mjs` — Each service has its own HTTP server
- `server/shared/auth.mjs` — Centralized authentication logic

### **Configuration Files**
- `package.json` — npm scripts: `npm run dev`, `npm run build`
- `tsconfig.json` — TypeScript compiler options
- `vite.config.ts` — Frontend bundler settings
- `.github/workflows/auto-deploy-vps.yml` — Production deployment automation

### **Environment Files**
```
Repo (GitHub):
  └── deploy/production/env/control-os.generated.env  ← Example ONLY

VPS Server (Production):
  └── /etc/control-os/control-os.env                  ← REAL secrets
```

---

## 🔄 Data Flow Architecture

```
Browser (React App)
    ↓ HTTPS
Login Page (src/pages/auth/login-page.tsx)
    ↓
POST /api/auth/login
    ↓
auth-api/server.mjs (Port 8779)
    ├─ Validates credentials against CONTROL_AUTH_USERS_JSON
    ├─ Generates JWT token (HS256)
    └─ Returns token + refresh cookie
    ↓
Token stored in:
  ├─ Memory (access token - 15 min)
  └─ Secure HttpOnly Cookie (refresh token - 7 days)
    ↓
Subsequent API calls:
    ├─ Authorization: Bearer {token}
    └─ Credentials: include (sends cookies)
    ↓
root-app-api/server.mjs (Port 8792)
    ├─ Verifies JWT signature
    ├─ Extracts actor (user ID, role)
    ├─ Authorizes based on RBAC
    └─ Returns data (projects, runs, etc.)
    ↓
UI updates with data
```

---

## 🔐 Authentication Flow

```
1. User enters credentials at https://jamansendhub.com/login
   ↓
2. Frontend calls POST /api/auth/login
   {
     "email": "billing@jamansendhub.com",
     "password": "actual-password"
   }
   ↓
3. auth-api receives request
   ├─ Looks up user in CONTROL_AUTH_USERS_JSON
   ├─ Compares password against bcrypt hash using bcrypt.compare()
   └─ If match → generates JWT token
   ↓
4. Token sent to browser
   ├─ Access token: stored in memory (15 min TTL)
   ├─ Refresh token: stored in secure cookie (7 days)
   ↓
5. Browser includes token in Authorization header
   Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
   ↓
6. API servers verify token
   ├─ Check signature against CONTROL_AUTH_TOKEN_SECRET
   ├─ Validate issuer/audience
   ├─ Check expiration
   └─ Extract actor claims (user ID, role, permissions)
   ↓
7. If valid → Process request
   If invalid → Return 401 Unauthorized
```

---

## 📦 Service Ports (Local Dev)

```
Frontend (Vite):      http://127.0.0.1:5173
auth-api:             http://127.0.0.1:8779
root-app-api:         http://127.0.0.1:8792
cloud-browser-api:    http://127.0.0.1:8787
sending-api:          http://127.0.0.1:8788
google-accounts-api:  http://127.0.0.1:8789
calendar-invite-api:  http://127.0.0.1:8790
batch-workspace-api:  http://127.0.0.1:8793
workspace-api:        http://127.0.0.1:8794
session-api:          http://127.0.0.1:8795
task-manager-api:     http://127.0.0.1:8796
```

---

## 🚀 Deployment Pipeline

```
1. Developer pushes to main branch
   ↓
2. GitHub Actions triggered by auto-deploy-vps.yml
   ├─ Event: push to main
   └─ Conditions: Only on main branch
   ↓
3. Runner checks out code
   ├─ git clone https://github.com/mojnu700/control-os-live.git
   ├─ git checkout main
   └─ git pull latest changes
   ↓
4. SSH into VPS and execute deployment
   ├─ Load env from: /etc/control-os/control-os.env
   ├─ Run: npm ci (clean install)
   ├─ Run: npm run build (TypeScript → JavaScript)
   ├─ Deploy to: /opt/control-os/releases/{timestamp}/
   ├─ Update symlink: /opt/control-os/current → new release
   ↓
5. Health check
   ├─ GET /api/root-app/health
   ├─ Retry 3x with backoff
   ├─ Timeout: 60 seconds
   ↓
6. Systemd restart
   ├─ systemctl restart control-os-root-app
   ├─ systemctl restart control-os-auth-api
   ├─ systemctl restart all services
   ↓
7. Status update
   ├─ Success: Mark workflow as ✅
   ├─ Failure: Mark workflow as ❌ (send alert)
   ↓
8. Production live with new code
```

---

## 🔐 Secrets Management

### In GitHub (CI/CD)
```
VPS_HOST           → jamansendhub.com (or IP)
VPS_USER           → deploy user
VPS_SSH_PRIVATE_KEY → SSH key for deployment
```

### On VPS (Production)
```
/etc/control-os/control-os.env (manually maintained)
├─ CONTROL_AUTH_MODE=token
├─ CONTROL_AUTH_TOKEN_SECRET=b191c1e1...
├─ CONTROL_AUTH_USERS_JSON=[{"id":"billing",...,"passwordHash":"$2b$12$..."}]
├─ CONTROL_SECRET_MASTER_KEY=5b488e90...
└─ VITE_AUTH_MODE=external
```

**NEVER:**
- ❌ Commit passwords to GitHub
- ❌ Commit `.env` files
- ❌ Share private keys in chat
- ❌ Use dev credentials in production

---

## 📊 API Endpoints Summary

```
POST   /api/auth/login              → Generate token
POST   /api/auth/refresh            → Refresh token
POST   /api/auth/logout             → Logout

GET    /api/root-app/health         → Health check
GET    /api/projects                → List projects
POST   /api/projects                → Create project
GET    /api/projects/:id/runs       → List runs
POST   /api/projects/:id/runs       → Create run

GET    /api/sending/health          → Sending API health
POST   /api/sending/campaigns       → Email campaigns

GET    /api/cloud-browser/health    → Browser API health
POST   /api/cloud-browser/sessions  → Browser sessions

GET    /api/workspace/health        → Workspace API health
POST   /api/workspace/items         → Workspace items

... (more endpoints)
```

---

## ✅ Production Checklist

Before going live:

- [ ] Password reset on VPS (See: VPS_PASSWORD_RESET_GUIDE.md)
- [ ] Services restarted successfully
- [ ] Health endpoint returns correct auth mode
- [ ] Login works with billing@jamansendhub.com
- [ ] All APIs responding 200 OK
- [ ] No errors in systemd logs
- [ ] DNS resolves jamansendhub.com
- [ ] HTTPS certificate valid
- [ ] Backups configured
- [ ] Monitoring alerts set up

---

## 📞 Common Operations

### View Logs
```bash
sudo journalctl -u control-os-root-app -f
sudo journalctl -u control-os-auth-api -f
```

### Restart Services
```bash
sudo systemctl restart control-os-root-app
sudo systemctl restart control-os-auth-api
```

### Check Service Status
```bash
sudo systemctl status control-os-root-app
sudo systemctl status control-os-auth-api
```

### View Environment
```bash
sudo cat /etc/control-os/control-os.env
```

### Test Health
```bash
curl https://jamansendhub.com/api/root-app/health
```

---

**Status:** Production deployed and running ✅  
**Admin Email:** billing@jamansendhub.com  
**Password:** Needs to be set on VPS (See VPS_PASSWORD_RESET_GUIDE.md)

Last Updated: April 25, 2026
