#!/usr/bin/env python3
"""Patch batch-workspace-store.mjs and server.mjs with claim/release/complete support."""

import os

STORE_PATH = "/opt/control-os/current/server/batch-workspace-api/batch-workspace-store.mjs"
SERVER_PATH = "/opt/control-os/current/server/batch-workspace-api/server.mjs"

# ── STORE PATCH ─────────────────────────────────────────────────────────────

with open(STORE_PATH, "r") as f:
    store = f.read()

OLD_CREATE = '''    async createTask({ actorId, batchId, title, description, assigneeId }) {
      let created = null;
      await json.mutate((draft) => {
        const task = {
          id: newId("tsk"),
          batchId,
          title,
          description: description || null,
          status: "open",
          assigneeId: assigneeId || null,
          createdAt: nowIso(),
          createdBy: actorId,
          updatedAt: nowIso(),
        };
        draft.tasks.unshift(task);
        created = task;
      });
      return created;
    },'''

NEW_CREATE = '''    async createTask({ actorId, batchId, title, description, assigneeId, type, reviewMode, executionMode, priority }) {
      let created = null;
      await json.mutate((draft) => {
        const task = {
          id: newId("tsk"),
          workspaceId: null,
          batchId,
          title,
          description: description || null,
          status: "open",
          type: type || "general",
          reviewMode: reviewMode || "review",
          executionMode: executionMode || "browser_guided",
          priority: priority || "normal",
          assigneeId: assigneeId || null,
          claimedBy: null,
          claimedAt: null,
          completedAt: null,
          outcome: null,
          createdAt: nowIso(),
          createdBy: actorId,
          updatedAt: nowIso(),
        };
        draft.tasks.unshift(task);
        created = task;
      });
      return created;
    },

    async claimTask({ taskId, actorId }) {
      let updated = null;
      await json.mutate((draft) => {
        const tasks = Array.isArray(draft.tasks) ? draft.tasks : [];
        const idx = tasks.findIndex((t) => t.id === taskId);
        if (idx === -1) return;
        const task = tasks[idx];
        if (task.status !== "open" && task.status !== "pending") return;
        if (task.claimedBy) return;
        tasks[idx] = { ...task, status: "claimed", claimedBy: actorId, claimedAt: nowIso(), updatedAt: nowIso() };
        updated = tasks[idx];
      });
      return updated;
    },

    async releaseTask({ taskId, actorId }) {
      let updated = null;
      await json.mutate((draft) => {
        const tasks = Array.isArray(draft.tasks) ? draft.tasks : [];
        const idx = tasks.findIndex((t) => t.id === taskId);
        if (idx === -1) return;
        const task = tasks[idx];
        if (task.claimedBy !== actorId) return;
        tasks[idx] = { ...task, status: "open", claimedBy: null, claimedAt: null, updatedAt: nowIso() };
        updated = tasks[idx];
      });
      return updated;
    },

    async completeTask({ taskId, actorId, status, outcome }) {
      let updated = null;
      await json.mutate((draft) => {
        const tasks = Array.isArray(draft.tasks) ? draft.tasks : [];
        const idx = tasks.findIndex((t) => t.id === taskId);
        if (idx === -1) return;
        const task = tasks[idx];
        if (task.claimedBy !== actorId) return;
        const finalStatus = status === "failed" ? "failed" : "done";
        tasks[idx] = { ...task, status: finalStatus, completedAt: nowIso(), outcome: outcome || null, updatedAt: nowIso() };
        updated = tasks[idx];
      });
      return updated;
    },'''

if OLD_CREATE in store:
    store = store.replace(OLD_CREATE, NEW_CREATE)
    with open(STORE_PATH, "w") as f:
        f.write(store)
    print("STORE: patched createTask + added claimTask/releaseTask/completeTask")
else:
    print("STORE: OLD_CREATE not found - already patched or changed")

# ── SERVER PATCH ─────────────────────────────────────────────────────────────

with open(SERVER_PATH, "r") as f:
    server = f.read()

# Insert claim/release/complete routes BEFORE the workspace admin posture section
OLD_SERVER = '''      // -----------------------------------------------------------------
      // Workspace Admin Posture
      // (frontend batchWorkspaceClient routes /api/workspace/admin/* here)
      // -----------------------------------------------------------------'''

