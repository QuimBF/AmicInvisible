const { defineConfig, devices } = require('@playwright/test')

const CI = !!process.env.CI
// Locally use the installed Google Chrome, so no browser download is needed.
const channel = CI ? undefined : 'chrome'

module.exports = defineConfig({
  testDir: 'e2e',
  forbidOnly: CI,
  reporter: CI ? [['list'], ['html', { open: 'never' }]] : 'list',
  use: { baseURL: 'http://127.0.0.1:4173/' },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'], channel } },
    { name: 'phone', use: { ...devices['Pixel 7'], channel } },
  ],
  webServer: {
    command: 'python3 publica.py _site && python3 -m http.server 4173 --bind 127.0.0.1 --directory _site 2>/dev/null',
    url: 'http://127.0.0.1:4173/',
    reuseExistingServer: !CI,
  },
})
