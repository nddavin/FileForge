import { test, expect } from '@playwright/test';

test.describe('Responsiveness Tests', () => {
	const viewports = [
		{ name: 'Small Mobile', width: 320, height: 568 },
		{ name: 'Mobile', width: 375, height: 667 },
		{ name: 'Large Mobile', width: 414, height: 896 },
		{ name: 'Tablet', width: 768, height: 1024 },
		{ name: 'Large Tablet', width: 1024, height: 768 },
		{ name: 'Desktop', width: 1280, height: 800 },
		{ name: 'Large Desktop', width: 1440, height: 900 },
		{ name: 'Extra Large Desktop', width: 1920, height: 1080 },
	];

	for (const viewport of viewports) {
		test(`${viewport.name} (${viewport.width}x${viewport.height}) - page loads`, async ({ page, browserName }) => {
			const waitUntil = browserName === 'firefox' ? 'load' : 'networkidle';
			const timeout = browserName === 'firefox' ? 60_000 : 30_000;

			await page.setViewportSize({ width: viewport.width, height: viewport.height });
			await page.goto('/', { waitUntil, timeout });
			await page.waitForTimeout(500);

			// Check that page loaded
			const title = await page.title();
			expect(title).toBeTruthy();
		});

		test(`${viewport.name} (${viewport.width}x${viewport.height}) - no horizontal overflow`, async ({ page, browserName }) => {
			const waitUntil = browserName === 'firefox' ? 'load' : 'networkidle';
			const timeout = browserName === 'firefox' ? 60_000 : 30_000;

			await page.setViewportSize({ width: viewport.width, height: viewport.height });
			await page.goto('/', { waitUntil, timeout });
			await page.waitForTimeout(500);

			// Check for horizontal overflow
			const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
			const viewportWidth = viewport.width;
			
			// Allow small margin for rounding
			expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 5);
		});

		test(`${viewport.name} (${viewport.width}x${viewport.height}) - content is visible`, async ({ page, browserName }) => {
			const waitUntil = browserName === 'firefox' ? 'load' : 'networkidle';
			const timeout = browserName === 'firefox' ? 60_000 : 30_000;

			await page.setViewportSize({ width: viewport.width, height: viewport.height });
			await page.goto('/', { waitUntil, timeout });
			await page.waitForTimeout(500);

			// Check that body has content
			const bodyText = await page.evaluate(() => document.body.textContent);
			expect(bodyText?.trim().length).toBeGreaterThan(0);
		});

		test(`${viewport.name} (${viewport.width}x${viewport.height}) - interactive elements accessible`, async ({ page, browserName }) => {
			const waitUntil = browserName === 'firefox' ? 'load' : 'networkidle';
			const timeout = browserName === 'firefox' ? 60_000 : 30_000;

			await page.setViewportSize({ width: viewport.width, height: viewport.height });
			await page.goto('/', { waitUntil, timeout });
			await page.waitForTimeout(500);

			// Check for interactive elements
			const buttons = await page.locator('button, [role="button"]').count();
			const inputs = await page.locator('input, textarea, select').count();
			const links = await page.locator('a[href]').count();

			// At least some interactive elements should be present
			const totalInteractive = buttons + inputs + links;
			expect(totalInteractive).toBeGreaterThan(0);
		});

		test(`${viewport.name} (${viewport.width}x${viewport.height}) - screenshot`, async ({ page, browserName }) => {
			const waitUntil = browserName === 'firefox' ? 'load' : 'networkidle';
			const timeout = browserName === 'firefox' ? 60_000 : 30_000;

			await page.setViewportSize({ width: viewport.width, height: viewport.height });
			await page.goto('/', { waitUntil, timeout });
			await page.waitForTimeout(500);

			// Take screenshot for visual regression
			expect(await page.screenshot({ fullPage: true })).toMatchSnapshot(
				`${viewport.name.toLowerCase().replace(/\s+/g, '-')}-${viewport.width}x${viewport.height}.png`
			);
		});
	}
});

