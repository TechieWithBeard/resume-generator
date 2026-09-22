import { defineConfig, devices } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// Locate python executable (local virtual environment or system Python in CI)
const candidateVenvs = [
  path.resolve(__dirname, '../../../.venv/bin/python'),
  path.resolve(__dirname, '../.venv/bin/python'),
  path.resolve(__dirname, '../../.venv/bin/python'),
];
let pythonExec = process.env['PYTHON_CMD'] || (process.env['VIRTUAL_ENV'] ? `${process.env['VIRTUAL_ENV']}/bin/python` : '');

if (!pythonExec) {
  for (const candidate of candidateVenvs) {
    if (fs.existsSync(candidate)) {
      pythonExec = candidate;
      break;
    }
  }
}
if (!pythonExec) {
  pythonExec = 'python3';
}

const rootDir = path.resolve(__dirname, '..');

export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  fullyParallel: false,
  forbidOnly: !!process.env['CI'],
  retries: process.env['CI'] ? 1 : 0,
  workers: process.env['CI'] ? 1 : 1,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
  ],
  use: {
    baseURL: 'http://localhost:8000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: `cd "${rootDir}" && ${pythonExec} backend/run.py`,
    url: 'http://localhost:8000/api/health',
    reuseExistingServer: !process.env['CI'],
    timeout: 120_000,
  },
});
