#!/usr/bin/env python3
"""Patch root-app-api/server.mjs with:
  1. Task Manager routes (projects + tasks CRUD)
  2. Ops archive route (PATCH /api/ops/jobs/:id/archive)
"""

SERVER_PATH = "/opt/control-os/current/server/root-app-api/server.mjs"

with open(SERVER_PATH, "r") as f:
    server = f.read()

# ============================================================================
# 1.  Add OPERATOR_ACTION_DEFS entries for task-manager + ops archive
# ============================================================================

OLD_DEFS_TAIL = '''  opsReportCreate: {
    actionKey: "root-app.ops.reports.create",
    label: "Create ops report",
    risk: "bounded",
    requiredRoles: ["admin", "manager", "lead"],
    requiresJustification: false,
    note: "Creates a new ops report record.",
  },
};'''

NEW_DEFS_TAIL = '''  opsReportCreate: {
    actionKey: "root-app.ops.reports.create",
    label: "Create ops report",
    risk: "bounded",
    requiredRoles: ["admin", "manager", "lead"],
    requiresJustification: false,
    note: "Creates a new ops report record.",
  },
  opsJobArchive: {
    actionKey: "root-app.ops.jobs.archive",
    label: "Archive ops job",
    risk: "bounded",
    requiredRoles: ["admin", "manager"],
    requiresJustification: false,
    note: "Archives an ops job by marking its status.",
  },
  taskManagerProjectCreate: {
    actionKey: "root-app.task-manager.projects.create",
    label: "Create task-manager project",
    risk: "low",
    requiredRoles: ["admin", "manager", "lead", "worker"],
    requiresJustification: false,
    note: "Creates a new task-manager project.",
  },
  taskManagerProjectUpdate: {
    actionKey: "root-app.task-manager.projects.update",
    label: "Update task-manager project",
    risk: "low",
    requiredRoles: ["admin", "manager", "lead", "worker"],
    requiresJustification: false,
    note: "Updates a task-manager project.",
  },
  taskManagerProjectDelete: {
    actionKey: "root-app.task-manager.projects.delete",
    label: "Delete task-manager project",
    risk: "bounded",
    requiredRoles: ["admin", "manager"],
    requiresJustification: false,
    note: "Deletes a task-manager project and its tasks.",
  },
  taskManagerTaskCreate: {
    actionKey: "root-app.task-manager.tasks.create",
    label: "Create task-manager task",
    risk: "low",
    requiredRoles: ["admin", "manager", "lead", "worker"],
    requiresJustification: false,
    note: "Creates a new task in task-manager.",
  },
  taskManagerTaskUpdate: {
    actionKey: "root-app.task-manager.tasks.update",
    label: "Update task-manager task",
    risk: "low",
    requiredRoles: ["admin", "manager", "lead", "worker"],
    requiresJustification: false,
    note: "Updates a task-manager task (status, priority, assignee, etc.).",
  },
  taskManagerTaskDelete: {
    actionKey: "root-app.task-manager.tasks.delete",
    label: "Delete task-manager task",
    risk: "bounded",
    requiredRoles: ["admin", "manager", "lead"],
    requiresJustification: false,
    note: "Permanently deletes a task-manager task.",
  },
};'''

if OLD_DEFS_TAIL in server:
    server = server.replace(OLD_DEFS_TAIL, NEW_DEFS_TAIL)
    print("DEFS: patched OPERATOR_ACTION_DEFS")
else:
    print("DEFS: anchor not found - aborting")
    exit(1)

# ============================================================================
# 2.  Add RBAC_ROUTE_REGISTRY entries for task-manager + ops archive
# ============================================================================

OLD_RBAC_TAIL = '''  {
    match: (m, p) => m === "POST" && p === "/api/ops/reports",
    def: OPERATOR_ACTION_DEFS.opsReportCreate,
  },
];'''

