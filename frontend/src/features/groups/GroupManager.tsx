import { useState } from "react";
import { useParams } from "react-router-dom";
import toast from "react-hot-toast";
import Modal from "../../ui/Modal";
import { isTeacher } from "../../util/login";
import {
  useGroups,
  useMyGroup,
  useUnassignedStudents,
  useGroupMembers,
  useCreateGroup,
  useDeleteGroup,
  useAddGroupMember,
  useRemoveGroupMember,
} from "./useGroups";

interface GroupMember {
  id: number;
  name: string;
  email: string;
}

function GroupMembersPanel({
  group,
  isOpen,
  onRemove,
}: {
  group: CourseGroup;
  isOpen: boolean;
  onRemove: (userId: number, groupId: number) => void;
}) {
  const { data: members = [] } = useGroupMembers(group.id);

  if (!isOpen || members.length === 0) return null;

  return (
    <div className="divide-y divide-border bg-bg-secondary/50">
      {members.map((member: GroupMember) => (
        <div key={member.id} className="flex items-center justify-between py-3 px-5 md:px-8 pl-12">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-7 h-7 rounded-full bg-btn-primary/10 flex items-center justify-center text-xs font-semibold text-btn-primary flex-shrink-0">
              {member.name.charAt(0).toUpperCase()}
            </div>
            <span className="text-sm text-text-primary truncate">{member.name}</span>
          </div>
          <button
            className="text-xs px-2.5 py-1 rounded-md text-red-600 bg-red-50 hover:bg-red-100 border border-red-200 transition-colors cursor-pointer font-medium"
            onClick={() => onRemove(member.id, group.id)}
          >
            Remove
          </button>
        </div>
      ))}
    </div>
  );
}

