/* Smart Sorting Rules - AI-powered sorting rule management */

import React, { useState } from 'react';
import { useFileManager, SortCondition, SortingRule } from '../contexts/FileManagerContext';
import { predictFolder } from '../contexts/FileManagerContext';
import styles from './SmartSortingRules.module.css';

export const SmartSortingRules: React.FC = () => {
  const { sortingRules, saveRule, deleteRule, files } = useFileManager();
  const [showBuilder, setShowBuilder] = useState(false);
  const [editingRule, setEditingRule] = useState<SortingRule | null>(null);

  // Count files that match each rule
  const getMatchingCount = (rule: SortingRule) => {
    return files.filter(f => predictFolder(f, [rule]) === rule.target_folder).length;
  };

  return (
    <div className={styles.rulesPanel}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.title}>
          <h3>🤖 AI Smart Sorting Rules</h3>
          <span className={styles.ruleCount}>
            {sortingRules.length} active rule{sortingRules.length !== 1 ? 's' : ''}
          </span>
        </div>
        
        <button 
          className={styles.addRuleBtn}
          onClick={() => {
            setEditingRule(null);
            setShowBuilder(true);
          }}
        >
          + Add New Rule
        </button>
      </div>

      {/* Rule Builder Modal */}
      {showBuilder && (
        <RuleBuilder
          rule={editingRule}
          onSave={async (rule) => {
            await saveRule(rule);
            setShowBuilder(false);
          }}
          onCancel={() => setShowBuilder(false)}
        />
      )}

      {/* Active Rules List */}
      <div className={styles.rulesList}>
        {sortingRules.length === 0 ? (
          <div className={styles.emptyState}>
            <span className={styles.emptyIcon}>📋</span>
            <p>No sorting rules configured yet.</p>
            <p>Create your first rule to automatically organize new uploads.</p>
          </div>
        ) : (
          sortingRules.map((rule) => (
            <div key={rule.id} className={styles.ruleCard}>
              <div className={styles.ruleHeader}>
                <div className={styles.ruleName}>
                  <span className={styles.ruleIcon}>
                    {rule.auto_apply ? '⚡' : '📋'}
                  </span>
                  <span>{rule.name}</span>
                </div>
                <div className={styles.ruleActions}>
                  <button 
                    className={styles.editBtn}
                    onClick={() => {
                      setEditingRule(rule);
                      setShowBuilder(true);
                    }}
                  >
                    Edit
                  </button>
                  <button 
                    className={styles.deleteBtn}
                    onClick={() => {
                      if (rule.id) deleteRule(rule.id);
                    }}
                  >
                    Delete
                  </button>
                </div>
              </div>

              <div className={styles.ruleConditions}>
                <span className={styles.conditionLabel}>IF:</span>
                <div className={styles.conditions}>
                  {rule.conditions.map((cond, i) => (
                    <span key={i} className={styles.conditionBadge}>
                      {formatCondition(cond)}
                    </span>
                  ))}
                </div>
              </div>

              <div className={styles.ruleAction}>
                <span className={styles.actionLabel}>THEN:</span>
                <span className={styles.actionBadge}>
                  → Move to "{rule.target_folder}"
                </span>
              </div>

              <div className={styles.ruleFooter}>
                <span className={styles.matchCount}>
                  ✨ Matches {getMatchingCount(rule)} files
                </span>
                {rule.auto_apply && (
                  <span className={styles.autoApplyBadge}>
                    Auto-apply enabled
                  </span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

// Format condition for display
const formatCondition = (cond: SortCondition): string => {
  const operators: Record<string, string> = {
    eq: '=',
    ne: '!=',
    contains: 'contains',
    gt: '>',
    lt: '<',
    gte: '≥',
    lte: '≤'
  };
  return `${cond.field} ${operators[cond.operator] || cond.operator} "${cond.value}"`;
};

// Rule Builder Component
interface RuleBuilderProps {
  rule: SortingRule | null;
  onSave: (rule: SortingRule) => Promise<void>;
  onCancel: () => void;
}

const RuleBuilder: React.FC<RuleBuilderProps> = ({ rule, onSave, onCancel }) => {
  const [name, setName] = useState(rule?.name || '');
  const [targetFolder, setTargetFolder] = useState(rule?.target_folder || '');
  const [autoApply, setAutoApply] = useState(rule?.auto_apply ?? true);
  const [conditions, setConditions] = useState<SortCondition[]>(
    rule?.conditions || []
  );
  const [saving, setSaving] = useState(false);

  const addCondition = () => {
    setConditions([
      ...conditions,
      { field: 'preacher_id', operator: 'eq', value: '' }
    ]);
  };

  const updateCondition = (index: number, updates: Partial<SortCondition>) => {
    setConditions(conditions.map((c, i) => 
      i === index ? { ...c, ...updates } : c
    ));
  };

  const removeCondition = (index: number) => {
    setConditions(conditions.filter((_, i) => i !== index));
  };

  const handleSave = async () => {
    if (!name || !targetFolder || conditions.length === 0) {
      alert('Please fill in all required fields');
      return;
    }

    setSaving(true);
    try {
      await onSave({
        id: rule?.id,
        church_id: '', // Will be set by context
        name,
        conditions,
        target_folder: targetFolder,
        priority: rule?.priority || 0,
        auto_apply: autoApply
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className={styles.builderOverlay}>
      <div className={styles.builder}>
        <div className={styles.builderHeader}>
          <h3>{rule ? 'Edit Rule' : 'Create New Rule'}</h3>
          <button className={styles.closeBtn} onClick={onCancel}>✕</button>
        </div>

        <div className={styles.builderContent}>
          {/* Rule Name */}
          <div className={styles.formGroup}>
            <label>Rule Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Pastor John's Sermons"
            />
          </div>

          {/* Target Folder */}
          <div className={styles.formGroup}>
            <label>Target Folder</label>
            <input
              type="text"
              value={targetFolder}
              onChange={(e) => setTargetFolder(e.target.value)}
              placeholder="e.g., /sermons/pastor-john"
            />
          </div>

          {/* Conditions */}
          <div className={styles.formGroup}>
            <label>Conditions (AND logic)</label>
            <div className={styles.conditionsList}>
              {conditions.map((cond, index) => (
                <div key={index} className={styles.conditionRow}>
                  <select
                    value={cond.field}
                    onChange={(e) => updateCondition(index, { field: e.target.value })}
                  >
                    <option value="preacher_id">Preacher</option>
                    <option value="primary_language">Language</option>
                    <option value="location_city">Location</option>
                    <option value="file_type">File Type</option>
                    <option value="quality_score">Quality Score</option>
                    <option value="created_at">Date Created</option>
                  </select>

                  <select
                    value={cond.operator}
                    onChange={(e) => updateCondition(index, { 
                      operator: e.target.value as SortCondition['operator'] 
                    })}
                  >
                    <option value="eq">equals</option>
                    <option value="ne">not equals</option>
                    <option value="contains">contains</option>
                    <option value="gt">greater than</option>
                    <option value="lt">less than</option>
                  </select>

                  <input
                    type="text"
                    value={cond.value}
                    onChange={(e) => updateCondition(index, { value: e.target.value })}
                    placeholder="Value..."
                  />

                  <button 
                    className={styles.removeCondition}
                    onClick={() => removeCondition(index)}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
            <button className={styles.addConditionBtn} onClick={addCondition}>
              + Add Condition
            </button>
          </div>

          {/* Auto Apply Toggle */}
          <div className={styles.autoApplyToggle}>
            <label>
              <input
                type="checkbox"
                checked={autoApply}
                onChange={(e) => setAutoApply(e.target.checked)}
              />
              Auto-sort new uploads matching this rule
            </label>
          </div>
        </div>

        <div className={styles.builderFooter}>
          <button className={styles.cancelBtn} onClick={onCancel}>
            Cancel
          </button>
          <button 
            className={styles.saveBtn} 
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save Rule'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SmartSortingRules;
