import { test, expect } from '@playwright/test';

test.describe('Visual regression - homepage', () => {
  test('homepage visual snapshot', async ({ page }) => {
    await page.goto('http://localhost:5173');
    await page.setViewportSize({ width: 1280, height: 800 });

    // Wait for main app element; adjust selector to match your app
    await page.waitForSelector('body');

    // DOM snapshot
    const html = await page.content();
    expect(html).toMatchSnapshot('home.dom.html');

    // Full page screenshot
    expect(await page.screenshot({ fullPage: true })).toMatchSnapshot('home.full.png');
  });
});
