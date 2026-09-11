import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./web-tests",
  fullyParallel: true,
  workers: 2,
  timeout: 90000,
  projects: [
    { name: "firefox", use: { browserName: "firefox" } },
    { name: "webkit", use: { browserName: "webkit" } },
    {
      name: "chromium",
      use: {
        browserName: "chromium",
      },
    },
  ],
  expect: { timeout: 10000 },
  use: {
    baseURL: "http://127.0.0.1:4173",
    trace: "on-first-retry",
  },
  webServer: {
    command: "python3 -m http.server 4173 --directory docs",
    url: "http://127.0.0.1:4173",
    reuseExistingServer: !process.env.CI,
  },
});
