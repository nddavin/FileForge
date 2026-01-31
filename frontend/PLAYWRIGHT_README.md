Playwright visual tests

Quick start

1. Install dev dependency

   npm install -D @playwright/test

2. Start the dev server (defaults to port 5173)

   npm run dev

3. Run visual tests

   npm run test:visual

4. Update baseline snapshots after intentional changes

   npm run test:visual:update

Notes
- Tests expect the dev server running at http://localhost:5173. Adjust tests if you use a different port.
- Playwright snapshots are stored in the tests folder next to specs.