NEW_RBAC_TAIL = '''  {
    match: (m, p) => m === "POST" && p === "/api/ops/reports",
    def: OPERATOR_ACTION_DEFS.opsReportCreate,
  },
  {
    match: (m, p) => m === "PATCH" && /^\\/api\\/ops\\/jobs\\/[^/]+\\/archive$/.test(p),
    def: OPERATOR_ACTION_DEFS.opsJobArchive,
  },
  {
    match: (m, p) => m === "POST" && p === "/api/task-manager/projects",
    def: OPERATOR_ACTION_DEFS.taskManagerProjectCreate,
  },
  {
    match: (m, p) => m === "PATCH" && /^\\/api\\/task-manager\\/projects\\/[^/]+$/.test(p),
    def: OPERATOR_ACTION_DEFS.taskManagerProjectUpdate,
  },
  {
    match: (m, p) => m === "DELETE" && /^\\/api\\/task-manager\\/projects\\/[^/]+$/.test(p),
    def: OPERATOR_ACTION_DEFS.taskManagerProjectDelete,
  },
  {
    match: (m, p) => m === "POST" && p === "/api/task-manager/tasks",
    def: OPERATOR_ACTION_DEFS.taskManagerTaskCreate,
  },
  {
    match: (m, p) => m === "PATCH" && /^\\/api\\/task-manager\\/tasks\\/[^/]+$/.test(p),
    def: OPERATOR_ACTION_DEFS.taskManagerTaskUpdate,
  },
  {
    match: (m, p) => m === "DELETE" && /^\\/api\\/task-manager\\/tasks\\/[^/]+$/.test(p),
    def: OPERATOR_ACTION_DEFS.taskManagerTaskDelete,
  },
];'''

if OLD_RBAC_TAIL in server:
    server = server.replace(OLD_RBAC_TAIL, NEW_RBAC_TAIL)
    print("RBAC: patched RBAC_ROUTE_REGISTRY")
else:
    print("RBAC: anchor not found - aborting")
    exit(1)

# ============================================================================
# 3.  Insert route handlers before the catch-all 404
# ============================================================================

CATCH_ALL = '''      // Catch-all: no route matched
      sendJson(res, 404, fail("NOT_FOUND", "Endpoint not found", { path, method }));'''

