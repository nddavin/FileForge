// Team Member Management Component
import React, { useState, useEffect } from 'react';
import {
  listTeamMembers,
  getTeamMember,
  getTeamRoleLabel,
} from '../../lib/taskApi';
import { TeamMember, TeamRole } from '../../lib/types';

const TeamMemberManagement: React.FC = () => {
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [selectedMember, setSelectedMember] = useState<TeamMember | null>(null);
  const [loading, setLoading] = useState(true);
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [availabilityFilter, setAvailabilityFilter] = useState<boolean | undefined>(
    undefined
  );

  useEffect(() => {
    loadTeamMembers();
  }, [roleFilter, availabilityFilter]);

  const loadTeamMembers = async () => {
    setLoading(true);
    try {
      const result = await listTeamMembers({
        limit: 50,
        ...(roleFilter && { role: roleFilter }),
        ...(availabilityFilter !== undefined && {
          is_active: availabilityFilter,
        }),
      });
      if (result.success) {
        setMembers(result.data || []);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleViewMember = async (member: TeamMember) => {
    setSelectedMember(member);
    try {
      const result = await getTeamMember(member.id);
      if (result.success && result.data) {
        setSelectedMember(result.data);
      }
    } catch (error) {
      console.error('Failed to get member details:', error);
    }
  };

  const getWorkloadPercentage = (member: TeamMember): number => {
    if (member.max_concurrent_tasks === 0) return 0;
    return Math.round((member.current_workload / member.max_concurrent_tasks) * 100);
  };

  const getWorkloadColor = (percentage: number): string => {
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 70) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Team Members</h1>
        <div className="flex gap-4">
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="rounded-md border-gray-300 border p-2"
          >
            <option value="">All Roles</option>
            <option value={TeamRole.EDITOR}>Editor</option>
            <option value={TeamRole.PROCESSOR}>Processor</option>
            <option value={TeamRole.MANAGER}>Manager</option>
            <option value={TeamRole.ADMIN}>Admin</option>
            <option value={TeamRole.AUDIO_ENGINEER}>Audio Engineer</option>
            <option value={TeamRole.VIDEO_PROCESSOR}>Video Processor</option>
            <option value={TeamRole.TRANSCRIBER}>Transcriber</option>
            <option value={TeamRole.LOCATION_TAGGER}>Location Tagger</option>
          </select>
          <select
            value={availabilityFilter === undefined ? '' : availabilityFilter.toString()}
            onChange={(e) =>
              setAvailabilityFilter(
                e.target.value === '' ? undefined : e.target.value === 'true'
              )
            }
            className="rounded-md border-gray-300 border p-2"
          >
            <option value="">All Status</option>
            <option value="true">Available</option>
            <option value="false">Unavailable</option>
          </select>
        </div>
      </div>

      {/* Team Members Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {members.map((member) => (
          <div
            key={member.id}
            className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => handleViewMember(member)}
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="font-semibold text-lg">{member.full_name}</h3>
                <p className="text-sm text-gray-500">{member.email}</p>
              </div>
              <span
                className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                  member.is_available
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                {member.is_available ? 'Available' : 'Busy'}
              </span>
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Role</span>
                <span className="font-medium">
                  {getTeamRoleLabel(member.team_role)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Completed Tasks</span>
                <span className="font-medium">{member.completed_tasks_count}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Rating</span>
                <span className="font-medium">{member.rating.toFixed(1)} / 5.0</span>
              </div>
            </div>

            {/* Workload Progress */}
            <div className="mt-4">
              <div className="flex justify-between text-xs text-gray-500 mb-1">
                <span>Workload</span>
                <span>
                  {member.current_workload}/{member.max_concurrent_tasks}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all ${getWorkloadColor(
                    getWorkloadPercentage(member)
                  )}`}
                  style={{ width: `${getWorkloadPercentage(member)}%` }}
                />
              </div>
            </div>

            {/* Skills */}
            {member.skills.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-1">
                {member.skills.slice(0, 3).map((skill) => (
                  <span
                    key={skill.id}
                    className="inline-flex px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded"
                  >
                    {skill.name}
                  </span>
                ))}
                {member.skills.length > 3 && (
                  <span className="inline-flex px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">
                    +{member.skills.length - 3} more
                  </span>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {members.length === 0 && !loading && (
        <div className="text-center py-12 text-gray-500">
          No team members found matching the current filters.
        </div>
      )}

      {/* Member Details Modal */}
      {selectedMember && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-xl font-bold">{selectedMember.full_name}</h2>
                <p className="text-gray-500">{selectedMember.email}</p>
              </div>
              <button
                onClick={() => setSelectedMember(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg
                  className="w-6 h-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-gray-500">Role</label>
                  <p className="font-medium">
                    {getTeamRoleLabel(selectedMember.team_role)}
                  </p>
                </div>
                <div>
                  <label className="text-sm text-gray-500">Status</label>
                  <p className="font-medium">
                    {selectedMember.is_available ? 'Available' : 'Unavailable'}
                  </p>
                </div>
                <div>
                  <label className="text-sm text-gray-500">Completed Tasks</label>
                  <p className="font-medium">{selectedMember.completed_tasks_count}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-500">Rating</label>
                  <p className="font-medium">{selectedMember.rating.toFixed(1)} / 5.0</p>
                </div>
              </div>

              {/* Workload Details */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-medium mb-2">Workload</h3>
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <div className="w-full bg-gray-200 rounded-full h-4">
                      <div
                        className={`h-4 rounded-full ${getWorkloadColor(
                          getWorkloadPercentage(selectedMember)
                        )}`}
                        style={{
                          width: `${getWorkloadPercentage(selectedMember)}%`,
                        }}
                      />
                    </div>
                  </div>
                  <span className="text-sm font-medium">
                    {getWorkloadPercentage(selectedMember)}%
                  </span>
                </div>
                <p className="text-sm text-gray-500 mt-1">
                  {selectedMember.current_workload} of {selectedMember.max_concurrent_tasks}{' '}
                  tasks assigned
                </p>
              </div>

              {/* Skills */}
              <div>
                <h3 className="font-medium mb-2">Skills</h3>
                <div className="flex flex-wrap gap-2">
                  {selectedMember.skills.map((skill) => (
                    <span
                      key={skill.id}
                      className="inline-flex px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded-full"
                    >
                      {skill.name}
                      {skill.proficiency_levels.expert && (
                        <span className="ml-1 text-blue-600">⭐</span>
                      )}
                    </span>
                  ))}
                </div>
              </div>

              {/* Notification Channels */}
              <div>
                <h3 className="font-medium mb-2">Notification Preferences</h3>
                <div className="flex gap-2">
                  {selectedMember.notification_channels.map((channel) => (
                    <span
                      key={channel}
                      className="inline-flex px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded capitalize"
                    >
                      {channel}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeamMemberManagement;
