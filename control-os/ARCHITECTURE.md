# Control OS — Architecture

## Overview

Control OS is an enterprise-grade, multi-surface operator shell. The React/TypeScript SPA talks to a set of independent Node.js ESM microservices and one Go worker over HTTP. They share no runtime state except JWT-based auth.

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend SPA | React 18, TypeScript, Vite 6, Tailwind CSS 3 |
| Desktop shell | Tauri 2 (wraps the SPA) |
| Microservices | Node.js 24 ESM (plain `.mjs`, no transpile) |
| Go worker (pilot) | Go — Gmail API send execution worker |
| Primary persistence | File-based JSON with atomic writes + file locking (`durable-json-store.mjs`) |
| Optional persistence | PostgreSQL (`postgres` npm package), Redis |
| Container orchestration | Docker / Docker Compose, Kubernetes |
| Monitoring | Prometheus + Grafana |
| Auth | HS256 JWT (access token, 15 min TTL) + httponly refresh cookie (7 day TTL) |
| Service auth | RS256 signed service JWTs for service-to-service calls |

## Service Port Map

| Service | Default Port | Responsibility |
|---|---|---|
| `auth-api` | **8779** | Login, token refresh, RBAC, session store |
| `cloud-browser-api` | **8787** | Browser profile/session orchestration, GoLogin provider |
| `sending-api` | **8788** | Email dispatch, delivery queue, mixed fleet routing |
| `google-accounts-api` | **8789** | OAuth token broker — service-only endpoints, never called by the UI directly |
| `calendar-invite-api` | **8790** | Calendar invite dispatch, ICS generation, Google Calendar provider |
| `sending-go-worker` | **8791** | Go pilot for Gmail API execution (claim/release/callback over HTTP) |
| `root-app-api` | **8792** | Projects, runs, workers, alerts, audit log, cost ledger, dashboard federation |
| `batch-workspace-api` | **8793** | Batch workspace management, worker inbox |
| `workspace-api` | **8794** | Workspaces, batches, members, tasks (claim/release/complete) |
| `session-api` | **8795** | Device enrollment, session lifecycle (start/heartbeat/release) |
| Vite dev server | **5173** | Frontend development |
| Tauri dev | **1420** | Desktop shell development |

## Frontend Architecture (`src/`)

### Module System

All features are delivered as **modules** registered at startup via `registerModule()` in `src/modules/index.ts` before React renders. A `ModuleDefinition` declares routes, sidebar nav items, modals, dashboard widgets, a settings panel, and permission keys. The module registry (`src/lib/module-registry.ts`) enforces:

- Duplicate registration guard
- `minHostVersion` compatibility check (current `HOST_VERSION = "2.0.0"`)
- Dependency presence checks
- Plugin protocol negotiation for external plugins (`pluginContract`)

Registered modules (10 total):

| Module ID | Nav section | Key routes |
|---|---|---|
| `ops` | operations | `/ops` |
| `cloud-browser` | operations | `/cloud-browser` |
| `calendar-invite` | operations | `/calendar-invite` |
| `sending` | operations | `/sending` |
| `batch-workspace` | operations | `/batch-workspace` |
| `session` | operations | `/session` |
| `workspace` | operations | `/workspace` |
| `task-manager` | operations | `/tasks` |
| `root-app` | overview | `/dashboard`, `/projects`, `/runs`, `/workers` |
| `root-surfaces` | operations | `/live`, `/scheduler`, `/cost` |

### Runtime Posture (`src/lib/runtime-posture.ts`)

Controls which backends are real vs. fake per surface, driven by `VITE_*_API_MODE` env vars. The `apiClient` (`src/lib/api-client.ts`) intercepts calls and routes to either the in-browser `fakeBackend` (demo data) or a live HTTP backend.

**ADR-0001:** Never use `VITE_*_API_MODE=auto` in production. Always set explicit `real` or `fake`.

### Auth (`src/app/store/auth-store.ts`, `src/lib/auth-runtime.ts`)

Two auth modes:
- `external` — backend-issued JWTs with refresh via httponly cookie. Access tokens live **in memory only**; `sessionStorage` stores only user metadata.
- `local` — dev bridge only. Never use in production.

`fetchWithAuth()` handles `401 → silent refresh → retry` automatically.

### Fake Backend (dev mode only)

- `src/lib/fake-backend.ts` handles root app API routes
- Modules register dev-time fake routes via `registerFakeRoute()` inside `onInit()` — never directly in `fake-backend.ts`
- All fake routes are **blocked in production builds** (`import.meta.env.PROD` guard)

### Endpoints Contract

`src/lib/endpoints.ts` is the single source of truth for all frontend API endpoint paths.

### State Management

- Zustand stores under `src/app/store/` for client state
- React Query for server state
- No Redux

## Backend Architecture (`server/`)

Each directory is an **independent** Node.js ESM service. They do not import each other at runtime — cross-service calls use HTTP with service JWTs.