export default function Group() {
  const { id } = useParams();
  const courseId = Number(id);

  const [selectedGroup, setSelectedGroup] = useState<number>(-1);
  const [groupName, setGroupName] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<CourseGroup | null>(null);

  const { data: groups = [], isLoading: groupsLoading } = useGroups(courseId);
  const { data: unassignedStudents = [], isLoading: unassignedLoading } = useUnassignedStudents(courseId);
  const { data: myGroup = null, isLoading: myGroupLoading } = useMyGroup(courseId);

  const createGroupMutation = useCreateGroup(courseId);
  const deleteGroupMutation = useDeleteGroup(courseId);
  const addMemberMutation = useAddGroupMember(courseId);
  const removeMemberMutation = useRemoveGroupMember(courseId);

  const loading = isTeacher() ? (groupsLoading || unassignedLoading) : myGroupLoading;

const handleCreateGroup = async () => {
  const trimmedName = groupName.trim();

  if (!trimmedName) {
    toast.error('Please enter a group name');
    return;
  }

  if (trimmedName.length > 50) {
    toast.error('Group name must be 50 characters or fewer');
    return;
  }

  try {
    await createGroupMutation.mutateAsync(trimmedName);
    setGroupName('');
    toast.success('Group created!');
  } catch {
    toast.error('Error creating group');
  }
};

  const handleDeleteGroup = async () => {
    if (!deleteTarget) return;
    try {
      await deleteGroupMutation.mutateAsync(deleteTarget.id);
      if (selectedGroup === deleteTarget.id) setSelectedGroup(-1);
      toast.success('Group deleted!');
    } catch {
      toast.error('Error deleting group');
    } finally {
      setDeleteTarget(null);
    }
  };

  const handleAddToGroup = async (userId: number) => {
    if (selectedGroup === -1) {
      toast.error('Please select a group first');
      return;
    }
    try {
      await addMemberMutation.mutateAsync({ groupId: selectedGroup, userId });
      toast.success('Student added to group!');
    } catch {
      toast.error('Error adding student to group');
    }
  };

  const handleRemoveFromGroup = async (userId: number, groupId: number) => {
    try {
      await removeMemberMutation.mutateAsync({ groupId, userId });
      toast.success('Student removed from group!');
    } catch {
      toast.error('Error removing student from group');
    }
  };

  if (loading) {
    return (
      <div className="p-4 md:p-8 w-full max-w-260 mx-auto">
        <p className="text-text-secondary text-sm">Loading...</p>
      </div>
    );
  }

  /* ─── Student View ─── */
  if (!isTeacher()) {
    return (
      <div className="p-4 md:p-8 w-full max-w-260 mx-auto flex flex-col gap-6">
        <h2 className="text-2xl font-semibold text-text-primary m-0">My Group</h2>

        <div className="bg-white rounded-2xl border border-border shadow-sm overflow-hidden">
          {myGroup ? (
            <>
              <div className="px-5 md:px-8 py-4 border-b border-border">
                <h3 className="text-base font-semibold text-text-primary m-0">{myGroup.name}</h3>
              </div>
              <div className="divide-y divide-border">
                {myGroup.members.map((member: GroupMember) => (
                  <div key={member.id} className="flex items-center gap-3 px-5 md:px-8 py-3.5">
                    <div className="w-9 h-9 rounded-full bg-btn-primary/10 flex items-center justify-center text-sm font-semibold text-btn-primary flex-shrink-0">
                      {member.name.charAt(0).toUpperCase()}
                    </div>
                    <span className="text-sm font-medium text-text-primary">{member.name}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="px-5 md:px-8 py-8 flex flex-col items-center gap-2">
              <span className="text-3xl">👥</span>
              <p className="text-text-secondary text-sm m-0">You are not assigned to any group yet.</p>
            </div>
          )}
        </div>
      </div>
    );
  }

  /* ─── Teacher View ─── */
  return (
    <div className="p-4 md:p-8 w-full max-w-260 mx-auto flex flex-col gap-6">
      <h2 className="text-2xl font-semibold text-text-primary m-0">Groups</h2>

      {/* Create group row */}
      <div className="flex flex-col sm:flex-row gap-3">
        <input
          type="text"
          placeholder="New group name..."
          value={groupName}
          maxLength={50}
          onChange={(e) => setGroupName(e.target.value)}
          className="flex-1 sm:max-w-xs px-3.5 py-2.5 border border-border rounded-lg bg-white text-text-primary text-sm font-[inherit] focus:outline-none focus:ring-2 focus:ring-btn-primary/30 focus:border-btn-primary transition-all"
        />
        <button
          onClick={handleCreateGroup}
          className="px-5 py-2.5 bg-btn-primary text-white text-sm font-semibold rounded-lg cursor-pointer transition-all hover:brightness-110 active:scale-[0.98] border-none"
        >
          Create Group
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Unassigned Students */}
        <div className="bg-white rounded-2xl border border-border shadow-sm overflow-hidden">
          <div className="px-5 md:px-8 py-4 border-b border-border flex items-center justify-between">
            <h3 className="text-base font-semibold text-text-primary m-0">Unassigned Students</h3>
            <span className="text-xs font-medium text-text-secondary bg-bg-secondary px-2.5 py-1 rounded-full">
              {unassignedStudents.length}
            </span>
          </div>
          {unassignedStudents.length === 0 ? (
            <div className="px-5 md:px-8 py-8 flex flex-col items-center gap-2">
              <p className="text-text-secondary text-sm m-0">All students are assigned.</p>
            </div>
          ) : (
            <div className="divide-y divide-border">
              {unassignedStudents.map((student: GroupMember) => (
                <div key={student.id} className="flex items-center justify-between px-5 md:px-8 py-3 transition-colors hover:bg-btn-primary/[0.03]">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-8 h-8 rounded-full bg-btn-primary/10 flex items-center justify-center text-xs font-semibold text-btn-primary flex-shrink-0">
                      {student.name.charAt(0).toUpperCase()}
                    </div>
                    <span className="text-sm text-text-primary truncate">{student.name}</span>
                  </div>
                  <button
                    className="text-xs font-medium text-btn-primary bg-btn-primary/10 hover:bg-btn-primary hover:text-white px-3 py-1.5 rounded-lg border-none transition-colors cursor-pointer"
                    onClick={() => handleAddToGroup(student.id)}
                  >
                    Add
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Groups List */}
        <div className="bg-white rounded-2xl border border-border shadow-sm overflow-hidden">
          <div className="px-5 md:px-8 py-4 border-b border-border flex items-center justify-between">
            <h3 className="text-base font-semibold text-text-primary m-0">Groups</h3>
            <span className="text-xs font-medium text-text-secondary bg-bg-secondary px-2.5 py-1 rounded-full">
              {groups.length}
            </span>
          </div>
          {groups.length === 0 ? (
            <div className="px-5 md:px-8 py-8 flex flex-col items-center gap-2">
              <span className="text-3xl">📁</span>
              <p className="text-text-secondary text-sm m-0">No groups created yet.</p>
            </div>
          ) : (
            <div className="divide-y divide-border">
              {groups.map((group: CourseGroup) => (
                <div key={group.id}>
                  <div
                  className={`flex items-start justify-between gap-3 px-5 md:px-8 py-3.5 cursor-pointer transition-colors ${
                    selectedGroup === group.id
                      ? "bg-btn-primary/[0.05]"
                      : "hover:bg-btn-primary/[0.03]"
                  }`}
                  onClick={() => setSelectedGroup(selectedGroup === group.id ? -1 : group.id)}
                >
                  <div className="flex items-start gap-3 min-w-0 flex-1">
                    <span
                      className={`mt-0.5 flex-shrink-0 text-xs text-text-secondary transition-transform duration-200 ${
                        selectedGroup === group.id ? "rotate-90" : ""
                      }`}
                    >
                      &#9654;
                    </span>

                    <div className="min-w-0 flex-1 flex items-start gap-2">
                      <span className="text-sm font-medium text-text-primary break-words whitespace-normal">
                        {group.name}
                      </span>
                      {selectedGroup === group.id && (
                        <span className="mt-1 w-1.5 h-1.5 rounded-full bg-btn-primary flex-shrink-0" />
                      )}
                    </div>
                  </div>

                  <button
                    className="flex-shrink-0 text-xs px-2.5 py-1 rounded-md text-red-600 bg-red-50 hover:bg-red-100 border border-red-200 transition-colors cursor-pointer font-medium"
                    onClick={(e) => {
                      e.stopPropagation();
                      setDeleteTarget(group);
                    }}
                  >
                    Delete
                  </button>
                </div>
                  <GroupMembersPanel
                    group={group}
                    isOpen={selectedGroup === group.id}
                    onRemove={handleRemoveFromGroup}
                  />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Delete Group Confirmation Modal */}
      <Modal isOpen={deleteTarget !== null} onClose={() => setDeleteTarget(null)} title="Delete Group">
        <div className="flex flex-col gap-4">
          <p className="text-sm text-text-secondary m-0">
            Are you sure you want to delete <strong className="text-text-primary">{deleteTarget?.name}</strong>? All students in this group will become unassigned. This action cannot be undone.
          </p>
          <div className="flex gap-3 justify-end pt-2 border-t border-border">
            <button
              onClick={() => setDeleteTarget(null)}
              className="px-4 py-2 rounded-lg border border-border text-sm font-medium text-text-secondary hover:bg-bg-secondary transition-colors cursor-pointer bg-transparent"
            >
              Cancel
            </button>
            <button
              onClick={handleDeleteGroup}
              className="px-4 py-2 rounded-lg bg-red-600 text-white text-sm font-semibold border-none cursor-pointer transition-all hover:bg-red-700 active:scale-[0.98]"
            >
              Delete
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
