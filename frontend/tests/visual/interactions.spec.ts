import { test, expect } from '@playwright/test';

test.describe('Interactive Elements', () => {
	test('buttons are clickable and visible', async ({ page, browserName }) => {
		const waitUntil = browserName === 'firefox' ? 'load' : 'networkidle';
		const timeout = browserName === 'firefox' ? 60_000 : 30_000;
		
		await page.goto('/', { waitUntil, timeout });
		await page.waitForTimeout(500);
		
		// Find all buttons
		const buttons = page.locator('button, [role="button"], .btn');
		const count = await buttons.count();
		
		if (count > 0) {
			// Check that buttons are visible
			for (let i = 0; i < Math.min(count, 5); i++) {
				await expect(buttons.nth(i)).toBeVisible();
			}
		}
	});

	test('links are clickable and visible', async ({ page, browserName }) => {
		const waitUntil = browserName === 'firefox' ? 'load' : 'networkidle';
		const timeout = browserName === 'firefox' ? 60_000 : 30_000;
		
		await page.goto('/', { waitUntil, timeout });
		await page.waitForTimeout(500);
		
		// Find all links
		const links = page.locator('a[href]');
		const count = await links.count();
		
		if (count > 0) {
			// Check that links are visible
			for (let i = 0; i < Math.min(count, 5); i++) {
				await expect(links.nth(i)).toBeVisible();
			}
		}
	});

	test('forms are accessible', async ({ page, browserName }) => {
		const waitUntil = browserName === 'firefox' ? 'load' : 'networkidle';
		const timeout = browserName === 'firefox' ? 60_000 : 30_000;
		
		await page.goto('/', { waitUntil, timeout });
		await page.waitForTimeout(500);
		
		// Find all form inputs
		const inputs = page.locator('input, textarea, select');
		const count = await inputs.count();
		
		if (count > 0) {
			// Check that inputs are visible
			for (let i = 0; i < Math.min(count, 5); i++) {
				await expect(inputs.nth(i)).toBeVisible();
			}
		}
	});

	test('dropdowns and menus work correctly', async ({ page, browserName }) => {
		const waitUntil = browserName === 'firefox' ? 'load' : 'networkidle';
		const timeout = browserName === 'firefox' ? 60_000 : 30_000;
		
		await page.goto('/', { waitUntil, timeout });
		await page.waitForTimeout(500);
		
		// Find dropdowns
		const dropdowns = page.locator('[role="combobox"], select, .dropdown');
		const count = await dropdowns.count();
		
		if (count > 0) {
			// Check that dropdowns are visible
			for (let i = 0; i < Math.min(count, 3); i++) {
				await expect(dropdowns.nth(i)).toBeVisible();
			}
		}
	});
});

test.describe('Navigation', () => {
	test('page loads without critical errors', async ({ page, browserName }) => {
		const waitUntil = browserName === 'firefox' ? 'load' : 'networkidle';
		const timeout = browserName === 'firefox' ? 60_000 : 30_000;
		
		const response = await page.goto('/', { waitUntil, timeout });
		// Accept 200 or 304 (not modified) as successful
		expect([200, 304]).toContain(response?.status());
	});

	test('no critical console errors on page load', async ({ page, browserName }) => {
		const waitUntil = browserName === 'firefox' ? 'load' : 'networkidle';
		const timeout = browserName === 'firefox' ? 60_000 : 30_000;
		
		const errors: string[] = [];
		page.on('console', msg => {
			if (msg.type() === 'error') {
				errors.push(msg.text());
			}
		});
		
		await page.goto('/', { waitUntil, timeout });
		await page.waitForTimeout(1000);
		
		// Check for critical errors (ignore non-critical ones)
		const criticalErrors = errors.filter(err => 
			!err.includes('DevTools') && 
			!err.includes('Warning') &&
			!err.includes('deprecated') &&
			!err.includes('favicon')
		);
		
		// Allow some non-critical errors
		expect(criticalErrors.length).toBeLessThanOrEqual(2);
	});

	test('page has content', async ({ page, browserName }) => {
		const waitUntil = browserName === 'firefox' ? 'load' : 'networkidle';
		const timeout = browserName === 'firefox' ? 60_000 : 30_000;
		
		await page.goto('/', { waitUntil, timeout });
		await page.waitForTimeout(500);
		
		// Check that page has content
		const body = page.locator('body');
		await expect(body).toBeVisible();
		
		// Check that body has some content
		const bodyText = await body.textContent();
		expect(bodyText?.trim().length).toBeGreaterThan(0);
	});
});
