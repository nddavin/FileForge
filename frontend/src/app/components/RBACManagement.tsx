import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { projectId, publicAnonKey } from '/utils/supabase/info';
import { Card, CardContent, CardHeader, CardTitle } from '@/app/components/ui/card';
import { Button } from '@/app/components/ui/button';
import { Badge } from '@/app/components/ui/badge';
import { Input } from '@/app/components/ui/input';
import { Checkbox } from '@/app/components/ui/checkbox';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/app/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/app/components/ui/dialog';
import {
  Plus,
  Trash2,
  Edit2,
  Shield,
  Users,
  Loader2,
  CheckCircle,
  XCircle,
  AlertTriangle,
} from 'lucide-react';
import { toast } from 'sonner';

// Permission definitions
const ALL_PERMISSIONS = [
  { id: 'files:read', name: 'Read Files', description: 'View and download files' },
  { id: 'files:write', name: 'Write Files', description: 'Upload and edit files' },
  { id: 'files:delete', name: 'Delete Files', description: 'Remove files' },
  { id: 'sermons:manage', name: 'Manage Sermons', description: 'Edit sermon metadata' },
  { id: 'sermons:publish', name: 'Publish Sermons', description: 'Publish sermons to public' },
  { id: 'users:read', name: 'Read Users', description: 'View user list' },
  { id: 'users:write', name: 'Manage Users', description: 'Create and edit users' },
  { id: 'rbac:manage', name: 'Manage RBAC', description: 'Edit roles and permissions' },
  { id: 'bulk:operations', name: 'Bulk Operations', description: 'Perform batch operations' },
  { id: 'analytics:view', name: 'View Analytics', description: 'Access analytics dashboard' },
];

// Default roles
const DEFAULT_ROLES = [
  {
    id: 'role_admin',
    name: 'Administrator',
    description: 'Full system access',
    permissions: ALL_PERMISSIONS.map(p => p.id),
    isSystem: true,
  },
  {
    id: 'role_manager',
    name: 'Manager',
    description: 'Content management access',
    permissions: ['files:read', 'files:write', 'files:delete', 'sermons:manage', 'sermons:publish', 'users:read', 'bulk:operations', 'analytics:view'],
    isSystem: true,
  },
  {
    id: 'role_editor',
    name: 'Editor',
    description: 'Content editing access',
    permissions: ['files:read', 'files:write', 'sermons:manage', 'bulk:operations'],
    isSystem: true,
  },
  {
    id: 'role_viewer',
    name: 'Viewer',
    description: 'Read-only access',
    permissions: ['files:read', 'analytics:view'],
    isSystem: true,
  },
];

interface Role {
  id: string;
  name: string;
  description: string;
  permissions: string[];
  isSystem?: boolean;
  userCount?: number;
}

interface RBACManagementProps {
  // Optional: Only show if user has specific permission
  requiredPermission?: string;
}

