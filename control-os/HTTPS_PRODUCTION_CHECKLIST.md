# HTTPS Production Checklist — Control OS

This document captures every step that **must** be completed before deploying Control OS
to a real HTTPS production environment.  
Work through each section top-to-bottom. Check every box before going live.

---

## 1. TLS / HTTPS Infrastructure

- [ ] Obtain a valid TLS certificate from a trusted CA (Let's Encrypt, DigiCert, etc.)
- [ ] Configure your reverse proxy (nginx, Caddy, AWS ALB, etc.) to terminate TLS on port 443
- [ ] Redirect all HTTP (port 80) traffic to HTTPS with a permanent 301
- [ ] Set proxy to forward `X-Forwarded-Proto: https` to backend services
- [ ] Verify `X-Forwarded-Proto` is stripped from untrusted client requests at the proxy
- [ ] Enable HTTP/2 on the reverse proxy for better performance
- [ ] Set TLS minimum version to TLS 1.2 (prefer TLS 1.3 only)
- [ ] Configure strong cipher suites (disable RC4, 3DES, export ciphers)

---

## 2. HTTP Security Headers (now applied by all backends)

All six backend services now emit security headers on every response via
`applySecurityHeaders()` in `server/shared/http-security.mjs`:

| Header | Value |
|---|---|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` (set only on HTTPS) |
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |

- [ ] Verify `Strict-Transport-Security` appears in production responses (requires HTTPS)
- [ ] Verify `X-Content-Type-Options: nosniff` on all API responses
- [ ] Verify `X-Frame-Options: DENY` on all API responses
- [ ] Consider adding `Content-Security-Policy` at the reverse proxy / Vite build level
  for the frontend SPA (not required for API backends but strongly recommended for the UI)

---

## 3. Cookie Security

- [ ] Set `CONTROL_AUTH_REFRESH_COOKIE_SECURE=true` in production env  
  _(now the default in `.env.example`; auto-detected from `X-Forwarded-Proto` when unset)_
- [ ] Confirm `CONTROL_AUTH_REFRESH_COOKIE_SAMESITE` is set correctly:
  - `Strict` — best protection, blocks all cross-site sends
  - `Lax` — default; safe for most cases
  - `None` — only if cross-site cookies are intentionally needed (requires `Secure=true`)
- [ ] Confirm `HttpOnly` is set (it is hardcoded in `auth-api/server.mjs`)

---

## 4. CORS Configuration

- [ ] Replace all `http://127.0.0.1:*` origins in CORS env vars with your real `https://` origin:
  ```
  CONTROL_AUTH_CORS_ALLOWED_ORIGINS=https://app.example.com
  CONTROL_CORS_ALLOWED_ORIGINS=https://app.example.com
  ```
- [ ] Confirm no `*` wildcard origins are used in production (ADR-0002)
- [ ] Remove or explicitly disable `CONTROL_CORS_ALLOW_DEV_ORIGINS` in production

---

## 5. Authentication & Secrets

- [ ] Replace placeholder `CONTROL_AUTH_TOKEN_SECRET` with a cryptographically random value  
  _(minimum 32 bytes of entropy — generate with `node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"`)_
- [ ] Replace placeholder `CONTROL_SECRET_MASTER_KEY` with a cryptographically random value
- [ ] Set `CONTROL_AUTH_MODE=token` (must not be `dev_local` in production)
- [ ] Set `VITE_AUTH_MODE=external` (must not be `local` in production)
- [ ] Rotate secrets after any suspected exposure; revoke all existing sessions when doing so
- [ ] Do not commit real secrets to source control — use your deployment platform's secret manager
- [ ] Ensure `CONTROL_SECRET_ALLOW_PLAINTEXT_DEV` is **not** set in production
- [ ] Generate RS256 key pair for service JWTs (`CONTROL_SERVICE_JWT_PUBLIC_KEY_PEM` / `CONTROL_SERVICE_JWT_PRIVATE_KEY_PEM`)

---

## 6. Production API Mode (ADR-0001)

- [ ] Set all `VITE_*_API_MODE` variables to `real` or explicit `fake` — never `auto`:
  ```
  VITE_AUTH_MODE=external
  VITE_APP_API_MODE=real          # or fake under Module-live mixed posture
  VITE_CLOUD_BROWSER_API_MODE=real
  VITE_SENDING_API_MODE=real
  VITE_GOOGLE_ACCOUNTS_API_MODE=real
  VITE_CALENDAR_INVITE_API_MODE=real
  ```
- [ ] Run `npm run verify:prod-gate` and confirm it passes before every deployment

---

## 7. Backend API Base URLs

- [ ] Update all `VITE_*_API_BASE_URL` values from `http://127.0.0.1:*` to real `https://` URLs:
  ```
  VITE_AUTH_API_BASE_URL=https://auth.example.com
  VITE_CLOUD_BROWSER_API_BASE_URL=https://cloud-browser.example.com
  VITE_SENDING_API_BASE_URL=https://sending.example.com
  VITE_GOOGLE_ACCOUNTS_API_BASE_URL=https://google-accounts.example.com
  VITE_CALENDAR_INVITE_API_BASE_URL=https://calendar-invite.example.com
  ```
- [ ] Set the `GOOGLE_ACCOUNTS_API_BASE_URL` backend env var to the `https://` URL for all services that call the Google Accounts broker (sending-api, calendar-invite-api)

---

## 8. Rate Limiting & Abuse Protection

- [ ] If backends run behind a trusted reverse proxy, set `CONTROL_RATE_LIMIT_TRUST_PROXY=true`
  so that rate limiting keys on the real client IP rather than the proxy IP
- [ ] Review and tighten rate limit windows/maxima for your expected traffic:
  - `CONTROL_RATE_LIMIT_AUTH_LOGIN_MAX` (default: 10 / 60 s)
  - `CONTROL_RATE_LIMIT_AUTH_REFRESH_MAX` (default: 30 / 5 min)
  - `CONTROL_RATE_LIMIT_SENDING_DISPATCH_MAX` (default: 30 / 60 s)

---

## 9. Data & File Paths

- [ ] Set all `*_DATA_PATH` and `*_QUEUE_PATH` variables to absolute paths on a persistent volume
- [ ] Ensure the process user has write permission to those paths
- [ ] Schedule regular backups of all `.json` data files
- [ ] Do not use the default in-tree paths (`server/*-api/.*.json`) for production

---

## 10. Sending / Calendar Allowlists

- [ ] Set `SENDING_ALLOWED_RECIPIENT_DOMAINS` to your real allowlisted domains (not `example.com`)
- [ ] Set `CALENDAR_INVITE_ALLOWED_ATTENDEE_DOMAINS` to your real allowlisted domains
- [ ] Set `CALENDAR_INVITE_PUSH_WEBHOOK_ADDRESS` to the real HTTPS webhook URL
- [ ] Set a strong, random `CALENDAR_INVITE_PUSH_TOKEN_SECRET`
- [ ] Remove or disable `CALENDAR_INVITE_ALLOW_DEV_PUSH_TOKEN_FALLBACK` in production

---

## 11. Users & Access Control

- [ ] Populate `CONTROL_AUTH_USERS_JSON` with real user records (or integrate a real user store)
- [ ] Confirm that only users with `admin`/`manager`/`lead` roles can perform write operations
- [ ] Verify RBAC enforcement is active: the root-app-api applies `enforceWriteRbac()` on
  all POST/PATCH/DELETE routes before handler dispatch (Phase 0 deny-by-default)
- [ ] Rotate user passwords after initial setup

---

## 12. Automated Gates

- [ ] Run `npm run verify:prod-gate` — must pass before each release:
  - `npm run build`
  - `npm run check:server-syntax`
  - `npm run smoke:all`
  - `npm run e2e:browser-smoke`
- [ ] Complete the manual sign-off in `BROWSER_OPERATOR_SIGNOFF.md`
- [ ] Complete the manual real-environment checks in `MANUAL_REAL_TEST_MATRIX.md`

---

## 13. Process Management & Reliability

- [ ] Run each backend service under a process manager (systemd, PM2, Docker with restart policy)
- [ ] Set `CONTROL_SHUTDOWN_GRACE_MS` to a value ≥ your load balancer's connection drain timeout
- [ ] Configure health-check URLs at your load balancer:
  - auth-api: `/api/auth/health`
  - cloud-browser-api: `/api/cloud-browser/health`
  - sending-api: `/api/sending/health`
  - google-accounts-api: `/api/google-accounts/health`
  - calendar-invite-api: `/api/calendar-invite/health`
  - root-app-api: `/api/root-app/health`

---

## 14. Monitoring & Logging

- [ ] Forward structured JSON logs from all services to a central log aggregation system
- [ ] Set up alerts on `"level":"error"` log events
- [ ] Monitor rate-limit `429` responses — sudden spikes indicate abuse
- [ ] Review the root-app audit log (`/api/audit-logs`) periodically for anomalous actions
- [ ] Confirm `CONTROL_REQUEST_LOG_ENABLE=true` is set for production audit trails

---

## 15. Post-Deploy Verification

- [ ] Open the browser Settings → Runtime Posture panel and confirm all modules show `real` mode
- [ ] Send a real test email through the Sending module and confirm receipt
- [ ] Create a real calendar invite through the Calendar Invite module and confirm delivery
- [ ] Log in with a production user account and confirm token refresh works over HTTPS
- [ ] Confirm cookies carry the `Secure` flag in browser DevTools → Application → Cookies
- [ ] Run a TLS quality check (e.g., <https://www.ssllabs.com/ssltest/>) and target grade A

---

*Generated by the HTTPS production scan — Control OS (platform-control-generic).*
