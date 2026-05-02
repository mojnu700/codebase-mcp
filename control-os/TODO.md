# Control OS — delivery board

**Mission:** production-grade, generic operator platform; new work follows **[docs/HANDOFF_NEW_AGENT_AND_MODULE.md](docs/HANDOFF_NEW_AGENT_AND_MODULE.md)** and `**npm run verify:prod-gate`** before merge.

## Open (Definition of Done / release)

- Runtime surfaces explicit in prod (`real` / `fake` only; no `auto` in prod-shaped builds)
— enforced by `src/lib/auth-runtime.ts` (`readAppApiMode()` always returns `"real"`) and `scripts/verify/check-no-fake-modes.mjs` + `scripts/verify/prod-runtime-posture.mjs`
- Root Surfaces (`/live`, `/cost`, `/scheduler`) remain contract-stable under gate
— pages fully rewritten (corrupted JSX fixed); all required text + testids present; `SharedFilterControls` wired
- Shared filter (project + time range) fully wired, not partial UI-only
— `/live` and `/scheduler` use client-side filter (session/ops APIs have no server-side filter params); `/cost` passes `projectId` + `timeRange` as server-side query params to `/api/cost/ledger`
- E2E covers root surfaces against real root-app API (standalone stack when `ROOT_SURFACES_BASE_URL` unset)
— `npm run e2e:root-surfaces-smoke`; included in `verify:phase07`, CI, and `verify:prod-gate`
- Go-live evidence + rollback exercised per [docs/production/END_TO_END_GO_LIVE.md](docs/production/END_TO_END_GO_LIVE.md)
— `docs/production/STAGING_EVIDENCE_BUNDLE_2026-04-19.md` signed; rollback runbook reviewed and accepted; `CUTOVER_EXECUTION_2026-04-19.md` GO decision recorded

## Production cutover (Phase 3.2 — org / deploy)

- Deploy validated artifact set ([docs/production/PRODUCTION_CUTOVER_PLAN.md](docs/production/PRODUCTION_CUTOVER_PLAN.md))
— refresh release evidence on the active head before traffic ramp; do not rely on the older 2026-04-19 validated SHA
- Controlled ramp-up + error budgets (plan §7)
— ramp phases A/B/C defined with abort thresholds locked in `CUTOVER_EXECUTION_2026-04-19.md` §6; VPS execution pending operator
- Post-release report ([docs/production/POST_RELEASE_REPORT_TEMPLATE.md](docs/production/POST_RELEASE_REPORT_TEMPLATE.md))
— filed at `docs/production/POST_RELEASE_REPORT_2026-04-19.md`; update with current-head verification evidence and live ramp timestamps during controlled go-live

## Baseline (keep green)

- `npm run verify:prod-gate` — full release bar
- `npm run verify:phase08` — faster incremental (`verify:phase07` + dashboard federation smoke; phase07 includes browser + root-surfaces E2E, aligned with CI)
- `npm run e2e:root-surfaces-smoke` — root surfaces E2E (standalone: auth + root-app + Vite when `ROOT_SURFACES_BASE_URL` unset; CI runs this)

Phases **1–2** (posture, root surfaces, policy, contracts) and **4–5** roadmap items are **done** in tree; detail lives in `**deploy/production/`**, `**docs/production/`**, and `**docs/decisions/**` (ADRs). Dated cutover log: `docs/production/CUTOVER_EXECUTION_2026-04-19.md`.

## Pending (VPS production host — operator action required)

- Physically delete the leftover shadow folder `.continue/prompts/N workspace` after VS Code releases the file lock
- Confirm the updated `deploy/production/systemd/*.service` set and `control-os.target` are installed on the VPS via the deploy workflow before traffic ramp
- Execute VPS traffic ramp phases A/B/C (`CUTOVER_EXECUTION_2026-04-19.md` §5)
- Fill in ramp timeline + error budget checkpoint log in `POST_RELEASE_REPORT_2026-04-19.md` §4–5

P0 gate hygiene (done in tree): `e2e:root-surfaces-smoke` is part of `verify:prod-gate` in `package.json`; smoke helpers use `fetchWithRetry`, env-tunable health/server timeouts (see `.env.example` § Smoke / verify).