### Shared Utilities (`server/shared/`)

| File | Purpose |
|---|---|
| `durable-json-store.mjs` | All persistence — file-based JSON, atomic writes, file locking |
| `durable-queue.mjs` | Durable queue abstraction over the JSON store |
| `auth.mjs` | HS256 JWT minting, verification, scrypt password hashing |
| `service-jwt.mjs` | RS256 service-to-service JWT verification |
| `graceful-runtime.mjs` | SIGTERM/SIGINT drain handling (all services use this) |
| `workflow-runtime.mjs` | Generic async workflow/execution loop (sending, calendar-invite) |
| `operator-authz.mjs` | RBAC check middleware |
| `http-security.mjs` | CORS policy, security headers, cookie serialization |
| `rate-limit.mjs` | Per-IP rate limiting with distributed Redis backend support |
| `logger.mjs` / `structured-logger.mjs` | Structured JSON logging |
| `secret-crypto.mjs` | AES-GCM secret encryption (master key: `CONTROL_SECRET_MASTER_KEY`) |
| `postgres.mjs` / `postgres-store.mjs` | Optional PostgreSQL backend |
| `redis.mjs` / `redis-store.mjs` | Optional Redis backend |
| `request-context.mjs` | X-Request-ID, X-Correlation-ID propagation |

### Cross-Service Communication

All service-to-service calls use HTTP with **RS256 signed service JWTs**:

- `sending-api` → `google-accounts-api`: broker token fetch (audience: `google-accounts-broker`)
- `calendar-invite-api` → `google-accounts-api`: same broker pattern
- `sending-go-worker` → `sending-api`: claim / release / callback (audience: `sending-execution-callback`)

The UI **never** calls `google-accounts-api` broker endpoints directly.

## Go Worker (`server/sending-go-worker-pilot/`)

Pilot implementation for Gmail API send execution. The worker:

1. **Claims** a task from `sending-api` via `POST /api/sending/internal/execution/claim` using a signed RS256 service JWT.
2. **Executes** the Gmail API send using an OAuth access token obtained from the `google-accounts-api` broker.
3. **Releases/callbacks** the result via `POST /api/sending/internal/execution/callback`.

The worker **never reads the durable queue file directly**. All coordination is over HTTP.

## RBAC

Roles: `admin`, `manager`, `lead`, `worker`, `viewer` (defined in `src/lib/permissions.ts`).

Modules extend role permissions at startup via `registerPermissions()` or the declarative `policyCapabilities[]` array in `ModuleDefinition`. Permission keys follow the pattern `<module>:<action>`, e.g. `sending:create`, `cloud-browser:launch`.

## Persistence Modes

| Service | Default store | Optional store |
|---|---|---|
| auth-api | JSON (`durable-json-store`) | — |
| cloud-browser-api | JSON (`durable-json-store`) | — |
| sending-api | JSON (`durable-json-store`) | PostgreSQL |
| google-accounts-api | JSON (`durable-json-store`) | — |
| calendar-invite-api | JSON (`durable-json-store`) | — |
| root-app-api | JSON (`durable-json-store`) | — |
| batch-workspace-api | JSON (`durable-json-store`) | PostgreSQL |
| workspace-api | JSON (`durable-json-store`) | PostgreSQL |
| session-api | JSON (file-based) | — |

## Health & Monitoring

Every service exposes a `/api/<service>/health` endpoint. Prometheus scrapes these endpoints; dashboards are provided in `monitoring/grafana-dashboard.json`. Alert rules are in `monitoring/alert-rules.yml`.

## Infrastructure

| Artifact | Path |
|---|---|
| Docker | `Dockerfile`, `docker-compose.yml` |
| Kubernetes | `k8s/control-os-deployment.yml` |
| Nginx (production TLS) | `deploy/production/nginx/` |
| Caddy (production TLS) | `deploy/production/caddy/` |
| Systemd units | `deploy/production/systemd/` |
| GitHub CI | `.github/workflows/ci.yml` |
| Auto-deploy VPS | `.github/workflows/auto-deploy-vps.yml` |
| Production gate | `.github/workflows/production-gate.yml` |

## Production Gate

```
npm run verify:prod-gate
```

Runs in sequence: runtime posture check → auth posture check → no-fake-modes check → TypeScript build → unit tests → server syntax check → all smoke tests → E2E browser smoke.

## Architecture Decision Records

| ADR | Summary |
|---|---|
| ADR-0001 | Never use `VITE_*_API_MODE=auto` in production — explicit `real`/`fake` only |
| ADR-0002 | Tauri desktop requires CSP allowlisting for any backend origin |
| ADR-0003 | Google Accounts uses an HTTP service boundary — no direct file reads by other services |
| ADR-0004 | Plugin protocol versioning for external module plugins |
| ADR-0005 | Multi-tenant posture — tenant isolation at the service boundary |