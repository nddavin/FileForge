import { vi } from 'vitest';
import '@testing-library/jest-dom';
import '@testing-library/react';

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock ResizeObserver as a class with constructor
class MockResizeObserver {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}
global.ResizeObserver = MockResizeObserver;

// Mock Element.prototype.hasPointerCapture and releasePointerCapture
Object.defineProperty(Element.prototype, 'hasPointerCapture', {
  writable: true,
  value: vi.fn(() => false),
});

Object.defineProperty(Element.prototype, 'releasePointerCapture', {
  writable: true,
  value: vi.fn(() => true),
});

// Set up test timeout
vi.setConfig({ testTimeout: 10000 });

// Mock window.scrollTo
window.scrollTo = vi.fn();

// Mock floating-ui imports (used by radix-ui components)
vi.mock('@floating-ui/react-dom', () => ({
  useFloating: vi.fn(() => ({
    x: 0,
    y: 0,
    strategy: 'absolute',
    refs: {
      floating: { current: null },
      reference: { current: null },
    },
    update: vi.fn(),
  })),
  inline: vi.fn((fn) => fn),
}));

// Mock scrollIntoView for Radix UI components in jsdom
Element.prototype.scrollIntoView = vi.fn();

// Mock for candidate used by Radix UI Select
if (typeof HTMLSelectElement !== 'undefined') {
  Object.defineProperty(HTMLSelectElement.prototype, 'selectedOptions', {
    get: function() {
      return {
        length: 1,
        0: { value: 'sermons', text: 'Sermons', getAttribute: () => 'sermons' }
      };
    },
    configurable: true
  });
}
