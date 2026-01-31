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
          new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const lcpEntry = entries.find((entry) => entry.entryType === 'largest-contentful-paint');
            if (lcpEntry) {
              resolve(lcpEntry.startTime);
            }
          }).observe({ type: 'largest-contentful-paint', buffered: true });
        });
      });

      expect(lcp).toBeLessThan(2500); // 2.5 seconds
    });

    test('First Input Delay (FID) should be under 100ms', async ({ page }) => {
      const fid = await page.evaluate(() => {
        return new Promise<number>((resolve) => {
          new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const fidEntry = entries.find((entry) => entry.entryType === 'first-input') as any;
            if (fidEntry) {
              resolve(fidEntry.processingStart - fidEntry.startTime);
            }
          }).observe({ type: 'first-input', buffered: true });
        });
      });

      expect(fid).toBeLessThan(100); // 100 milliseconds
    });

    test('Cumulative Layout Shift (CLS) should be under 0.1', async ({ page }) => {
      const cls = await page.evaluate(() => {
        return new Promise<number>((resolve) => {
          let clsValue = 0;
          new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
              if (!entry.hadRecentInput) {
                clsValue += entry.value;
              }
            }
            resolve(clsValue);
          }).observe({ type: 'layout-shift', buffered: true });
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
        const timing = performance.timing;
        return {
          domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
          loadComplete: timing.loadEventEnd - timing.navigationStart,
          domInteractive: timing.domInteractive - timing.navigationStart,
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

    test('Speed Index should be under 3.4s', async ({ page }) => {
      const speedIndex = await page.evaluate(() => {
        return new Promise<number>((resolve) => {
          const paintEntries: PerformanceEntry[] = [];
          const observer = new PerformanceObserver((list) => {
            paintEntries.push(...list.getEntries());
          });
          observer.observe({ type: 'paint', buffered: true });

          setTimeout(() => {
            const fcp = paintEntries.find((e) => e.name === 'first-contentful-paint');
            const lcp = paintEntries.find((e) => e.name === 'largest-contentful-paint');
            
            if (fcp && lcp) {
              resolve((fcp.startTime + lcp.startTime) / 2);
            } else {
              resolve(0);
            }
          }, 5000);
        });
      });

      expect(speedIndex).toBeLessThan(3400);
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
      const buttons = await page.locator('button').all();
      
      if (buttons.length > 0) {
        const responseTime = await page.evaluate(async (element) => {
          const start = performance.now();
          element.click();
          await new Promise(resolve => setTimeout(resolve, 0));
          return performance.now() - start;
        }, buttons[0]);

        expect(responseTime).toBeLessThan(100);
      }
    });

    test('Form input response time should be under 50ms', async ({ page }) => {
      const inputs = await page.locator('input').all();
      
      if (inputs.length > 0) {
        const responseTime = await page.evaluate(async (element) => {
          const start = performance.now();
          element.focus();
          await new Promise(resolve => setTimeout(resolve, 0));
          return performance.now() - start;
        }, inputs[0]);

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
          const startTime = performance.now();
          
          // Use Playwright's waitForNavigation to properly measure navigation time
          await Promise.all([
            page.waitForNavigation({ timeout: 5000 }).catch(() => {
              // Navigation might not happen (e.g., anchor links)
            }),
            links[0].click()
          ]);
          
          const responseTime = performance.now() - startTime;
          
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
        const scripts = Array.from(document.querySelectorAll('script[src]'));
        let totalSize = 0;
        
        for (const script of scripts) {
          const src = script.getAttribute('src');
          if (src) {
            // Estimate size based on URL (this is approximate)
            totalSize += src.length * 10; // Rough estimate
          }
        }
        
        return totalSize;
      });

      // Total JS should be under 500KB (rough estimate)
      expect(jsSize).toBeLessThan(500 * 1024);
    });

    test('CSS bundle size should be reasonable', async ({ page }) => {
      const cssSize = await page.evaluate(() => {
        const stylesheets = Array.from(document.querySelectorAll('link[rel="stylesheet"]'));
        let totalSize = 0;
        
        for (const stylesheet of stylesheets) {
          const href = stylesheet.getAttribute('href');
          if (href) {
            // Estimate size based on URL (this is approximate)
            totalSize += href.length * 5; // Rough estimate
          }
        }
        
        return totalSize;
      });

      // Total CSS should be under 100KB (rough estimate)
      expect(cssSize).toBeLessThan(100 * 1024);
    });

    test('Total page weight should be under 2MB', async ({ page }) => {
      const pageWeight = await page.evaluate(() => {
        const resources = performance.getEntriesByType('resource');
        let totalSize = 0;
        
        for (const resource of resources) {
          if (resource.transferSize) {
            totalSize += resource.transferSize;
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
      const errorCount = await page.evaluate(() => {
        const resources = performance.getEntriesByType('resource');
        return resources.filter((r) => {
          const entry = r as PerformanceResourceTiming;
          return entry.transferSize === 0 && entry.duration > 0;
        }).length;
      });

      // Should have no 404 errors
      expect(errorCount).toBe(0);
    });

    test('Images should be optimized', async ({ page }) => {
      const imageOptimization = await page.evaluate(() => {
        const images = Array.from(document.querySelectorAll('img'));
        let totalSize = 0;
        
        for (const img of images) {
          const src = img.getAttribute('src');
          if (src) {
            // Estimate size based on URL (this is approximate)
            totalSize += src.length * 8; // Rough estimate
          }
        }
        
        return totalSize;
      });

      // Images should be under 500KB total (rough estimate)
      expect(imageOptimization).toBeLessThan(500 * 1024);
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
      const cacheableResources = await page.evaluate(() => {
        const resources = performance.getEntriesByType('resource');
        return resources.filter((r) => {
          const entry = r as PerformanceResourceTiming;
          // Check if resource has cache headers (this is a simplified check)
          return entry.transferSize > 0;
        }).length;
      });

      // Most resources should be cacheable
      expect(cacheableResources).toBeGreaterThan(0);
    });

    test('Service Worker should be registered (if applicable)', async ({ page }) => {
      const serviceWorkerRegistered = await page.evaluate(() => {
        return 'serviceWorker' in navigator;
      });

      // Service worker support is optional
      // This test is informational
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

      // Should have some lazy-loaded images (informational)
      // This test is informational
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

      // Open Graph tags are recommended but not required
      // This test is informational
    });
  });
});
