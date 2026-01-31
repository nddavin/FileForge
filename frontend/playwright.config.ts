import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
	testDir: 'tests/visual',
	timeout: 30_000,
	expect: { timeout: 5000 },
	reporter: [['html', { open: 'never' }]],
	use: {
		headless: true,
		viewport: { width: 1280, height: 800 },
		actionTimeout: 5000,
		trace: 'retain-on-failure',
	},
	projects: [
		{ name: 'chromium', use: { ...devices['Desktop Chrome'] } },
		{ name: 'firefox', use: { ...devices['Desktop Firefox'] } },
		{ name: 'webkit', use: { ...devices['Desktop Safari'] } },
		// mobile viewport example
		{ name: 'mobile-chrome', use: { ...devices['Pixel 5'] } },
		{ name: 'mobile-safari', use: { ...devices['iPhone 12'] } },
	],
		snapshotDir: 'tests/visual/__snapshots__',
		webServer: {
			// use Vite dev server so Playwright tests the live app during development
			command: 'npm run dev -- --port 5173',
			port: 5173,
			timeout: 60_000,
			reuseExistingServer: true,
		},
});