export function RBACManagement({ requiredPermission }: RBACManagementProps = {}) {
  const { session } = useAuth();
  const [roles, setRoles] = useState<Role[]>(DEFAULT_ROLES);
  const [loading, setLoading] = useState(false);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    permissions: [] as string[],
  });
  const [saving, setSaving] = useState(false);

  // Decode JWT and check permissions
  const checkPermission = useCallback((permission: string): boolean => {
    if (!session?.access_token) return false;
    
    try {
      // Decode JWT payload (simplified - in production use proper JWT library)
      const payload = JSON.parse(atob(session.access_token.split('.')[1]));
      
      // Check for specific permission
      const userPermissions = payload.permissions || payload.scope?.split(' ') || [];
      if (userPermissions.includes(permission)) return true;
      if (userPermissions.includes('rbac:manage')) return true;
      if (payload.role === 'admin' || payload.role === 'administrator') return true;
      
      return false;
    } catch (error) {
      console.error('Error decoding JWT:', error);
      return false;
    }
  }, [session]);

  // Client-side permission guard
  const [hasAccess, setHasAccess] = useState(false);

  useEffect(() => {
    if (requiredPermission) {
      setHasAccess(checkPermission(requiredPermission));
    } else {
      // Default: require rbac:manage or admin role
      setHasAccess(checkPermission('rbac:manage'));
    }
  }, [session, requiredPermission, checkPermission]);

  // Fetch roles from API
  const fetchRoles = useCallback(async () => {
    setLoading(true);
    try {
      // In production: GET /rbac/roles
      // const response = await fetch(`https://${projectId}.supabase.co/functions/v1/make-server-24311ee2/rbac/roles`, {
      //   headers: { Authorization: `Bearer ${publicAnonKey}` },
      // });
      // const data = await response.json();
      // setRoles(data);
      
      // Using mock data for demo
      await new Promise(resolve => setTimeout(resolve, 500));
    } catch (error) {
      toast.error('Failed to fetch roles');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRoles();
  }, [fetchRoles]);

  const handleOpenDialog = (role?: Role) => {
    if (role) {
      setEditingRole(role);
      setFormData({
        name: role.name,
        description: role.description,
        permissions: [...role.permissions],
      });
    } else {
      setEditingRole(null);
      setFormData({
        name: '',
        description: '',
        permissions: [],
      });
    }
    setIsDialogOpen(true);
  };

  const handlePermissionChange = (permissionId: string, checked: boolean) => {
    setFormData(prev => ({
      ...prev,
      permissions: checked
        ? [...prev.permissions, permissionId]
        : prev.permissions.filter(p => p !== permissionId),
    }));
  };

  const handleSave = async () => {
    if (!formData.name.trim()) {
      toast.error('Role name is required');
      return;
    }
    if (formData.permissions.length === 0) {
      toast.error('At least one permission is required');
      return;
    }

    setSaving(true);
    try {
      // In production: POST /rbac/roles or PATCH /rbac/roles/{id}
      // const method = editingRole ? 'PATCH' : 'POST';
      // const url = editingRole 
      //   ? `https://${projectId}.supabase.co/functions/v1/make-server-24311ee2/rbac/roles/${editingRole.id}`
      //   : `https://${projectId}.supabase.co/functions/v1/make-server-24311ee2/rbac/roles`;
      // 
      // await fetch(url, {
      //   method,
      //   headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${publicAnonKey}` },
      //   body: JSON.stringify(formData),
      // });

      await new Promise(resolve => setTimeout(resolve, 1000));

      // Update local state
      if (editingRole) {
        setRoles(prev => prev.map(r => 
          r.id === editingRole.id ? { ...r, ...formData } : r
        ));
        toast.success('Role updated successfully');
      } else {
        const newRole: Role = {
          id: `role_${Date.now()}`,
          ...formData,
          isSystem: false,
          userCount: 0,
        };
        setRoles(prev => [...prev, newRole]);
        toast.success('Role created successfully');
      }

      setIsDialogOpen(false);
    } catch (error) {
      toast.error('Failed to save role');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (role: Role) => {
    if (role.isSystem) {
      toast.error('Cannot delete system roles');
      return;
    }

    if (!confirm(`Are you sure you want to delete "${role.name}"?`)) {
      return;
    }

    setLoading(true);
    try {
      // In production: DELETE /rbac/roles/{id}
      // await fetch(`https://${projectId}.supabase.co/functions/v1/make-server-24311ee2/rbac/roles/${role.id}`, {
      //   method: 'DELETE',
      //   headers: { Authorization: `Bearer ${publicAnonKey}` },
      // });

      await new Promise(resolve => setTimeout(resolve, 500));

      setRoles(prev => prev.filter(r => r.id !== role.id));
      toast.success('Role deleted successfully');
    } catch (error) {
      toast.error('Failed to delete role');
    } finally {
      setLoading(false);
    }
  };

  // Permission guard - hide component if no access
  if (!hasAccess) {
    return (
      <Card className="border-yellow-200 bg-yellow-50">
        <CardContent className="py-8 text-center">
          <AlertTriangle className="w-12 h-12 mx-auto text-yellow-500 mb-4" />
          <h3 className="text-lg font-medium text-yellow-800 mb-2">Access Restricted</h3>
          <p className="text-yellow-600">You don't have permission to manage RBAC.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Roles & Permissions</h2>
          <p className="text-gray-500">Manage user roles and their permissions</p>
        </div>
        <Button onClick={() => handleOpenDialog()}>
          <Plus className="w-4 h-4 mr-2" />
          Add Role
        </Button>
      </div>

      {/* Roles Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Defined Roles
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[250px]">Role</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="w-[100px]">Users</TableHead>
                  <TableHead className="w-[150px]">Type</TableHead>
                  <TableHead className="w-[100px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {roles.map(role => (
                  <TableRow key={role.id}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{role.name}</Badge>
                        {role.isSystem && (
                          <Badge variant="secondary" className="text-xs">System</Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-gray-500">{role.description}</TableCell>
                    <TableCell>
                      <Badge variant="secondary">{role.userCount || 0}</Badge>
                    </TableCell>
                    <TableCell>
                      {role.isSystem ? (
                        <span className="text-xs text-gray-400">Built-in</span>
                      ) : (
                        <span className="text-xs text-gray-400">Custom</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleOpenDialog(role)}
                          disabled={role.isSystem}
                        >
                          <Edit2 className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(role)}
                          disabled={role.isSystem}
                          className="text-red-500 hover:text-red-600"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Permissions Matrix */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="w-5 h-5" />
            Permissions Matrix
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[200px]">Permission</TableHead>
                <TableHead>Description</TableHead>
                {roles.map(role => (
                  <TableHead key={role.id} className="text-center">
                    {role.name}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {ALL_PERMISSIONS.map(permission => (
                <TableRow key={permission.id}>
                  <TableCell>
                    <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                      {permission.id}
                    </code>
                  </TableCell>
                  <TableCell className="text-gray-500">{permission.description}</TableCell>
                  {roles.map(role => {
                    const hasPermission = role.permissions.includes(permission.id);
                    return (
                      <TableCell key={role.id} className="text-center">
                        {hasPermission ? (
                          <CheckCircle className="w-5 h-5 text-green-500 mx-auto" />
                        ) : (
                          <XCircle className="w-5 h-5 text-gray-300 mx-auto" />
                        )}
                      </TableCell>
                    );
                  })}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Add/Edit Role Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingRole ? 'Edit Role' : 'Create New Role'}
            </DialogTitle>
            <DialogDescription>
              {editingRole
                ? `Modify the "${editingRole.name}" role permissions`
                : 'Define a new role with specific permissions'}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            {/* Role Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Role Name</label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="e.g., Content Manager"
                  disabled={!!editingRole?.isSystem}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Description</label>
                <Input
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Brief description of this role"
                />
              </div>
            </div>

            {/* Permissions */}
            <div>
              <label className="text-sm font-medium mb-2 block">Permissions</label>
              <div className="grid grid-cols-2 gap-2 max-h-[300px] overflow-y-auto border rounded-lg p-4">
                {ALL_PERMISSIONS.map(permission => {
                  const isChecked = formData.permissions.includes(permission.id);
                  return (
                    <div
                      key={permission.id}
                      className="flex items-start gap-3 p-2 rounded hover:bg-gray-50"
                    >
                      <Checkbox
                        checked={isChecked}
                        onCheckedChange={(checked) => 
                          handlePermissionChange(permission.id, checked as boolean)
                        }
                        disabled={!!editingRole?.isSystem}
                      />
                      <div>
                        <p className="text-sm font-medium">{permission.name}</p>
                        <p className="text-xs text-gray-500">{permission.description}</p>
                        <code className="text-xs text-gray-400">{permission.id}</code>
                      </div>
                    </div>
                  );
                })}
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Selected: {formData.permissions.length} permissions
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={saving || !!editingRole?.isSystem}>
              {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              {editingRole ? 'Save Changes' : 'Create Role'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default RBACManagement;
