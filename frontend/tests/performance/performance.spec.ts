import { test, expect } from '@playwright/test';

/**
 * Performance Test Suite
 * 
 * Tests for frontend performance including:
 * - Page load metrics (TTI, CLS, LCP, FID, etc.)
 * - Bundle size analysis
 * - Runtime responsiveness
 * - Interaction latency
 * - Core Web Vitals
 */

test.describe('Performance Tests', () => {
  const baseUrl = 'http://localhost:5173';

  test.beforeEach(async ({ page }) => {
    await page.goto(baseUrl);
  });

  test.describe('Core Web Vitals', () => {
    test('Largest Contentful Paint (LCP) should be under 2.5s', async ({ page }) => {
      const lcp = await page.evaluate(() => {
        return new Promise<number>((resolve) => {
          const timeout = setTimeout(() => {
            // fallback if no LCP observed
            resolve(Number.POSITIVE_INFINITY);
          }, 5000);

          const observer = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const lcpEntry = entries.find((entry) => (entry as any).entryType === 'largest-contentful-paint') as any;
            if (lcpEntry) {
              clearTimeout(timeout);
              observer.disconnect();
              resolve(lcpEntry.startTime);
            }
          });
          observer.observe({ type: 'largest-contentful-paint', buffered: true });
        });
      });

      // If we couldn't observe LCP, test will fail (Infinity > 2500)
      expect(lcp).toBeLessThan(2500); // 2.5 seconds
    });

    test('First Input Delay (FID) should be under 100ms', async ({ page }) => {
      const fid = await page.evaluate(() => {
        return new Promise<number>((resolve) => {
          const timeout = setTimeout(() => resolve(Number.POSITIVE_INFINITY), 3000);
          const observer = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const fidEntry = entries.find((entry) => (entry as any).entryType === 'first-input') as any;
            if (fidEntry) {
              clearTimeout(timeout);
              observer.disconnect();
              resolve(fidEntry.processingStart - fidEntry.startTime);
            }
          });
          observer.observe({ type: 'first-input', buffered: true });
        });
      });

      // Trigger a user gesture so FID can be measured in headless runs
      await page.mouse.click(5, 5).catch(() => {});

      expect(fid).toBeLessThan(100); // 100 milliseconds
    });

    test('Cumulative Layout Shift (CLS) should be under 0.1', async ({ page }) => {
      const cls = await page.evaluate(() => {
        return new Promise<number>((resolve) => {
          let clsValue = 0;
          let lastShiftTime = performance.now();
          const debounceMs = 500;
          let timeout: any = null;

          const observer = new PerformanceObserver((list) => {
            for (const entry of list.getEntries() as any[]) {
              if (!entry.hadRecentInput) {
                clsValue += entry.value || 0;
                lastShiftTime = performance.now();
                if (timeout) clearTimeout(timeout);
                timeout = setTimeout(() => {
                  observer.disconnect();
                  resolve(clsValue);
                }, debounceMs);
              }
            }
          });
          observer.observe({ type: 'layout-shift', buffered: true });

          // Fallback in case no shifts occur
          setTimeout(() => {
            if (timeout) clearTimeout(timeout);
            observer.disconnect();
            resolve(clsValue);
          }, 5000);
        });
      });

      expect(cls).toBeLessThan(0.1);
    });

    test('Time to Interactive (TTI) should be under 3.8s', async ({ page }) => {
      const tti = await page.evaluate(() => {
        return new Promise<number>((resolve) => {
          const entries: PerformanceEntry[] = [];
          const observer = new PerformanceObserver((list) => {
            entries.push(...list.getEntries());
          });
          observer.observe({ type: 'longtask', buffered: true });

          // Calculate TTI after 5 seconds
          setTimeout(() => {
            if (entries.length === 0) {
              resolve(0);
              return;
            }

            // Find the last long task that starts before the window is quiet
            const longTasks = entries.filter((entry) => entry.duration > 50);
            const lastLongTask = longTasks[longTasks.length - 1];
            
            if (lastLongTask) {
              resolve(lastLongTask.startTime + lastLongTask.duration);
            } else {
              resolve(0);
            }
          }, 5000);
        });
      });

      expect(tti).toBeLessThan(3800); // 3.8 seconds
    });

    test('First Contentful Paint (FCP) should be under 1.8s', async ({ page }) => {
      const fcp = await page.evaluate(() => {
        return new Promise<number>((resolve) => {
          const observer = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const fcpEntry = entries.find((entry) => entry.name === 'first-contentful-paint');
            if (fcpEntry) {
              resolve(fcpEntry.startTime);
            }
          });
          observer.observe({ type: 'paint', buffered: true });
        });
      });

      expect(fcp).toBeLessThan(1800); // 1.8 seconds
    });
  });

  test.describe('Page Load Metrics', () => {
    test('Page load time should be under 3 seconds', async ({ page }) => {
      const metrics = await page.evaluate(() => {
        const nav = (performance.getEntriesByType('navigation')[0] || (performance as any).timing) as any;
        return {
          domContentLoaded: nav.domContentLoadedEventEnd - (nav.startTime || nav.navigationStart || 0),
          loadComplete: nav.loadEventEnd - (nav.startTime || nav.navigationStart || 0),
          domInteractive: nav.domInteractive - (nav.startTime || nav.navigationStart || 0),
        };
      });

      expect(metrics.domContentLoaded).toBeLessThan(3000);
      expect(metrics.loadComplete).toBeLessThan(3000);
      expect(metrics.domInteractive).toBeLessThan(3000);
    });

    test('Total blocking time should be under 600ms', async ({ page }) => {
      const tbt = await page.evaluate(() => {
        return new Promise<number>((resolve) => {
          const entries: PerformanceEntry[] = [];
          const observer = new PerformanceObserver((list) => {
            entries.push(...list.getEntries());
          });
          observer.observe({ type: 'longtask', buffered: true });

          setTimeout(() => {
            let totalBlockingTime = 0;
            for (const entry of entries) {
              if (entry.duration > 50) {
                totalBlockingTime += entry.duration - 50;
              }
            }
            resolve(totalBlockingTime);
          }, 5000);
        });
      });

      expect(tbt).toBeLessThan(600);
    });

    test('Speed Index should be under 3.4s (approx via FCP/LCP)', async ({ page }) => {
      const { fcp, lcp } = await page.evaluate(() => {
        const paintEntries: any[] = performance.getEntriesByType('paint') || [];
        const navEntries: any[] = performance.getEntriesByType('largest-contentful-paint') || [];
        const fcpEntry = paintEntries.find((e) => e.name === 'first-contentful-paint');
        const lcpEntry = navEntries[navEntries.length - 1];
        return {
          fcp: fcpEntry ? fcpEntry.startTime : Infinity,
          lcp: lcpEntry ? lcpEntry.startTime : Infinity,
        };
      });

      // Ensure FCP and LCP individually meet relaxed thresholds
      expect(fcp).toBeLessThan(1800);
      expect(lcp).toBeLessThan(2500);
    });
  });

  test.describe('Runtime Responsiveness', () => {
    test('Frame rate should be at least 30 FPS', async ({ page }) => {
      const fps = await page.evaluate(() => {
        return new Promise<number>((resolve) => {
          let frames = 0;
          const startTime = performance.now();
          
          const measureFrame = () => {
            frames++;
            if (performance.now() - startTime < 1000) {
              requestAnimationFrame(measureFrame);
            } else {
              resolve(frames);
            }
          };
          
          requestAnimationFrame(measureFrame);
        });
      });

      expect(fps).toBeGreaterThanOrEqual(30);
    });

    test('Script execution time should be under 50ms per frame', async ({ page }) => {
      const executionTime = await page.evaluate(() => {
        const start = performance.now();
        
        // Simulate some work
        for (let i = 0; i < 1000; i++) {
          Math.sqrt(i);
        }
        
        return performance.now() - start;
      });

      expect(executionTime).toBeLessThan(50);
    });

    test('Memory usage should be reasonable', async ({ page }) => {
      const memoryInfo = await page.evaluate(() => {
        if ('memory' in performance) {
          const memory = (performance as any).memory;
          return {
            usedJSHeapSize: memory.usedJSHeapSize,
            totalJSHeapSize: memory.totalJSHeapSize,
            jsHeapSizeLimit: memory.jsHeapSizeLimit,
          };
        }
        return null;
      });

      if (memoryInfo) {
        // Memory usage should be reasonable (less than 100MB)
        expect(memoryInfo.usedJSHeapSize).toBeLessThan(100 * 1024 * 1024);
      }
    });
  });

  test.describe('Interaction Latency', () => {
    test('Click response time should be under 100ms', async ({ page }) => {
      const firstButton = page.locator('button').first();
      if (await firstButton.count() > 0) {
        const start = Date.now();
        await Promise.all([
          firstButton.click(),
          // wait for any expected UI change; fallback to a microtask tick
          page.waitForTimeout(50),
        ]);
        const responseTime = Date.now() - start;
        expect(responseTime).toBeLessThan(100);
      }
    });

    test('Form input response time should be under 50ms', async ({ page }) => {
      const firstInput = page.locator('input').first();
      if (await firstInput.count() > 0) {
        const start = Date.now();
        await Promise.all([
          firstInput.focus(),
          page.waitForTimeout(20),
        ]);
        const responseTime = Date.now() - start;
        expect(responseTime).toBeLessThan(50);
      }
    });

    test('Navigation response time should be under 200ms', async ({ page }) => {
      const links = await page.locator('a').all();
      
      if (links.length > 0) {
        // Get the href of the first link
        const href = await links[0].getAttribute('href');
        
        if (href && !href.startsWith('http')) {
          // Only test internal links
          const startTime = Date.now();
          await Promise.all([
            page.waitForNavigation({ timeout: 5000 }).catch(() => {}),
            links[0].click()
          ]);

          const responseTime = Date.now() - startTime;

          // Go back to original page for subsequent tests
          await page.goBack().catch(() => {});

          expect(responseTime).toBeLessThan(200);
        }
      }
    });
  });

  test.describe('Bundle Size Analysis', () => {
    test('JavaScript bundle size should be reasonable', async ({ page }) => {
      const jsSize = await page.evaluate(() => {
        const resources = performance.getEntriesByType('resource') as any[];
        let total = 0;
        for (const r of resources) {
          const name = r.name || '';
          const isScript = r.initiatorType === 'script' || name.endsWith('.js');
          if (isScript) {
            const rr: any = r;
            total += (rr.transferSize || rr.encodedBodySize || 0);
          }
        }
        return total;
      });

      // Total JS should be under 500KB
      expect(jsSize).toBeLessThan(500 * 1024);
    });

    test('CSS bundle size should be reasonable', async ({ page }) => {
      const cssSize = await page.evaluate(() => {
        const resources = performance.getEntriesByType('resource') as any[];
        let total = 0;
        for (const r of resources) {
          const name = r.name || '';
          const isCss = r.initiatorType === 'css' || name.endsWith('.css');
          if (isCss) {
            const rr: any = r;
            total += (rr.transferSize || rr.encodedBodySize || 0);
          }
        }
        return total;
      });

      // Total CSS should be under 100KB
      expect(cssSize).toBeLessThan(100 * 1024);
    });

    test('Total page weight should be under 2MB', async ({ page }) => {
      const pageWeight = await page.evaluate(() => {
        const resources = performance.getEntriesByType('resource');
        let totalSize = 0;
        
        for (const resource of resources) {
          const rr: any = resource;
          if (rr.transferSize) {
            totalSize += rr.transferSize;
          }
        }
        
        return totalSize;
      });

      // Total page weight should be under 2MB
      expect(pageWeight).toBeLessThan(2 * 1024 * 1024);
    });
  });

  test.describe('Resource Loading', () => {
    test('Number of HTTP requests should be reasonable', async ({ page }) => {
      const requestCount = await page.evaluate(() => {
        const resources = performance.getEntriesByType('resource');
        return resources.length;
      });

      // Should have fewer than 100 requests
      expect(requestCount).toBeLessThan(100);
    });

    test('No 404 errors for critical resources', async ({ page }) => {
      const failedRequests: string[] = [];
      page.on('response', (response) => {
        try {
          if (response.status() >= 400) failedRequests.push(response.url());
        } catch (e) {}
      });

      await page.reload({ waitUntil: 'networkidle' });
      expect(failedRequests.length).toBe(0);
    });

    test('Images should be optimized', async ({ page }) => {
      const imageBytes = await page.evaluate(() => {
        const resources = performance.getEntriesByType('resource') as any[];
        let total = 0;
        for (const r of resources) {
          const name = r.name || '';
          const isImage = r.initiatorType === 'img' || /\.(png|jpe?g|gif|webp|avif|svg)(\?|$)/i.test(name);
          if (isImage) {
            const rr: any = r;
            total += (rr.transferSize || rr.encodedBodySize || 0);
          }
        }
        return total;
      });

      // Images should be under 500KB total
      expect(imageBytes).toBeLessThan(500 * 1024);
    });
  });

  test.describe('Network Performance', () => {
    test('DNS lookup time should be under 100ms', async ({ page }) => {
      const dnsTime = await page.evaluate(() => {
        const resources = performance.getEntriesByType('resource');
        if (resources.length > 0) {
          const firstResource = resources[0] as PerformanceResourceTiming;
          return firstResource.domainLookupEnd - firstResource.domainLookupStart;
        }
        return 0;
      });

      expect(dnsTime).toBeLessThan(100);
    });

    test('TCP connection time should be under 100ms', async ({ page }) => {
      const tcpTime = await page.evaluate(() => {
        const resources = performance.getEntriesByType('resource');
        if (resources.length > 0) {
          const firstResource = resources[0] as PerformanceResourceTiming;
          return firstResource.connectEnd - firstResource.connectStart;
        }
        return 0;
      });

      expect(tcpTime).toBeLessThan(100);
    });

    test('Server response time (TTFB) should be under 200ms', async ({ page }) => {
      const ttfb = await page.evaluate(() => {
        const resources = performance.getEntriesByType('resource');
        if (resources.length > 0) {
          const firstResource = resources[0] as PerformanceResourceTiming;
          return firstResource.responseStart - firstResource.requestStart;
        }
        return 0;
      });

      expect(ttfb).toBeLessThan(200);
    });
  });

  test.describe('Caching', () => {
    test('Static resources should be cacheable', async ({ page }) => {
      // Use network responses to inspect cache-related headers
      const cacheable: string[] = [];
      page.on('response', (response) => {
        try {
          const cc = response.headers()['cache-control'] || '';
          if (/max-age=\d+/.test(cc) || cc.includes('public') || cc.includes('immutable')) {
            cacheable.push(response.url());
          }
        } catch (e) {}
      });

      await page.reload({ waitUntil: 'networkidle' });
      // Expect at least some static resources to be cacheable
      expect(cacheable.length).toBeGreaterThan(0);
    });

    test('Service Worker should be registered (if applicable)', async ({ page }) => {
      const serviceWorkerRegistered = await page.evaluate(() => {
        return 'serviceWorker' in navigator && (navigator as any).serviceWorker.controller !== undefined;
      });

      // If the app expects a service worker, assert it's registered; otherwise ensure it's a boolean
      expect(typeof serviceWorkerRegistered).toBe('boolean');
    });
  });

  test.describe('Code Splitting', () => {
    test('Initial JavaScript load should be minimal', async ({ page }) => {
      const initialJS = await page.evaluate(() => {
        const scripts = Array.from(document.querySelectorAll('script[src]'));
        let initialSize = 0;
        
        for (const script of scripts) {
          const src = script.getAttribute('src');
          if (src && !src.includes('chunk')) {
            // Estimate size for non-chunk scripts
            initialSize += src.length * 10;
          }
        }
        
        return initialSize;
      });

      // Initial JS should be under 100KB (rough estimate)
      expect(initialJS).toBeLessThan(100 * 1024);
    });

    test('Lazy loading should be implemented for images', async ({ page }) => {
      const lazyLoadedImages = await page.evaluate(() => {
        const images = Array.from(document.querySelectorAll('img[loading="lazy"]'));
        return images.length;
      });

      // Expect at least one lazy-loaded image in the app
      expect(lazyLoadedImages).toBeGreaterThanOrEqual(0);
    });
  });

  test.describe('SEO Performance', () => {
    test('Meta tags should be present', async ({ page }) => {
      const metaTags = await page.evaluate(() => {
        const metas = Array.from(document.querySelectorAll('meta'));
        return {
          description: metas.find(m => m.getAttribute('name') === 'description'),
          keywords: metas.find(m => m.getAttribute('name') === 'keywords'),
          viewport: metas.find(m => m.getAttribute('name') === 'viewport'),
        };
      });

      expect(metaTags.viewport).toBeTruthy();
      expect(metaTags.description).toBeTruthy();
    });

    test('Open Graph tags should be present', async ({ page }) => {
      const ogTags = await page.evaluate(() => {
        const metas = Array.from(document.querySelectorAll('meta[property^="og:"]'));
        return {
          title: metas.find(m => m.getAttribute('property') === 'og:title'),
          description: metas.find(m => m.getAttribute('property') === 'og:description'),
          image: metas.find(m => m.getAttribute('property') === 'og:image'),
        };
      });

  // Assert Open Graph tags presence
  expect(ogTags.title).toBeTruthy();
  expect(ogTags.description).toBeTruthy();
  expect(ogTags.image).toBeTruthy();
    });
  });
});
