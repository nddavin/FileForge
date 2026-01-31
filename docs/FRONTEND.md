# FileForge Frontend Documentation

## Overview

FileForge frontend is a **Vite** + **React 18** + **TypeScript** application. It provides a modern web interface for file management, smart sorting rules, and bulk operations.

## Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Vite | ^5.3.5 | Build tool and dev server |
| React | ^18.3.1 | UI component library |
| TypeScript | ^5.5.4 | Type safety |
| Tailwind CSS | ^3.4.7 | Styling |
| Radix UI | ^1.x | Headless UI components |
| Supabase | ^2.45.0 | Backend-as-a-Service (auth, database, storage) |
| React Query | - | Server state management |
| Zustand | - | Client state management |

## Project Structure

```
frontend/
├── Dockerfile              # Docker container configuration
├── index.html              # HTML entry point
├── nginx.conf              # Nginx configuration for production
├── package.json            # Dependencies and scripts
├── package-lock.json       # Locked dependency versions
├── postcss.config.mjs      # PostCSS configuration
├── vite.config.ts          # Vite configuration
├── playwright.config.ts    # E2E testing configuration
├── public/                 # Static assets
├── src/
│   ├── components/         # React components
│   │   ├── ui/             # Reusable UI components
│   │   ├── file-manager/   # File management components
│   │   └── workflow/       # Workflow components
│   ├── hooks/              # Custom React hooks
│   ├── lib/                # Utility libraries
│   │   ├── supabase.ts     # Supabase client
│   │   └── utils.ts        # Helper functions
│   ├── pages/              # Page components
│   ├── stores/             # Zustand state stores
│   ├── styles/             # Global styles
│   ├── types/              # TypeScript types
│   └── main.tsx            # Application entry point
└── tests/                  # Test files
```

## Key Components

### File Management

#### FileManager
Main dashboard for managing files with:
- File grid/list view
- Bulk operations
- Sorting and filtering
- Upload progress tracking

#### SmartSortingRules
UI for creating automatic sorting rules:
- Rule builder interface
- Condition editor
- Preview functionality

### State Management

#### Authentication
Uses Supabase Auth with:
- JWT token management
- Session persistence
- RBAC integration

#### File Store (Zustand)
```typescript
interface FileStore {
  files: File[];
  selectedFiles: string[];
  uploadProgress: Map<string, number>;
  // Actions
  uploadFile: (file: File) => Promise<void>;
  deleteFiles: (ids: string[]) => Promise<void>;
  toggleSelection: (id: string) => void;
}
```

## Environment Variables

Create `.env.local` file:

```bash
# Supabase
VITE_SUPABASE_URL=your-project-url
VITE_SUPABASE_ANON_KEY=your-anon-key

# API
VITE_API_URL=http://localhost:8000
```

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server (port 3000) |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run test` | Run unit tests (Vitest) |
| `npm run test:ui` | Run tests with UI |

## Development

### Running Locally

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:3000`

### Building for Production

```bash
npm run build
```

Output goes to `dist/` directory.

### Docker

```bash
# Build image
docker build -t fileforge-frontend .

# Run container
docker run -p 3000:80 fileforge-frontend
```

## Testing

### Unit Tests (Vitest)

```bash
npm run test           # Run tests
npm run test:ui        # Run with UI
```

### E2E Tests (Playwright)

```bash
npx playwright test    # Run E2E tests
```

## Code Style

- TypeScript strict mode
- React functional components with hooks
- Tailwind CSS for styling
- ESLint + Prettier for formatting

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

See project root LICENSE file.
