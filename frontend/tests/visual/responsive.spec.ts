import { test, expect } from '@playwright/test';

test.describe('Responsive Layout', () => {
	test('desktop layout renders correctly', async ({ page, browserName }) => {
		const waitUntil = browserName === 'firefox' ? 'load' : 'networkidle';
		const timeout = browserName === 'firefox' ? 60_000 : 30_000;
		
		await page.setViewportSize({ width: 1280, height: 800 });
		await page.goto('/', { waitUntil, timeout });
		await page.waitForTimeout(500);
		
		// Check that page has content
		const body = page.locator('body');
		await expect(body).toBeVisible();
		
		// Take screenshot for visual regression
		expect(await page.screenshot({ fullPage: true })).toMatchSnapshot('desktop-layout.png');
	});

	test('tablet layout renders correctly', async ({ page, browserName }) => {
		const waitUntil = browserName === 'firefox' ? 'load' : 'networkidle';
		const timeout = browserName === 'firefox' ? 60_000 : 30_000;
		
		await page.setViewportSize({ width: 768, height: 1024 });
		await page.goto('/', { waitUntil, timeout });
		await page.waitForTimeout(500);
		
		// Check that page has content
		const body = page.locator('body');
		await expect(body).toBeVisible();
		
		// Take screenshot for visual regression
		expect(await page.screenshot({ fullPage: true })).toMatchSnapshot('tablet-layout.png');
	});

	test('mobile layout renders correctly', async ({ page, browserName }) => {
		const waitUntil = browserName === 'firefox' ? 'load' : 'networkidle';
		const timeout = browserName === 'firefox' ? 60_000 : 30_000;
		
		await page.setViewportSize({ width: 375, height: 667 });
		await page.goto('/', { waitUntil, timeout });
		await page.waitForTimeout(500);
		
		// Check that page has content
		const body = page.locator('body');
		await expect(body).toBeVisible();
		
		// Take screenshot for visual regression
		expect(await page.screenshot({ fullPage: true })).toMatchSnapshot('mobile-layout.png');
	});

	test('large desktop layout renders correctly', async ({ page, browserName }) => {
		const waitUntil = browserName === 'firefox' ? 'load' : 'networkidle';
		const timeout = browserName === 'firefox' ? 60_000 : 30_000;
		
		await page.setViewportSize({ width: 1920, height: 1080 });
		await page.goto('/', { waitUntil, timeout });
		await page.waitForTimeout(500);
		
		// Check that page has content
		const body = page.locator('body');
		await expect(body).toBeVisible();
		
		// Take screenshot for visual regression
		expect(await page.screenshot({ fullPage: true })).toMatchSnapshot('large-desktop-layout.png');
	});
});
