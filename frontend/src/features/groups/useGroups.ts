import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listGroups,
  listStuGroup,
  listUnassignedStudents,
  listGroupMembers,
  createGroup,
  deleteGroup,
  addGroupMember,
  removeGroupMember,
} from "../../services/groupApi";

export function useGroups(courseId: number) {
  return useQuery({
    queryKey: ["groups", courseId],
    queryFn: () => listGroups(courseId),
    enabled: !!courseId,
  });
}

export function useMyGroup(courseId: number) {
  return useQuery({
    queryKey: ["my-group", courseId],
    queryFn: () => listStuGroup(courseId),
    enabled: !!courseId,
  });
}

export function useUnassignedStudents(courseId: number) {
  return useQuery({
    queryKey: ["unassigned-students", courseId],
    queryFn: () => listUnassignedStudents(courseId),
    enabled: !!courseId,
  });
}

export function useGroupMembers(groupId: number) {
  return useQuery({
    queryKey: ["group-members", groupId],
    queryFn: () => listGroupMembers(groupId),
    enabled: !!groupId,
  });
}

export function useCreateGroup(courseId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => createGroup(courseId, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["groups", courseId] });
      queryClient.invalidateQueries({ queryKey: ["unassigned-students", courseId] });
    },
  });
}

export function useDeleteGroup(courseId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (groupId: number) => deleteGroup(groupId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["groups", courseId] });
      queryClient.invalidateQueries({ queryKey: ["unassigned-students", courseId] });
    },
  });
}

export function useAddGroupMember(courseId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: { groupId: number; userId: number }) =>
      addGroupMember(params.groupId, params.userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["groups", courseId] });
      queryClient.invalidateQueries({ queryKey: ["group-members"] });
      queryClient.invalidateQueries({ queryKey: ["unassigned-students", courseId] });
    },
  });
}

export function useRemoveGroupMember(courseId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: { groupId: number; userId: number }) =>
      removeGroupMember(params.groupId, params.userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["groups", courseId] });
      queryClient.invalidateQueries({ queryKey: ["group-members"] });
      queryClient.invalidateQueries({ queryKey: ["unassigned-students", courseId] });
    },
  });
}
