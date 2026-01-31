import { test, expect } from '@playwright/test';

test('home page visual snapshot', async ({ page }) => {
	await page.goto('/', { waitUntil: 'networkidle', timeout: 30_000 });
	// give the app a moment to paint
	await page.waitForTimeout(500);
	// take full page screenshot and compare with snapshot
	expect(await page.screenshot({ fullPage: true })).toMatchSnapshot('home-fullpage.png');
});
