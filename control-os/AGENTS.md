# Agent and contributor defaults

Control OS is maintained as a **generic**, fork-friendly operator platform.

- **New Cursor chat or new agent:** read **[docs/HANDOFF_NEW_AGENT_AND_MODULE.md](docs/HANDOFF_NEW_AGENT_AND_MODULE.md)** first — it links everything below in order and is safe to paste into an empty thread.
- Follow **`.cursor/rules/generic-platform-no-demo-data.mdc`** everywhere in the repo (always on for Cursor).
- **Adding or changing a module** (UI under `src/modules/`, HTTP under `server/`): follow **[docs/MODULE_AUTHORING.md](docs/MODULE_AUTHORING.md)** first. Cursor also loads file-scoped rules **`.cursor/rules/module-additions-generic-no-fake.mdc`** and **`.cursor/rules/server-module-apis-generic-no-fake.mdc`** when those paths are in context — keep the same **no silent demo / env-driven** bar so **any AI** extending the tree stays aligned.
- Ship confidence: **`npm run verify:phase08`** (incremental) or **`npm run verify:prod-gate`** (full). See [README.md](README.md) and [deploy/production/README.md](deploy/production/README.md).
