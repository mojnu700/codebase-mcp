import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

const browserSmokeIsolatedEnv =
  process.env.CONTROL_BROWSER_SMOKE_ISOLATED_ENV === "1";

export default defineConfig({
  // Playwright harnesses set this so repo-root `.env` / `.env.production` do not leak into the dev server.
  ...(browserSmokeIsolatedEnv
    ? { envDir: path.resolve(__dirname, "scripts/e2e/empty-vite-env") }
    : {}),
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src")
    }
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: [],
    coverage: {
      provider: "v8",
      include: ["src/lib/**/*.ts", "src/app/store/**/*.ts"],
      exclude: ["src/lib/demo-data.ts", "src/lib/fake-backend.ts"],
    },
  },
  build: {
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) {
            return;
          }

          if (id.includes("ag-grid")) {
            return "vendor-ag-grid";
          }

          if (id.includes("recharts")) {
            return "vendor-recharts";
          }

          return;
        }
      }
    }
  },
  server: {
    port: 1420,
    strictPort: true,
    host: "127.0.0.1"
  },
  clearScreen: false
});
