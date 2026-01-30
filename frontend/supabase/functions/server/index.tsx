import { Hono } from "npm:hono";
import { cors } from "npm:hono/cors";
import { logger } from "npm:hono/logger";
import { createClient } from "npm:@supabase/supabase-js@2";
import * as kv from "./kv_store.tsx";

const app = new Hono();

// Create Supabase clients
const supabase = createClient(
  Deno.env.get('SUPABASE_URL'),
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY'),
);

const supabaseAnon = createClient(
  Deno.env.get('SUPABASE_URL'),
  Deno.env.get('SUPABASE_ANON_KEY'),
);

// Enable logger
app.use('*', logger(console.log));

// Enable CORS for all routes and methods
app.use(
  "/*",
  cors({
    origin: "*",
    allowHeaders: ["Content-Type", "Authorization"],
    allowMethods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    exposeHeaders: ["Content-Length"],
    maxAge: 600,
  }),
);

// Create storage bucket on startup
(async () => {
  const bucketName = 'make-24311ee2-files';
  const { data: buckets } = await supabase.storage.listBuckets();
  const bucketExists = buckets?.some(bucket => bucket.name === bucketName);
  if (!bucketExists) {
    await supabase.storage.createBucket(bucketName, { public: false });
    console.log(`Created bucket: ${bucketName}`);
  }
})();

// Health check endpoint
app.get("/make-server-24311ee2/health", (c) => {
  return c.json({ status: "ok" });
});

// Authentication: Sign up
app.post("/make-server-24311ee2/signup", async (c) => {
  try {
    const { email, password, name } = await c.req.json();

    const { data, error } = await supabase.auth.admin.createUser({
      email,
      password,
      user_metadata: { name },
      // Automatically confirm the user's email since an email server hasn't been configured.
      email_confirm: true
    });

    if (error) {
      console.error('Sign up error:', error);
      return c.json({ error: error.message }, 400);
    }

    return c.json({ user: data.user });
  } catch (error) {
    console.error('Sign up request error:', error);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

// Files: List all files
app.get("/make-server-24311ee2/files", async (c) => {
  try {
    const files = await kv.getByPrefix('file:');
    const fileList = files.map((f) => f.value);
    return c.json(fileList);
  } catch (error) {
    console.error('Error fetching files:', error);
    return c.json({ error: 'Failed to fetch files' }, 500);
  }
});

// Files: Get single file
app.get("/make-server-24311ee2/files/:id", async (c) => {
  try {
    const id = c.req.param('id');
    const file = await kv.get(`file:${id}`);
    
    if (!file) {
      return c.json({ error: 'File not found' }, 404);
    }

    return c.json(file);
  } catch (error) {
    console.error('Error fetching file:', error);
    return c.json({ error: 'Failed to fetch file' }, 500);
  }
});

// Files: Create file metadata
app.post("/make-server-24311ee2/files", async (c) => {
  try {
    const fileData = await c.req.json();
    const id = crypto.randomUUID();
    
    const file = {
      id,
      ...fileData,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    await kv.set(`file:${id}`, file);
    return c.json(file, 201);
  } catch (error) {
    console.error('Error creating file:', error);
    return c.json({ error: 'Failed to create file' }, 500);
  }
});

// Files: Update file metadata
app.put("/make-server-24311ee2/files/:id", async (c) => {
  try {
    const id = c.req.param('id');
    const updates = await c.req.json();
    
    const existing = await kv.get(`file:${id}`);
    if (!existing) {
      return c.json({ error: 'File not found' }, 404);
    }

    const updated = {
      ...existing,
      ...updates,
      id,
      updated_at: new Date().toISOString(),
    };

    await kv.set(`file:${id}`, updated);
    return c.json(updated);
  } catch (error) {
    console.error('Error updating file:', error);
    return c.json({ error: 'Failed to update file' }, 500);
  }
});

// Files: Delete file
app.delete("/make-server-24311ee2/files/:id", async (c) => {
  try {
    const id = c.req.param('id');
    const file = await kv.get(`file:${id}`);
    
    if (!file) {
      return c.json({ error: 'File not found' }, 404);
    }

    // Delete from storage
    if (file.path) {
      await supabase.storage.from('make-24311ee2-files').remove([file.path]);
    }

    // Delete metadata
    await kv.del(`file:${id}`);
    return c.json({ success: true });
  } catch (error) {
    console.error('Error deleting file:', error);
    return c.json({ error: 'Failed to delete file' }, 500);
  }
});

// Folders: List all folders
app.get("/make-server-24311ee2/folders", async (c) => {
  try {
    const folders = await kv.getByPrefix('folder:');
    const folderList = folders.map((f) => f.value);
    return c.json(folderList);
  } catch (error) {
    console.error('Error fetching folders:', error);
    return c.json({ error: 'Failed to fetch folders' }, 500);
  }
});

// Folders: Create folder
app.post("/make-server-24311ee2/folders", async (c) => {
  try {
    const { name, parent_id } = await c.req.json();
    const id = crypto.randomUUID();
    
    const folder = {
      id,
      name,
      parent_id,
      created_at: new Date().toISOString(),
    };

    await kv.set(`folder:${id}`, folder);
    return c.json(folder, 201);
  } catch (error) {
    console.error('Error creating folder:', error);
    return c.json({ error: 'Failed to create folder' }, 500);
  }
});

// Smart Sorting Rules: List all rules
app.get("/make-server-24311ee2/rules", async (c) => {
  try {
    const rules = await kv.getByPrefix('rule:');
    const ruleList = rules.map((r) => r.value);
    return c.json(ruleList);
  } catch (error) {
    console.error('Error fetching rules:', error);
    return c.json({ error: 'Failed to fetch rules' }, 500);
  }
});

// Smart Sorting Rules: Create rule
app.post("/make-server-24311ee2/rules", async (c) => {
  try {
    const ruleData = await c.req.json();
    const id = crypto.randomUUID();
    
    const rule = {
      id,
      ...ruleData,
      created_at: new Date().toISOString(),
    };

    await kv.set(`rule:${id}`, rule);
    return c.json(rule, 201);
  } catch (error) {
    console.error('Error creating rule:', error);
    return c.json({ error: 'Failed to create rule' }, 500);
  }
});

// Smart Sorting Rules: Delete rule
app.delete("/make-server-24311ee2/rules/:id", async (c) => {
  try {
    const id = c.req.param('id');
    await kv.del(`rule:${id}`);
    return c.json({ success: true });
  } catch (error) {
    console.error('Error deleting rule:', error);
    return c.json({ error: 'Failed to delete rule' }, 500);
  }
});

Deno.serve(app.fetch);