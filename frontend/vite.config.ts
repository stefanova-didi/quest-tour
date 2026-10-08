import { execSync } from "node:child_process";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

/** The build's version string, baked into the bundle as `__APP_VERSION__` (see src/lib/version.ts).
 *  CI and scripts/package-app.sh pass APP_VERSION so the SPA and the backend's VERSION file agree; a
 *  plain local build falls back to `git describe` (a tag such as v1.2.0, or v1.2.0-3-g6dd4e31 past
 *  it), then to "dev" when neither git nor a checkout is available. */
function appVersion(): string {
  const fromEnv = process.env.APP_VERSION?.trim();
  if (fromEnv) return fromEnv;
  try {
    const described = execSync("git describe --tags --always --dirty", { stdio: ["ignore", "pipe", "ignore"] });
    return described.toString().trim() || "dev";
  } catch {
    return "dev";
  }
}

export default defineConfig({
  plugins: [react()],
  define: { __APP_VERSION__: JSON.stringify(appVersion()) },
  server: { proxy: { "/api": process.env.DEV_API_TARGET ?? "http://localhost:8000" } },
  test: { environment: "jsdom", globals: true, setupFiles: ["./src/test/setup.ts"] },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id?.includes("/src/admin/")) {
            return "admin";
          }
          return null;
        },
      },
    },
  },
});
