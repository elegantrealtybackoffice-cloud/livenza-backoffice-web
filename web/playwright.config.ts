import { defineConfig, devices } from '@playwright/test'

const externalBase = process.env.PLAYWRIGHT_BASE_URL

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  expect: { timeout: 8_000 },
  use: { baseURL: externalBase ?? 'http://127.0.0.1:3000', trace: 'retain-on-failure' },
  webServer: externalBase ? undefined : {
    command: 'npm run dev',
    url: 'http://127.0.0.1:3000',
    reuseExistingServer: true,
    env: { ...process.env, LIVENZA_API_ORIGIN: process.env.LIVENZA_API_ORIGIN ?? 'http://127.0.0.1:5000' },
  },
  projects: [
    { name: 'mobile', use: { ...devices['Pixel 7'] } },
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
  ],
})
