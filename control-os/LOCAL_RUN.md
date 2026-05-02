# Local Run

Local development uses the real module backends plus the Vite app shell.

## Fast Start

- Double-click [start-local-dev.cmd](start-local-dev.cmd)
- Or run `npm run dev:all`
- For an isolated Sending Go worker validation stack on alternate ports, run `npm run dev:sending-worker-live`
- For the shortest onboarding path, start with [docs/DEVELOPER_QUICKSTART.md](docs/DEVELOPER_QUICKSTART.md)

## Local URLs

- App: `http://127.0.0.1:5173/login`
- Auth API: `http://127.0.0.1:8779`
- Cloud Browser API: `http://127.0.0.1:8787`
- Sending API: `http://127.0.0.1:8788`
- Google Accounts API: `http://127.0.0.1:8789`
- Calendar Invite API: `http://127.0.0.1:8790`
- Root App API: `http://127.0.0.1:8792`
- Batch Workspace API: `http://127.0.0.1:8793`
- Workspace API: `http://127.0.0.1:8794`
- Session API: `http://127.0.0.1:8795`

## Isolated Sending Worker Validation Stack

Use this when the default local ports are already occupied or when you want a clean worker-validation posture without starting unrelated services.

- Command: `npm run dev:sending-worker-live`
- Services started:
  - Auth API: `http://127.0.0.1:8879`
  - Google Accounts API: `http://127.0.0.1:8889`
  - Sending API: `http://127.0.0.1:8888`
  - Sending Go Worker: `http://127.0.0.1:8891/readyz`
- This mode uses an isolated data root at `.dev-data/sending-worker-live/`
- It does not start Vite, Cloud Browser, or Calendar Invite
- It starts the Go worker automatically for this profile
- If `go` is not on PATH, set `SENDING_GO_WORKER_GO_BINARY`
- For a real Gmail/live-send run, set `SENDING_ALLOWED_RECIPIENT_DOMAINS` to include the controlled recipient domain before starting this profile if it is not `example.com`
- You can override the profile ports explicitly with:
  - `CONTROL_DEV_AUTH_PORT`
  - `CONTROL_DEV_GOOGLE_ACCOUNTS_PORT`
  - `CONTROL_DEV_SENDING_PORT`
  - `CONTROL_DEV_SENDING_GO_WORKER_PORT`

## Desktop (Tauri) note

- Web local dev uses Vite on `5173` and module APIs on their ports (above).
- Tauri dev uses Vite on `1420` by default. (`vite.config.ts`, `src-tauri/tauri.conf.json`)
- Tauri CSP restricts network connections via `connect-src` allowlisting; multi-origin module API access must be explicitly allowlisted (see `docs/decisions/ADR-0002-tauri-multi-origin-connectivity.md`). (`src-tauri/tauri.conf.json`)

## Dev Login

- Email: `admin@example.com`
- Password: `admin-password`

## Notes

- This launcher is development-only.
- It uses explicit token auth posture; it does not rely on `CONTROL_AUTH_MODE=dev_local`.
- It seeds a local auth user directory from the launcher environment.
- Root app APIs remain fake-backed in local dev.
- Settings now exposes this clearly in the Runtime Posture panel.
- Module data persists under `.dev-data/`.
- Sending and Calendar allowlists still default to `example.com` in this local run posture.
- The local launcher injects distinct service JWTs for Sending and Calendar Invite so both can call the Google Accounts broker.
- The local launcher does not start a Go Sending worker. If you exercise the pilot-scoped internal worker boundaries manually, wire `CONTROL_SERVICE_JWT_ISSUER`, `CONTROL_SERVICE_JWT_PUBLIC_KEY_PEM`, and `SENDING_INTERNAL_CALLBACK_SERVICE_JWT_AUDIENCE` into `sending-api` so it can verify internal claim/release/result calls.
- The local launcher can also start the Go Sending worker pilot if you opt in with `SENDING_GO_WORKER_ENABLE=true`. If `go` is not on PATH, set `SENDING_GO_WORKER_GO_BINARY` to the Go executable you want the launcher to use.
- The isolated `dev:sending-worker-live` launcher is the preferred local posture for the first real Gmail/live-send validation because it avoids default-port collisions and keeps queue/truth ownership in the real `sending-api`.
- A narrow repo-native end-to-end pilot smoke exists at `npm run smoke:sending-go-worker`; it starts local Auth, Google Accounts, Sending, a deterministic Gmail/token stub, and the Go worker to exercise the real claim -> broker -> Gmail submit -> callback path without requiring a live Gmail account.
- Google OAuth secrets remain owned by `google-accounts-api` in local dev; Sending Gmail API plus Calendar Google provider and Gmail-first `email_invite` paths do not read Google Accounts files directly.
- Calendar push protection uses an explicit dev secret in the launcher env.
- Backend responses emit request/correlation ids, and local shutdown now uses a bounded graceful drain window before force-closing idle handles.

## Real DSN Mailbox Follow-up Validation

Use this only after the Gmail API live-send path is already working on the isolated stack.

Recommended posture:

- start `npm run dev:sending-worker-live`
- keep `SENDING_SEND_WORKER_ENABLE=false`
- keep the Go worker pilot enabled only for Gmail API submission
- enable DSN follow-up separately by configuring the Sending DSN mailbox

Required operator inputs:

- one real IMAP mailbox that will actually receive bounce / DSN notices for the controlled Gmail sender
- mailbox host, port, TLS posture, username, and password
- the mailbox folder to poll, usually `INBOX`

Current auth constraint:

- the DSN mailbox path supports `basic_auth` only in this slice
- if the mailbox provider is Gmail-hosted, use a mailbox credential that really works with IMAP basic auth in your environment; do not plan on `oauth2_ref` for this phase

Exact config path:

- inspect current DSN mailbox config:
  - `GET http://127.0.0.1:8888/api/sending/dsn-mailbox/config`
- update DSN mailbox config:
  - `PUT http://127.0.0.1:8888/api/sending/dsn-mailbox/config`

Minimal real mailbox config payload:

```json
{
  "enabled": true,
  "host": "imap.gmail.com",
  "port": 993,
  "secure": true,
  "authMode": "basic_auth",
  "username": "REPLACE_ME",
  "password": "REPLACE_ME",
  "mailbox": "INBOX",
  "pollIntervalMs": 60000,
  "batchSize": 10
}
```

Validation flow:

- submit one real Gmail API send through Sending
- wait for the later bounce/delay/confirmation notice to land in the configured mailbox
- trigger one manual follow-up tick:
  - `POST http://127.0.0.1:8888/api/sending/execution/dsn-poll-tick`
- inspect:
  - `GET http://127.0.0.1:8888/api/sending/delivery-attempts`
  - `GET http://127.0.0.1:8888/api/sending/delivery-evidence?deliveryAttemptId=<id>`

Expected Gmail-first truth behavior:

- submission truth stays `provider_accepted`
- later strong DSN/mailbox evidence may move the attempt outcome to `bounced`, `deferred`, or `sent`
- truth ownership stays in `sending-api`; the Go submission worker does not wait for this path
