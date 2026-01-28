# ADR-002: Supabase with Row Level Security (RLS)

| ADR ID | Title | Status |
|--------|-------|--------|
| 002 | Supabase with Row Level Security | Accepted |

## Context

FileForge needs a database solution that provides:
- Strong security and access control
- Real-time capabilities
- Easy scaling
- PostgreSQL compatibility

We evaluated:
1. **Supabase** (PostgreSQL + RLS + Realtime)
2. **Firebase Firestore**
3. **Custom PostgreSQL** on managed services

## Decision

We chose **Supabase** as our primary database and authentication provider, leveraging **Row Level Security (RLS)** for access control.

### Architecture

```
┌─────────────────────────────────────────────────┐
│              Application (FastAPI)               │
├─────────────────────────────────────────────────┤
│              Supabase Client                     │
├─────────────┬───────────────┬───────────────────┤
│   Auth RLS  │  Data RLS     │  Realtime         │
│  Policies   │  Policies     │  Subscriptions    │
├─────────────┴───────────────┴───────────────────┤
│            PostgreSQL Database                   │
│   (Supabase managed with RLS policies)          │
└─────────────────────────────────────────────────┘
```

### RLS Policy Examples

#### Policy: Users can only see their own files

```sql
CREATE POLICY "Users can view own files"
ON files FOR SELECT
USING (auth.uid() = user_id);
```

#### Policy: Managers can see team files

```sql
CREATE POLICY "Managers can view team files"
ON files FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM user_teams
    WHERE user_teams.team_id = files.team_id
    AND user_teams.user_id = auth.uid()
    AND user_teams.role IN ('manager', 'admin')
  )
);
```

#### Policy: Admins can access all files

```sql
CREATE POLICY "Admins can view all files"
ON files FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM user_roles
    WHERE user_roles.user_id = auth.uid()
    AND user_roles.role = 'admin'
  )
);
```

## Consequences

### Positive

- **Security**: RLS enforces access control at database level
- **Real-time**: Built-in subscription support for live updates
- **Developer Experience**: Simple SDK, excellent documentation
- **PostgreSQL**: Full SQL capabilities, extensions available
- **Scalability**: Handles millions of records

### Negative

- **Vendor Lock-in**: Dependent on Supabase infrastructure
- **Cost**: Can increase with high usage
- **Complexity**: RLS policies can become complex
- **Cold Starts**: Edge function latency

## Implementation

### Database Schema

```sql
-- Enable RLS
ALTER TABLE files ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sermons ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Users can CRUD own files"
ON files FOR ALL
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Managers can view team files"
ON files FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM teams
    WHERE teams.id = files.team_id
    AND teams.manager_id = auth.uid()
  )
);
```

### Supabase Client

```python
from supabase import create_client, Client

class SupabaseService:
    def __init__(self, url: str, key: str):
        self.client: Client = create_client(url, key)
    
    async def get_files(self, user_id: str):
        return self.client.table('files') \
            .select('*') \
            .eq('user_id', user_id) \
            .execute()
    
    async def create_file(self, file_data: dict):
        return self.client.table('files') \
            .insert(file_data) \
            .execute()
    
    async def subscribe_to_files(self, user_id: str, callback):
        channel = self.client.channel('files')
        channel.on(
            'postgres_changes',
            {
                'event': '*',
                'schema': 'public',
                'table': 'files',
                'filter': f'user_id=eq.{user_id}'
            },
            callback
        ).subscribe()
```

## Date

2024-01-15
