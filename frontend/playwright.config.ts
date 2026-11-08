import { defineConfig, devices } from "@playwright/test";
import { randomBytes } from "node:crypto";
process.env.SAFETYLENS_E2E_PASSWORD ??= randomBytes(24).toString("hex");
process.env.DETECTOR_API_TOKEN ??= randomBytes(32).toString("hex");
process.env.DETECTOR_CAMERA_IDS = "cam-03";
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 45000,
  expect: { timeout: 15000 },
  reporter: [["list"], ["json", { outputFile: "test-results/results.json" }]],
  use: {
    baseURL: "http://127.0.0.1:3100",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "desktop", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: "../backend/.venv/bin/python ../scripts/e2e_backend.py",
      url: "http://127.0.0.1:8107/api/health",
      reuseExistingServer: false,
      timeout: 30000,
    },
    {
      command: "npm run dev -- --hostname 127.0.0.1 --port 3100",
      url: "http://127.0.0.1:3100",
      reuseExistingServer: false,
      timeout: 60000,
      env: {
        NEXT_PUBLIC_API_URL: "http://127.0.0.1:8107",
        NEXT_PUBLIC_DEMO_FALLBACK: "false",
        NEXT_TELEMETRY_DISABLED: "1",
        SAFETYLENS_DISABLE_BUILD_CACHE: "true",
      },
    },
  ],
});