NEW_SERVER = '''      // -----------------------------------------------------------------
      // Task lifecycle — claim, release, complete
      // -----------------------------------------------------------------

      const taskClaimMatch = path.match(/^\\/api\\/batch-workspace\\/tasks\\/([^/]+)\\/claim$/);
      if (taskClaimMatch && method === "POST") {
        const taskId = decodeURIComponent(taskClaimMatch[1]);
        setRequestContextFields({ operation: "batch-workspace.tasks.claim" });
        const task = await store.getTaskById(taskId);
        if (!task) { sendJson(res, 404, fail("NOT_FOUND", "Task not found")); return; }
        if (!(await requireBatchAccess(res, actor, task.batchId))) return;
        const rlKey = buildRateLimitKey(["batch_workspace", "tasks_claim", actor.id]);
        if (!(await enforceRateLimit(res, writeRateLimiter, rlKey, { route: "tasks.claim" }))) return;
        const updated = await store.claimTask({ taskId, actorId: actor.id });
        if (!updated) { sendJson(res, 409, fail("CONFLICT", "Task cannot be claimed in its current state")); return; }
        sendJson(res, 200, ok({ task: updated }));
        return;
      }

      const taskReleaseMatch = path.match(/^\\/api\\/batch-workspace\\/tasks\\/([^/]+)\\/release$/);
      if (taskReleaseMatch && method === "POST") {
        const taskId = decodeURIComponent(taskReleaseMatch[1]);
        setRequestContextFields({ operation: "batch-workspace.tasks.release" });
        const task = await store.getTaskById(taskId);
        if (!task) { sendJson(res, 404, fail("NOT_FOUND", "Task not found")); return; }
        if (!(await requireBatchAccess(res, actor, task.batchId))) return;
        const updated = await store.releaseTask({ taskId, actorId: actor.id });
        if (!updated) { sendJson(res, 409, fail("CONFLICT", "Task is not claimable by you or not in a releasable state")); return; }
        sendJson(res, 200, ok({ task: updated }));
        return;
      }

      const taskCompleteMatch = path.match(/^\\/api\\/batch-workspace\\/tasks\\/([^/]+)\\/complete$/);
      if (taskCompleteMatch && method === "POST") {
        const taskId = decodeURIComponent(taskCompleteMatch[1]);
        setRequestContextFields({ operation: "batch-workspace.tasks.complete" });
        const task = await store.getTaskById(taskId);
        if (!task) { sendJson(res, 404, fail("NOT_FOUND", "Task not found")); return; }
        if (!(await requireBatchAccess(res, actor, task.batchId))) return;
        const body = await readJson(req);
        if (!body) { sendJson(res, 400, fail("INVALID_JSON", "Invalid JSON")); return; }
        const completionStatus = body.status === "failed" ? "failed" : "done";
        const outcome = typeof body.outcome === "string" && body.outcome.trim() ? body.outcome.trim() : null;
        const rlKey = buildRateLimitKey(["batch_workspace", "tasks_complete", actor.id]);
        if (!(await enforceRateLimit(res, writeRateLimiter, rlKey, { route: "tasks.complete" }))) return;
        const updated = await store.completeTask({ taskId, actorId: actor.id, status: completionStatus, outcome });
        if (!updated) { sendJson(res, 409, fail("CONFLICT", "Task cannot be completed — you may not be the claimer")); return; }
        sendJson(res, 200, ok({ task: updated }));
        return;
      }

      // -----------------------------------------------------------------
      // Workspace Admin Posture
      // (frontend batchWorkspaceClient routes /api/workspace/admin/* here)
      // -----------------------------------------------------------------'''

if OLD_SERVER in server:
    server = server.replace(OLD_SERVER, NEW_SERVER)
    with open(SERVER_PATH, "w") as f:
        f.write(server)
    print("SERVER: added claim/release/complete routes")
else:
    print("SERVER: target anchor not found - already patched or changed")

# ── Also update createTask route in server to pass extra fields ───────────────

with open(SERVER_PATH, "r") as f:
    server = f.read()

OLD_TASK_CREATE = '''        const created = await store.createTask({ actorId: actor.id, batchId, title, description, assigneeId });'''
NEW_TASK_CREATE = '''        const taskType = ["general","browser","data_entry","review","approval"].includes(body.type) ? body.type : "general";
        const reviewModeVal = ["auto","review","manual_only"].includes(body.reviewMode) ? body.reviewMode : null;
        const execModeVal = ["browser_guided","cloud_automated","api_automated","esp_automated"].includes(body.executionMode) ? body.executionMode : null;
        const priorityVal = ["low","normal","high","urgent"].includes(body.priority) ? body.priority : null;
        const created = await store.createTask({ actorId: actor.id, batchId, title, description, assigneeId, type: taskType, reviewMode: reviewModeVal, executionMode: execModeVal, priority: priorityVal });'''

if OLD_TASK_CREATE in server:
    server = server.replace(OLD_TASK_CREATE, NEW_TASK_CREATE)
    with open(SERVER_PATH, "w") as f:
        f.write(server)
    print("SERVER: updated createTask to pass extra fields")
else:
    print("SERVER: createTask call not found - skipping")

print("Done.")
