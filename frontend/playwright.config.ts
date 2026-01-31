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
	],
	snapshotsDir: 'tests/visual/__snapshots__',
});
