# Control OS

Control OS is a modular operator platform with a stable shell, a reusable workflow spine, and real specialized backends for operational modules. Forks should keep the codebase **generic** (env-driven, no tenant-specific hardcoding in shared layers) and avoid **silent demo or fake metrics** on paths covered by production verification; see `AGENTS.md` and `.cursor/rules/generic-platform-no-demo-data.mdc`.

Current live module slices:

- Cloud Browser
- Sending
- Google Accounts
- Calendar Invite

The platform is not a starter scaffold anymore. It is a serious base with real module backends, backend-auth verification, smoke gates, browser smoke, and local-run tooling.

## Current Architecture

Generic platform layers:

- Tauri + React + TypeScript shell
- module host and module registry
- generic workflow contracts
- backend auth verification
- durable JSON stores and bounded durable queues
- Google Accounts HTTP boundary with service-brokered short-lived Google access tokens

Specialized module layers:

- Cloud Browser for provider-backed browser operations
- Sending for Provider API, SMTP, Gmail SMTP, and Gmail API transport work
- Google Accounts for backend-owned Google credential ownership, readiness, and broker issuance
- Calendar Invite for Google Calendar provider workflows and Gmail-first `email_invite` workflows, with a unified truth contract in `src/contract/calendar-invite-unified-truth-model.md`

Current Google-backed boundary truth:

- `google-accounts-api` owns the durable Google Accounts store and OAuth secrets.
- Calendar Invite's Google Calendar provider path uses the Google Accounts broker.
- Calendar Invite's Gmail-first `email_invite` path uses the Google Accounts broker with `email.send`.
- Sending's Gmail API transport path uses the Google Accounts broker.
- Sending SMTP and generic HTTP JSON provider behavior were intentionally not changed by the broker migration work.
- Calendar `email_invite` is implemented today for Gmail API create/update/cancel with Calendar-owned ICS generation and persisted invite evidence.
- SMTP invite transport, DSN/receipt confirmation, delegated send/alias support, and browser/cloud-browser invite execution modes remain deferred.

## Runtime Posture

Important current boundary:

- module backends are real
- auth backend is real
- some root app APIs are still intentionally fake-backed unless you provide a real root app API

That mixed posture is explicit in:

- [PRODUCTION_HANDOFF.md](PRODUCTION_HANDOFF.md)
- [LOCAL_RUN.md](LOCAL_RUN.md)
- the Runtime Posture panel in Settings

## Adding a module

**New agent / empty chat:** **[docs/HANDOFF_NEW_AGENT_AND_MODULE.md](docs/HANDOFF_NEW_AGENT_AND_MODULE.md)** (single entry, then links below).

Authoring checklist: **[docs/MODULE_AUTHORING.md](docs/MODULE_AUTHORING.md)**. Repo policy: **[AGENTS.md](AGENTS.md)**.

## Local Run

Fastest local start:

- double-click [start-local-dev.cmd](start-local-dev.cmd)

Fastest reliable developer onboarding path:

- read [docs/DEVELOPER_QUICKSTART.md](docs/DEVELOPER_QUICKSTART.md)

Terminal fallback:

```bash
npm install
npm run dev:all
```

Local run details are documented in [LOCAL_RUN.md](LOCAL_RUN.md).

Developer onboarding and local workflow details are documented in [docs/DEVELOPER_QUICKSTART.md](docs/DEVELOPER_QUICKSTART.md).

## Verification

Main production gate:

```bash
npm run verify:prod-gate
```

That gate includes:

- `scripts/verify/prod-runtime-posture.mjs` and `scripts/verify/prod-auth-posture.mjs`
- `scripts/verify/check-no-fake-modes.mjs`
- `npm run build`
- `npm run test` (Vitest)
- `npm run check:server-syntax`
- `npm run smoke:all`
- `npm run e2e:browser-smoke`
- `npm run e2e:root-surfaces-smoke`

Additional local pilot validation:

- `npm run smoke:sending-go-worker`

That smoke is intentionally local/dev only. It runs the real Sending Go worker against the real internal Sending lease/broker/callback boundaries while using a deterministic local Gmail stub instead of a live Gmail send.

## Environment

Use [.env.example](.env.example) as the canonical template.

Important:

- `VITE_*` variables are browser build/dev variables
- backend secrets must stay backend-owned
- backend auth now fails safe to token posture when `CONTROL_AUTH_MODE` is unset
- `VITE_AUTH_MODE=local` and `CONTROL_AUTH_MODE=dev_local` are development-only and must be explicitly opted into
- `VITE_APP_API_MODE=fake` is still a mixed-posture bridge, not full enterprise-live posture
- Calendar push/webhook protection now requires an explicit `CALENDAR_INVITE_PUSH_TOKEN_SECRET`, unless you intentionally enable the dev-only fallback env
- minimal built-in rate limits protect login, refresh, webhook ingest, dispatch submit, and high-impact config writes
- backend responses now emit request/correlation headers and structured logs carry those ids through request handling
- services now use bounded graceful shutdown windows and expose runtime/lifecycle posture in health and execution posture exports

## Intentionally Deferred

Still later work, not falsely claimed complete:

- full real root app API replacement for every non-module demo page
- backend server decomposition for the largest module servers
- database-backed state/queue for multi-node scale
- enterprise SSO / MFA / advanced IAM
- packaging/release automation beyond the current production gate
