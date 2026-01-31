import { test, expect } from '@playwright/test';

test('home page visual snapshot', async ({ page, browserName }) => {
	// Firefox has issues with networkidle, use load instead
	const waitUntil = browserName === 'firefox' ? 'load' : 'networkidle';
	const timeout = browserName === 'firefox' ? 60_000 : 30_000;
	await page.goto('/', { waitUntil, timeout });
	// give the app a moment to paint
	await page.waitForTimeout(500);
	// take full page screenshot and compare with snapshot
	expect(await page.screenshot({ fullPage: true })).toMatchSnapshot('home-fullpage.png');
});