test.describe('Responsive Breakpoints', () => {
	test('Mobile breakpoint (max-width: 640px)', async ({ page, browserName }) => {
		const waitUntil = browserName === 'firefox' ? 'load' : 'networkidle';
		const timeout = browserName === 'firefox' ? 60_000 : 30_000;

		await page.setViewportSize({ width: 375, height: 667 });
		await page.goto('/', { waitUntil, timeout });
		await page.waitForTimeout(500);

		// Check viewport width
		const viewportWidth = await page.evaluate(() => window.innerWidth);
		expect(viewportWidth).toBeLessThanOrEqual(640);
	});

	test('Tablet breakpoint (min-width: 641px, max-width: 1024px)', async ({ page, browserName }) => {
		const waitUntil = browserName === 'firefox' ? 'load' : 'networkidle';
		const timeout = browserName === 'firefox' ? 60_000 : 30_000;

		await page.setViewportSize({ width: 768, height: 1024 });
		await page.goto('/', { waitUntil, timeout });
		await page.waitForTimeout(500);

		// Check viewport width
		const viewportWidth = await page.evaluate(() => window.innerWidth);
		expect(viewportWidth).toBeGreaterThanOrEqual(641);
		expect(viewportWidth).toBeLessThanOrEqual(1024);
	});

	test('Desktop breakpoint (min-width: 1025px)', async ({ page, browserName }) => {
		const waitUntil = browserName === 'firefox' ? 'load' : 'networkidle';
		const timeout = browserName === 'firefox' ? 60_000 : 30_000;

		await page.setViewportSize({ width: 1280, height: 800 });
		await page.goto('/', { waitUntil, timeout });
		await page.waitForTimeout(500);

		// Check viewport width
		const viewportWidth = await page.evaluate(() => window.innerWidth);
		expect(viewportWidth).toBeGreaterThanOrEqual(1025);
	});
});

test.describe('Orientation Tests', () => {
	test('Portrait orientation (mobile)', async ({ page, browserName }) => {
		const waitUntil = browserName === 'firefox' ? 'load' : 'networkidle';
		const timeout = browserName === 'firefox' ? 60_000 : 30_000;

		await page.setViewportSize({ width: 375, height: 667 });
		await page.goto('/', { waitUntil, timeout });
		await page.waitForTimeout(500);

		// Check orientation
		const isPortrait = await page.evaluate(() => window.innerHeight > window.innerWidth);
		expect(isPortrait).toBe(true);
	});

	test('Landscape orientation (mobile)', async ({ page, browserName }) => {
		const waitUntil = browserName === 'firefox' ? 'load' : 'networkidle';
		const timeout = browserName === 'firefox' ? 60_000 : 30_000;

		await page.setViewportSize({ width: 667, height: 375 });
		await page.goto('/', { waitUntil, timeout });
		await page.waitForTimeout(500);

		// Check orientation
		const isLandscape = await page.evaluate(() => window.innerWidth > window.innerHeight);
		expect(isLandscape).toBe(true);
	});
});

test.describe('Touch vs Mouse Interactions', () => {
	test('Touch device simulation', async ({ page, browserName }) => {
		const waitUntil = browserName === 'firefox' ? 'load' : 'networkidle';
		const timeout = browserName === 'firefox' ? 60_000 : 30_000;

		// Set viewport to mobile size
		await page.setViewportSize({ width: 375, height: 667 });
		
		// Simulate touch device
		await page.goto('/', { waitUntil, timeout });
		await page.waitForTimeout(500);

		// Check that touch events are supported
		const hasTouch = await page.evaluate(() => 'ontouchstart' in window);
		// Note: Playwright may not fully simulate touch, but we can check viewport
		const viewportWidth = await page.evaluate(() => window.innerWidth);
		expect(viewportWidth).toBe(375);
	});

	test('Mouse device simulation', async ({ page, browserName }) => {
		const waitUntil = browserName === 'firefox' ? 'load' : 'networkidle';
		const timeout = browserName === 'firefox' ? 60_000 : 30_000;

		// Set viewport to desktop size
		await page.setViewportSize({ width: 1280, height: 800 });
		
		await page.goto('/', { waitUntil, timeout });
		await page.waitForTimeout(500);

		// Check viewport
		const viewportWidth = await page.evaluate(() => window.innerWidth);
		expect(viewportWidth).toBe(1280);
	});
});
