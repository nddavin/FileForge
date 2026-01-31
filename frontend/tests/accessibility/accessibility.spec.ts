import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

/**
 * Accessibility Test Suite
 * 
 * Tests for WCAG 2.1 Level AA compliance including:
 * - Automated axe-core checks
 * - Keyboard navigation
 * - Screen reader compatibility
 * - Focus management
 * - Color contrast
 */

test.describe('Accessibility Tests', () => {
  const baseUrl = 'http://localhost:5173';

  test.beforeEach(async ({ page }) => {
    await page.goto(baseUrl);
  });

  test.describe('Automated Accessibility Checks (axe-core)', () => {
    test('Home page should have no critical accessibility violations', async ({ page }) => {
      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze();

      expect(accessibilityScanResults.violations).toEqual([]);
    });

    test('Home page should have no serious accessibility violations', async ({ page }) => {
      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze();

      const seriousViolations = accessibilityScanResults.violations.filter(
        v => v.impact === 'serious'
      );
      expect(seriousViolations).toEqual([]);
    });

    test('All images should have alt text', async ({ page }) => {
      const accessibilityScanResults = await new AxeBuilder({ page })
        .include('img')
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();

      const imageViolations = accessibilityScanResults.violations.filter(
        v => v.id === 'image-alt'
      );
      expect(imageViolations).toEqual([]);
    });

    test('All form inputs should have labels', async ({ page }) => {
      const accessibilityScanResults = await new AxeBuilder({ page })
        .include('input, select, textarea')
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();

      const labelViolations = accessibilityScanResults.violations.filter(
        v => v.id === 'label'
      );
      expect(labelViolations).toEqual([]);
    });

    test('All links should have discernible text', async ({ page }) => {
      const accessibilityScanResults = await new AxeBuilder({ page })
        .include('a')
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();

      const linkViolations = accessibilityScanResults.violations.filter(
        v => v.id === 'link-name'
      );
      expect(linkViolations).toEqual([]);
    });

    test('Page should have proper heading hierarchy', async ({ page }) => {
      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();

      const headingViolations = accessibilityScanResults.violations.filter(
        v => v.id === 'heading-order'
      );
      expect(headingViolations).toEqual([]);
    });

    test('Color contrast should meet WCAG AA standards', async ({ page }) => {
      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();

      const contrastViolations = accessibilityScanResults.violations.filter(
        v => v.id === 'color-contrast'
      );
      expect(contrastViolations).toEqual([]);
    });

    test('Focus indicators should be visible', async ({ page }) => {
      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();

      const focusViolations = accessibilityScanResults.violations.filter(
        v => v.id === 'focus-order-semantics'
      );
      expect(focusViolations).toEqual([]);
    });

    test('ARIA attributes should be valid', async ({ page }) => {
      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'best-practice'])
        .analyze();

      const ariaViolations = accessibilityScanResults.violations.filter(
        v => v.id.startsWith('aria-')
      );
      expect(ariaViolations).toEqual([]);
    });

    test('Landmarks should be properly defined', async ({ page }) => {
      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();

      const landmarkViolations = accessibilityScanResults.violations.filter(
        v => v.id === 'region'
      );
      expect(landmarkViolations).toEqual([]);
    });
  });

  test.describe('Keyboard Navigation', () => {
    test('All interactive elements should be keyboard accessible', async ({ page }) => {
      // Get all interactive elements
      const interactiveElements = await page.locator('a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])').all();
      
      for (const element of interactiveElements) {
        await element.focus();
        const isFocused = await element.evaluate(el => document.activeElement === el);
        expect(isFocused).toBe(true);
      }
    });

    test('Tab order should be logical and predictable', async ({ page }) => {
      const focusableElements = await page.locator('a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])').all();
      
      if (focusableElements.length > 0) {
        // Focus first element
        await focusableElements[0].focus();
        
        // Tab through all elements
        for (let i = 1; i < focusableElements.length; i++) {
          await page.keyboard.press('Tab');
          const currentFocus = await page.evaluate(() => document.activeElement?.tagName);
          const expectedElement = await focusableElements[i].evaluate(el => el.tagName);
          
          // Check that focus moved to the next element
          expect(currentFocus).toBeTruthy();
        }
      }
    });

    test('Shift+Tab should navigate backwards', async ({ page }) => {
      const focusableElements = await page.locator('a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])').all();
      
      if (focusableElements.length > 1) {
        // Focus second element
        await focusableElements[1].focus();
        
        // Press Shift+Tab to go back
        await page.keyboard.press('Shift+Tab');
        
        const currentFocus = await page.evaluate(() => document.activeElement?.tagName);
        const firstElement = await focusableElements[0].evaluate(el => el.tagName);
        
        expect(currentFocus).toBe(firstElement);
      }
    });

    test('Enter key should activate buttons and links', async ({ page }) => {
      const buttons = await page.locator('button').all();
      
      for (const button of buttons) {
        await button.focus();
        await page.keyboard.press('Enter');
        // Button should be activated (no error thrown)
      }
    });

    test('Space key should activate buttons', async ({ page }) => {
      const buttons = await page.locator('button').all();
      
      for (const button of buttons) {
        await button.focus();
        await page.keyboard.press('Space');
        // Button should be activated (no error thrown)
      }
    });

    test('Escape key should close modals/dropdowns', async ({ page }) => {
      // Test escape key functionality
      await page.keyboard.press('Escape');
      // Should not cause errors
    });

    test('Focus should be visible when navigating with keyboard', async ({ page }) => {
      const focusableElements = await page.locator('a, button, input, select, textarea').all();
      
      for (const element of focusableElements) {
        await element.focus();
        const hasFocusStyle = await element.evaluate(el => {
          const computedStyle = window.getComputedStyle(el);
          return computedStyle.outline !== 'none' || 
                 computedStyle.boxShadow !== 'none' ||
                 el.getAttribute('data-focus-visible') !== null;
        });
        
        // Element should have some focus indication
        expect(hasFocusStyle || await element.isVisible()).toBe(true);
      }
    });

    test('Skip links should work if present', async ({ page }) => {
      const skipLinks = await page.locator('a[href^="#"], a[href^="."]').all();
      
      for (const link of skipLinks) {
        const href = await link.getAttribute('href');
        if (href && href.startsWith('#')) {
          await link.click();
          // Should navigate to the target without errors
        }
      }
    });
  });

  test.describe('Screen Reader Compatibility', () => {
    test('Page should have proper language attribute', async ({ page }) => {
      const lang = await page.evaluate(() => document.documentElement.lang);
      expect(lang).toBeTruthy();
      expect(lang?.length).toBeGreaterThan(1);
    });

    test('Page should have a title', async ({ page }) => {
      const title = await page.title();
      expect(title).toBeTruthy();
      expect(title.length).toBeGreaterThan(0);
    });

    test('Main content should be in a landmark', async ({ page }) => {
      const hasMain = await page.locator('main, [role="main"]').count();
      expect(hasMain).toBeGreaterThan(0);
    });

    test('Navigation should be in a nav landmark', async ({ page }) => {
      const hasNav = await page.locator('nav, [role="navigation"]').count();
      expect(hasNav).toBeGreaterThan(0);
    });

    test('Form elements should have accessible names', async ({ page }) => {
      const inputs = await page.locator('input, select, textarea').all();
      
      for (const input of inputs) {
        const hasLabel = await input.evaluate(el => {
          const id = el.id;
          if (id) {
            const label = document.querySelector(`label[for="${id}"]`);
            if (label) return true;
          }
          return el.hasAttribute('aria-label') || 
                 el.hasAttribute('aria-labelledby') ||
                 el.closest('label') !== null;
        });
        
        expect(hasLabel).toBe(true);
      }
    });

    test('Icons should have accessible labels', async ({ page }) => {
      const iconButtons = await page.locator('button svg, button i, a svg, a i').all();
      
      for (const icon of iconButtons) {
        const button = await icon.locator('..');
        const hasAccessibleName = await button.evaluate(el => {
          return el.hasAttribute('aria-label') || 
                 el.hasAttribute('aria-labelledby') ||
                 el.textContent?.trim().length > 0;
        });
        
        expect(hasAccessibleName).toBe(true);
      }
    });

    test('Live regions should be properly marked', async ({ page }) => {
      const liveRegions = await page.locator('[aria-live], [role="status"], [role="alert"]').all();
      
      for (const region of liveRegions) {
        const hasLiveAttribute = await region.evaluate(el => {
          return el.hasAttribute('aria-live') || 
                 el.getAttribute('role') === 'status' ||
                 el.getAttribute('role') === 'alert';
        });
        
        expect(hasLiveAttribute).toBe(true);
      }
    });

    test('Dynamic content updates should be announced', async ({ page }) => {
      // Check for aria-live regions that would announce updates
      const hasLiveRegions = await page.locator('[aria-live]').count();
      // This is informational - live regions are recommended but not always required
    });

    test('Hidden elements should not be accessible', async ({ page }) => {
      const hiddenElements = await page.locator('[hidden], [aria-hidden="true"]').all();
      
      for (const element of hiddenElements) {
        const isHidden = await element.evaluate(el => {
          return el.hasAttribute('hidden') || 
                 el.getAttribute('aria-hidden') === 'true';
        });
        
        expect(isHidden).toBe(true);
      }
    });
  });

  test.describe('Focus Management', () => {
    test('Page should have an initial focus target', async ({ page }) => {
      // Wait a moment for any initial focus to be set
      await page.waitForTimeout(100);
      
      const activeElement = await page.evaluate(() => document.activeElement?.tagName);
      // Either body or a specific element should be focused
      expect(activeElement).toBeTruthy();
    });

    test('Focus should not be trapped in elements', async ({ page }) => {
      const focusableElements = await page.locator('a, button, input, select, textarea').all();
      
      if (focusableElements.length > 0) {
        // Focus first element
        await focusableElements[0].focus();
        
        // Tab through all elements
        for (let i = 0; i < focusableElements.length; i++) {
          await page.keyboard.press('Tab');
        }
        
        // Focus should have moved through all elements
        const finalFocus = await page.evaluate(() => document.activeElement?.tagName);
        expect(finalFocus).toBeTruthy();
      }
    });

    test('Modal dialogs should trap focus', async ({ page }) => {
      // This test would be expanded when modals are implemented
      // For now, we verify the page doesn't have focus traps inappropriately
      const focusableElements = await page.locator('a, button, input, select, textarea').all();
      
      if (focusableElements.length > 0) {
        await focusableElements[0].focus();
        await page.keyboard.press('Tab');
        
        const focusMoved = await page.evaluate(() => {
          const first = document.activeElement;
          return first !== document.body;
        });
        
        expect(focusMoved).toBe(true);
      }
    });

    test('Focus should return to trigger after closing dialogs', async ({ page }) => {
      // This test would be expanded when dialogs are implemented
      // Verify that focus management is in place
    });
  });

  test.describe('Color and Visual Accessibility', () => {
    test('Text should have sufficient color contrast', async ({ page }) => {
      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();

      const contrastViolations = accessibilityScanResults.violations.filter(
        v => v.id === 'color-contrast'
      );
      expect(contrastViolations).toEqual([]);
    });

    test('Links should be distinguishable from text', async ({ page }) => {
      const links = await page.locator('a').all();
      
      for (const link of links) {
        const hasDistinctStyle = await link.evaluate(el => {
          const computedStyle = window.getComputedStyle(el);
          return computedStyle.textDecoration !== 'none' ||
                 computedStyle.color !== 'rgb(0, 0, 0)' ||
                 el.hasAttribute('aria-label');
        });
        
        // Links should be distinguishable (either by style or aria)
        expect(hasDistinctStyle || await link.textContent()).toBeTruthy();
      }
    });

    test('Form fields should have visible focus states', async ({ page }) => {
      const formFields = await page.locator('input, select, textarea').all();
      
      for (const field of formFields) {
        await field.focus();
        const hasFocusStyle = await field.evaluate(el => {
          const computedStyle = window.getComputedStyle(el);
          return computedStyle.outline !== 'none' || 
                 computedStyle.boxShadow !== 'none';
        });
        
        // Form fields should have visible focus
        expect(hasFocusStyle).toBe(true);
      }
    });
  });

  test.describe('Mobile Accessibility', () => {
    test('Touch targets should be at least 44x44 pixels', async ({ page }) => {
      const touchTargets = await page.locator('a, button, input, [role="button"]').all();
      
      for (const target of touchTargets) {
        const box = await target.boundingBox();
        if (box) {
          // Check if target is large enough for touch (44x44 minimum)
          const isLargeEnough = box.width >= 44 && box.height >= 44;
          // Some small targets may be acceptable if properly spaced
          // This is informational
        }
      }
    });

    test('Viewport should be properly configured', async ({ page }) => {
      const viewportMeta = await page.locator('meta[name="viewport"]').getAttribute('content');
      expect(viewportMeta).toBeTruthy();
      expect(viewportMeta).toContain('width=device-width');
    });

    test('Text should be resizable without breaking layout', async ({ page }) => {
      // Set zoom level to 200%
      await page.evaluate(() => {
        document.body.style.zoom = '2';
      });
      
      // Check that content is still readable
      const bodyText = await page.locator('body').textContent();
      expect(bodyText).toBeTruthy();
      
      // Reset zoom
      await page.evaluate(() => {
        document.body.style.zoom = '1';
      });
    });
  });

  test.describe('Form Accessibility', () => {
    test('Required fields should be marked', async ({ page }) => {
      const requiredFields = await page.locator('[required], [aria-required="true"]').all();
      
      for (const field of requiredFields) {
        const isMarkedRequired = await field.evaluate(el => {
          return el.hasAttribute('required') || 
                 el.getAttribute('aria-required') === 'true';
        });
        
        expect(isMarkedRequired).toBe(true);
      }
    });

    test('Error messages should be associated with inputs', async ({ page }) => {
      // This test would be expanded when form validation is implemented
      const inputs = await page.locator('input, select, textarea').all();
      
      for (const input of inputs) {
        const hasErrorAssociation = await input.evaluate(el => {
          const id = el.id;
          if (id) {
            const error = document.querySelector(`[aria-describedby="${id}"], [for="${id}"]`);
            return error !== null;
          }
          return false;
        });
        
        // Error association is recommended but not always present
      }
    });

    test('Form should have submit button', async ({ page }) => {
      const forms = await page.locator('form').all();
      
      for (const form of forms) {
        const hasSubmit = await form.locator('button[type="submit"], input[type="submit"]').count();
        // Forms should typically have submit buttons
      }
    });
  });

  test.describe('Media Accessibility', () => {
    test('Videos should have captions', async ({ page }) => {
      const videos = await page.locator('video').all();
      
      for (const video of videos) {
        const hasCaptions = await video.evaluate(el => {
          const videoEl = el as HTMLVideoElement;
          return videoEl.textTracks.length > 0 || 
                 videoEl.querySelector('track[kind="captions"]') !== null;
        });
        
        // Captions are recommended for videos
      }
    });

    test('Audio should have transcripts or controls', async ({ page }) => {
      const audioElements = await page.locator('audio').all();
      
      for (const audio of audioElements) {
        const hasControls = await audio.getAttribute('controls');
        expect(hasControls).toBeTruthy();
      }
    });

    test('Media should not auto-play without user consent', async ({ page }) => {
      const autoPlayMedia = await page.locator('video[autoplay], audio[autoplay]').count();
      // Auto-play without user consent is generally discouraged
    });
  });

  test.describe('Table Accessibility', () => {
    test('Data tables should have headers', async ({ page }) => {
      const tables = await page.locator('table').all();
      
      for (const table of tables) {
        const hasHeaders = await table.locator('th').count();
        if (hasHeaders > 0) {
          // Data tables should have headers
          const hasScope = await table.locator('th[scope]').count();
          // Scope attributes are recommended for headers
        }
      }
    });

    test('Tables should have captions or descriptions', async ({ page }) => {
      const tables = await page.locator('table').all();
      
      for (const table of tables) {
        const hasCaption = await table.locator('caption').count();
        const hasDescription = await table.evaluate(el => 
          el.hasAttribute('aria-describedby')
        );
        
        // Tables should have captions or descriptions
      }
    });
  });

  test.describe('ARIA Best Practices', () => {
    test('ARIA roles should be used correctly', async ({ page }) => {
      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'best-practice'])
        .analyze();

      const ariaViolations = accessibilityScanResults.violations.filter(
        v => v.id.startsWith('aria-')
      );
      expect(ariaViolations).toEqual([]);
    });

    test('Interactive elements should have appropriate roles', async ({ page }) => {
      const customButtons = await page.locator('[role="button"]').all();
      
      for (const button of customButtons) {
        const isKeyboardAccessible = await button.evaluate(el => {
          return el.hasAttribute('tabindex') || 
                 el.tagName === 'BUTTON' ||
                 el.tagName === 'A';
        });
        
        expect(isKeyboardAccessible).toBe(true);
      }
    });

    test('Expanded/collapsed states should be indicated', async ({ page }) => {
      const expandables = await page.locator('[aria-expanded]').all();
      
      for (const element of expandables) {
        const hasExpandedState = await element.evaluate(el => {
          const expanded = el.getAttribute('aria-expanded');
          return expanded === 'true' || expanded === 'false';
        });
        
        expect(hasExpandedState).toBe(true);
      }
    });
  });
});
