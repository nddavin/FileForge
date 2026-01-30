# FileForge Frontend Documentation

## Overview

FileForge is a sermon file management system built with **Next.js 16**, **React 18**, and **TypeScript**. The frontend provides a modern web interface for managing sermon files, organizing content with smart sorting rules, and handling bulk operations.

## Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | ^16.1.6 | React framework with SSR/SSG |
| React | 18.2.0 | UI component library |
| TypeScript | 5.9.3 | Type safety |
| Supabase | ^2.49.0 | Backend-as-a-Service (auth, database, storage) |
| Axios | ^1.6.3 | HTTP client |
| ESLint | ^9.39.2 | Code linting |

## Project Structure

```
frontend/
├── Dockerfile           # Docker container configuration
├── next.config.js       # Next.js configuration
├── package.json         # Dependencies and scripts
├── package-lock.json    # Locked dependency versions
├── public/              # Static assets
└── src/
    ├── __tests__/       # Unit and integration tests
    │   └── fileManager.test.tsx
    ├── app/             # Next.js App Router pages
    ├── components/      # React components
    │   ├── BulkOperationsBar.tsx
    │   ├── FileGrid.tsx
    │   ├── FileRelationshipMap.tsx
    │   ├── PreacherFilter.tsx
    │   ├── SermonFileManager.tsx
    │   ├── SermonWorkflowBoard.tsx
    │   ├── SmartSortingRules.tsx
    │   ├── SortableFileCard.tsx
    │   └── *.module.css # Component styles
    ├── contexts/        # React Context providers
    │   ├── AuthContext.tsx
    │   ├── FileManagerContext.tsx
    │   └── SermonSearchContext.tsx
    └── lib/             # Utility libraries
        ├── database.types.ts
        └── supabase.ts
```

## Key Components

### Core Components

#### [`SermonFileManager`](src/components/SermonFileManager.tsx)
Main dashboard component for managing sermon files. Features:
- Tabbed interface (Files, Smart Rules, Relationships)
- File grid view with bulk operations
- Smart sorting rules management
- File relationship visualization
- Folder assignment modal

#### [`FileGrid`](src/components/FileGrid.tsx)
Displays files in a grid layout with:
- File preview thumbnails
- Selection checkboxes
- Sorting and filtering options
- Multi-select support

#### [`BulkOperationsBar`](src/components/BulkOperationsBar.tsx)
Provides bulk actions for selected files:
- Move to folder
- Delete selected
- Apply sorting rules
- Export metadata

#### [`SmartSortingRules`](src/components/SmartSortingRules.tsx)
UI for creating and managing automatic file sorting rules based on:
- Speaker identification
- Date patterns
- Series categorization
- Custom regex patterns

#### [`FileRelationshipMap`](src/components/FileRelationshipMap.tsx)
Visualizes connections between sermon files:
- Series relationships
- Speaker connections
- Topic tags
- Cross-references

#### [`SermonWorkflowBoard`](src/components/SermonWorkflowBoard.tsx)
Kanban-style board for sermon processing workflow stages.

### Context Providers

#### [`AuthContext`](src/contexts/AuthContext.tsx)
Manages authentication state and RBAC:
- JWT token management
- User session handling
- Role-based access control
- Permission guards
- Protected route wrapper

**Key exports:**
- `useAuth()` - Hook to access auth state
- `AuthProvider` - Context provider component
- `ProtectedRoute` - HOC for protected pages
- `RoleBasedUI` - Conditional rendering by role
- `PermissionBasedUI` - Conditional rendering by permission
- `AdminOnly` / `ManagerOnly` - Role guard components

#### [`FileManagerContext`](src/contexts/FileManagerContext.tsx)
Provides file management state:
- File list management
- Selection state
- Upload progress
- Refresh functionality

#### [`SermonSearchContext`](src/contexts/SermonSearchContext.tsx)
Handles sermon search and filtering:
- Full-text search
- Filter by speaker, date, series
- Advanced query builder

## Library Configuration

### [`supabase.ts`](src/lib/supabase.ts)
Supabase client configuration with:
- Environment variable setup
- Auth configuration (auto-refresh, session persistence)
- Realtime subscriptions for file updates
- File storage operations (upload, delete, signed URLs)
- Auth helper functions (sign up, sign in, OAuth, password reset)

**Exported modules:**
- `supabase` - Supabase client instance
- `fileStorage` - File operations utility
- `fileRealtime` - Realtime subscription helpers
- `authHelpers` - Authentication functions
- `FileUploadResult` / `FileRecord` - Type definitions

### [`database.types.ts`](src/lib/database.types.ts)
TypeScript type definitions for Supabase database schema:

| Table | Description |
|-------|-------------|
| `files` | Uploaded file metadata |
| `users` | User profiles |
| `workflows` | Processing workflow configurations |
| `roles` | RBAC roles |
| `permissions` | Granular permissions |
| `audit_logs` | Action logging for compliance |

## Environment Variables

Required environment variables (set in `.env.local`):

```bash
NEXT_PUBLIC_SUPABASE_URL=your-project-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |

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
npm run start
```

### Docker

```bash
docker build -t fileforge-frontend .
docker run -p 3000:3000 fileforge-frontend
```

## Authentication Flow

1. User signs in via Supabase Auth
2. JWT token received and stored in localStorage
3. `AuthContext` decodes token and manages session
4. Role and permission claims extracted from token
5. Protected routes enforce access control

## File Upload Flow

1. User selects files via drag-and-drop or file picker
2. Files uploaded to Supabase Storage with progress tracking
3. File metadata saved to database
4. Realtime subscription notifies other clients
5. Processing pipeline triggered (backend)

## Smart Sorting Rules

The smart sorting system automatically organizes uploaded files based on:

- **Speaker Detection**: Identifies preacher from file metadata or audio analysis
- **Date Parsing**: Extracts sermon date from filename or ID3 tags
- **Series Detection**: Groups sermons into series based on naming patterns
- **Topic Classification**: Uses ML model to categorize by topic

Rules can be created and managed via the Smart Rules tab.

## Realtime Updates

The frontend subscribes to database changes via Supabase Realtime:

- File insert/update/delete notifications
- Processing status updates
- User presence indicators

## Testing

```bash
npm run test          # Run all tests
npm run test:watch    # Run tests in watch mode
npm run test:coverage # Generate coverage report
```

## Code Style

- TypeScript for type safety
- React functional components with hooks
- CSS Modules for component styling
- ESLint with Next.js config
- Prettier for formatting

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

See project root LICENSE file.