NEW_ROUTES = '''      // -----------------------------------------------------------------
      // Task Manager — Projects
      // -----------------------------------------------------------------

      if (path === "/api/task-manager/projects" && method === "GET") {
        setRequestContextFields({ operation: "task-manager.projects.list" });
        const state = store.getState();
        const projects = Array.isArray(state.taskManagerProjects) ? state.taskManagerProjects : [];
        sendJson(res, 200, ok({ items: projects, total: projects.length }));
        return;
      }

      if (path === "/api/task-manager/projects" && method === "POST") {
        setRequestContextFields({ operation: "task-manager.projects.create" });
        const body = await readJson(req);
        if (!body) { sendJson(res, 400, fail("INVALID_JSON", "Invalid JSON")); return; }
        const name = typeof body.name === "string" && body.name.trim() ? body.name.trim() : null;
        const color = typeof body.color === "string" && body.color.trim() ? body.color.trim() : "#6366f1";
        const description = typeof body.description === "string" && body.description.trim() ? body.description.trim() : null;
        if (!name) { sendJson(res, 422, fail("VALIDATION_FAILED", "name is required")); return; }
        const project = {
          id: `proj_${randomUUID().replace(/-/g, "").slice(0, 12)}`,
          name,
          color,
          description: description || null,
          createdAt: nowIso(),
          createdBy: actor.id,
          updatedAt: nowIso(),
        };
        await store.mutate((state) => {
          if (!Array.isArray(state.taskManagerProjects)) state.taskManagerProjects = [];
          state.taskManagerProjects.unshift(project);
        });
        sendJson(res, 200, ok({ project }));
        return;
      }

      const tmProjectMatch = path.match(/^\\/api\\/task-manager\\/projects\\/([^/]+)$/);
      if (tmProjectMatch && method === "PATCH") {
        const projectId = decodeURIComponent(tmProjectMatch[1]);
        setRequestContextFields({ operation: "task-manager.projects.update" });
        const body = await readJson(req);
        if (!body) { sendJson(res, 400, fail("INVALID_JSON", "Invalid JSON")); return; }
        let updated = null;
        await store.mutate((state) => {
          if (!Array.isArray(state.taskManagerProjects)) { state.taskManagerProjects = []; return; }
          const idx = state.taskManagerProjects.findIndex((p) => p.id === projectId);
          if (idx === -1) return;
          const proj = state.taskManagerProjects[idx];
          state.taskManagerProjects[idx] = {
            ...proj,
            name: typeof body.name === "string" && body.name.trim() ? body.name.trim() : proj.name,
            color: typeof body.color === "string" && body.color.trim() ? body.color.trim() : proj.color,
            description: typeof body.description === "string" ? (body.description.trim() || null) : proj.description,
            updatedAt: nowIso(),
          };
          updated = state.taskManagerProjects[idx];
        });
        if (!updated) { sendJson(res, 404, fail("NOT_FOUND", "Project not found")); return; }
        sendJson(res, 200, ok({ project: updated }));
        return;
      }

      if (tmProjectMatch && method === "DELETE") {
        const projectId = decodeURIComponent(tmProjectMatch[1]);
        setRequestContextFields({ operation: "task-manager.projects.delete" });
        let removed = false;
        await store.mutate((state) => {
          if (!Array.isArray(state.taskManagerProjects)) { state.taskManagerProjects = []; return; }
          const before = state.taskManagerProjects.length;
          state.taskManagerProjects = state.taskManagerProjects.filter((p) => p.id !== projectId);
          removed = state.taskManagerProjects.length !== before;
          if (Array.isArray(state.taskManagerTasks)) {
            state.taskManagerTasks = state.taskManagerTasks.filter((t) => t.projectId !== projectId);
          }
        });
        if (!removed) { sendJson(res, 404, fail("NOT_FOUND", "Project not found")); return; }
        sendJson(res, 200, ok({ deleted: true }));
        return;
      }

      // -----------------------------------------------------------------
      // Task Manager — Tasks
      // -----------------------------------------------------------------

      if (path === "/api/task-manager/tasks" && method === "GET") {
        setRequestContextFields({ operation: "task-manager.tasks.list" });
        const projectId = url.searchParams.get("projectId");
        const state = store.getState();
        let tasks = Array.isArray(state.taskManagerTasks) ? state.taskManagerTasks : [];
        if (projectId) tasks = tasks.filter((t) => t.projectId === projectId);
        sendJson(res, 200, ok({ items: tasks, total: tasks.length }));
        return;
      }

      if (path === "/api/task-manager/tasks" && method === "POST") {
        setRequestContextFields({ operation: "task-manager.tasks.create" });
        const body = await readJson(req);
        if (!body) { sendJson(res, 400, fail("INVALID_JSON", "Invalid JSON")); return; }
        const projectId = typeof body.projectId === "string" && body.projectId.trim() ? body.projectId.trim() : null;
        const title = typeof body.title === "string" && body.title.trim() ? body.title.trim() : null;
        if (!projectId || !title) { sendJson(res, 422, fail("VALIDATION_FAILED", "projectId and title are required")); return; }
        const validStatuses = ["todo","in_progress","done","blocked"];
        const validPriorities = ["low","normal","high","urgent"];
        const task = {
          id: `tsk_${randomUUID().replace(/-/g, "").slice(0, 12)}`,
          projectId,
          title,
          description: typeof body.description === "string" && body.description.trim() ? body.description.trim() : null,
          status: validStatuses.includes(body.status) ? body.status : "todo",
          priority: validPriorities.includes(body.priority) ? body.priority : "normal",
          assignee: typeof body.assignee === "string" && body.assignee.trim() ? body.assignee.trim() : null,
          dueDate: typeof body.dueDate === "string" && body.dueDate.trim() ? body.dueDate.trim() : null,
          tags: Array.isArray(body.tags) ? body.tags.filter((x) => typeof x === "string") : [],
          createdAt: nowIso(),
          createdBy: actor.id,
          updatedAt: nowIso(),
        };
        await store.mutate((state) => {
          if (!Array.isArray(state.taskManagerTasks)) state.taskManagerTasks = [];
          state.taskManagerTasks.unshift(task);
        });
        sendJson(res, 200, ok({ task }));
        return;
      }

      const tmTaskMatch = path.match(/^\\/api\\/task-manager\\/tasks\\/([^/]+)$/);
      if (tmTaskMatch && method === "PATCH") {
        const taskId = decodeURIComponent(tmTaskMatch[1]);
        setRequestContextFields({ operation: "task-manager.tasks.update" });
        const body = await readJson(req);
        if (!body) { sendJson(res, 400, fail("INVALID_JSON", "Invalid JSON")); return; }
        const validStatuses = ["todo","in_progress","done","blocked"];
        const validPriorities = ["low","normal","high","urgent"];
        let updated = null;
        await store.mutate((state) => {
          if (!Array.isArray(state.taskManagerTasks)) { state.taskManagerTasks = []; return; }
          const idx = state.taskManagerTasks.findIndex((t) => t.id === taskId);
          if (idx === -1) return;
          const t = state.taskManagerTasks[idx];
          state.taskManagerTasks[idx] = {
            ...t,
            title: typeof body.title === "string" && body.title.trim() ? body.title.trim() : t.title,
            description: typeof body.description === "string" ? (body.description.trim() || null) : t.description,
            status: validStatuses.includes(body.status) ? body.status : t.status,
            priority: validPriorities.includes(body.priority) ? body.priority : t.priority,
            assignee: typeof body.assignee === "string" ? (body.assignee.trim() || null) : t.assignee,
            dueDate: typeof body.dueDate === "string" ? (body.dueDate.trim() || null) : t.dueDate,
            tags: Array.isArray(body.tags) ? body.tags.filter((x) => typeof x === "string") : t.tags,
            updatedAt: nowIso(),
          };
          updated = state.taskManagerTasks[idx];
        });
        if (!updated) { sendJson(res, 404, fail("NOT_FOUND", "Task not found")); return; }
        sendJson(res, 200, ok({ task: updated }));
        return;
      }

      if (tmTaskMatch && method === "DELETE") {
        const taskId = decodeURIComponent(tmTaskMatch[1]);
        setRequestContextFields({ operation: "task-manager.tasks.delete" });
        let removed = false;
        await store.mutate((state) => {
          if (!Array.isArray(state.taskManagerTasks)) { state.taskManagerTasks = []; return; }
          const before = state.taskManagerTasks.length;
          state.taskManagerTasks = state.taskManagerTasks.filter((t) => t.id !== taskId);
          removed = state.taskManagerTasks.length !== before;
        });
        if (!removed) { sendJson(res, 404, fail("NOT_FOUND", "Task not found")); return; }
        sendJson(res, 200, ok({ deleted: true }));
        return;
      }

      // -----------------------------------------------------------------
      // Ops Jobs — Archive
      // -----------------------------------------------------------------

      const opsJobArchiveMatch = path.match(/^\\/api\\/ops\\/jobs\\/([^/]+)\\/archive$/);
      if (opsJobArchiveMatch && method === "PATCH") {
        const jobId = decodeURIComponent(opsJobArchiveMatch[1]);
        setRequestContextFields({ operation: "ops.jobs.archive" });
        let updated = null;
        await store.mutate((state) => {
          if (!state.ops || !Array.isArray(state.ops.jobs)) return;
          const idx = state.ops.jobs.findIndex((j) => j.id === jobId);
          if (idx === -1) return;
          state.ops.jobs[idx] = { ...state.ops.jobs[idx], status: "archived", archivedAt: nowIso(), archivedBy: actor.id, updatedAt: nowIso() };
          updated = state.ops.jobs[idx];
        });
        if (!updated) { sendJson(res, 404, fail("NOT_FOUND", "Job not found")); return; }
        sendJson(res, 200, ok({ job: updated }));
        return;
      }

      // Catch-all: no route matched
      sendJson(res, 404, fail("NOT_FOUND", "Endpoint not found", { path, method }));'''

if CATCH_ALL in server:
    server = server.replace(CATCH_ALL, NEW_ROUTES)
    print("ROUTES: inserted task-manager + ops-archive handlers")
else:
    print("ROUTES: catch-all anchor not found - aborting")
    exit(1)

# ============================================================================
# 4. Check if rootAppStore has a .mutate() method (it might be read-only getState)
#    Let's check what methods it exposes, then we'll adapt if needed.
# ============================================================================

with open(SERVER_PATH, "w") as f:
    f.write(server)

print("Done - file written.")
