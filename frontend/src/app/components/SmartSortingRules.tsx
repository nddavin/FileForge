import React, { useState, useEffect } from 'react';
import { Button } from '@/app/components/ui/button';
import { Input } from '@/app/components/ui/input';
import { Label } from '@/app/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/app/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/app/components/ui/select';
import { Plus, Trash2 } from 'lucide-react';
import { projectId, publicAnonKey } from '/utils/supabase/info';
import { toast } from 'sonner';

interface Rule {
  id: string;
  name: string;
  condition_type: 'speaker' | 'series' | 'date' | 'filename';
  condition_value: string;
  action_type: 'move_to_folder' | 'add_metadata';
  action_value: string;
  created_at: string;
}

export function SmartSortingRules() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  
  const [newRule, setNewRule] = useState({
    name: '',
    condition_type: 'speaker' as const,
    condition_value: '',
    action_type: 'add_metadata' as const,
    action_value: '',
  });

  useEffect(() => {
    fetchRules();
  }, []);

  const fetchRules = async () => {
    try {
      const response = await fetch(
        `https://${projectId}.supabase.co/functions/v1/make-server-24311ee2/rules`,
        {
          headers: {
            Authorization: `Bearer ${publicAnonKey}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setRules(data);
      }
    } catch (error) {
      console.error('Error fetching rules:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const response = await fetch(
        `https://${projectId}.supabase.co/functions/v1/make-server-24311ee2/rules`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${publicAnonKey}`,
          },
          body: JSON.stringify(newRule),
        }
      );

      if (response.ok) {
        toast.success('Rule created successfully');
        setNewRule({
          name: '',
          condition_type: 'speaker',
          condition_value: '',
          action_type: 'add_metadata',
          action_value: '',
        });
        setShowForm(false);
        await fetchRules();
      } else {
        toast.error('Failed to create rule');
      }
    } catch (error) {
      console.error('Error creating rule:', error);
      toast.error('Failed to create rule');
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    if (!confirm('Are you sure you want to delete this rule?')) {
      return;
    }

    try {
      const response = await fetch(
        `https://${projectId}.supabase.co/functions/v1/make-server-24311ee2/rules/${ruleId}`,
        {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${publicAnonKey}`,
          },
        }
      );

      if (response.ok) {
        toast.success('Rule deleted successfully');
        await fetchRules();
      } else {
        toast.error('Failed to delete rule');
      }
    } catch (error) {
      console.error('Error deleting rule:', error);
      toast.error('Failed to delete rule');
    }
  };

  if (loading) {
    return <div className="p-4">Loading rules...</div>;
  }

  return (
    <div className="p-4 space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Smart Sorting Rules</h2>
        <Button onClick={() => setShowForm(!showForm)}>
          <Plus className="w-4 h-4 mr-2" />
          Add Rule
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Create New Rule</CardTitle>
            <CardDescription>
              Automatically organize files based on conditions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateRule} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="rule-name">Rule Name</Label>
                <Input
                  id="rule-name"
                  value={newRule.name}
                  onChange={(e) => setNewRule({ ...newRule, name: e.target.value })}
                  placeholder="e.g., Sort by Speaker"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="condition-type">Condition Type</Label>
                  <Select
                    value={newRule.condition_type}
                    onValueChange={(value: any) =>
                      setNewRule({ ...newRule, condition_type: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="speaker">Speaker</SelectItem>
                      <SelectItem value="series">Series</SelectItem>
                      <SelectItem value="date">Date</SelectItem>
                      <SelectItem value="filename">Filename</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="condition-value">Condition Value</Label>
                  <Input
                    id="condition-value"
                    value={newRule.condition_value}
                    onChange={(e) =>
                      setNewRule({ ...newRule, condition_value: e.target.value })
                    }
                    placeholder="e.g., John Doe"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="action-type">Action Type</Label>
                  <Select
                    value={newRule.action_type}
                    onValueChange={(value: any) =>
                      setNewRule({ ...newRule, action_type: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="add_metadata">Add Metadata</SelectItem>
                      <SelectItem value="move_to_folder">Move to Folder</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="action-value">Action Value</Label>
                  <Input
                    id="action-value"
                    value={newRule.action_value}
                    onChange={(e) =>
                      setNewRule({ ...newRule, action_value: e.target.value })
                    }
                    placeholder="e.g., /sermons/john-doe"
                    required
                  />
                </div>
              </div>

              <div className="flex gap-2">
                <Button type="submit">Create Rule</Button>
                <Button type="button" variant="outline" onClick={() => setShowForm(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <div className="space-y-4">
        {rules.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center text-gray-500">
              No sorting rules yet. Create one to automatically organize your files.
            </CardContent>
          </Card>
        ) : (
          rules.map((rule) => (
            <Card key={rule.id}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-medium">{rule.name}</h3>
                    <p className="text-sm text-gray-600 mt-1">
                      When <span className="font-medium">{rule.condition_type}</span> is{' '}
                      <span className="font-medium">{rule.condition_value}</span>
                    </p>
                    <p className="text-sm text-gray-600">
                      Then <span className="font-medium">{rule.action_type}</span>:{' '}
                      <span className="font-medium">{rule.action_value}</span>
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeleteRule(rule.id)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
