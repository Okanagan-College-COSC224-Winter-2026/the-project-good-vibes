import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listAssignments,
  getAssignment,
  createAssignment,
  editAssignment,
  deleteAssignment,
  listAssignmentResources,
  uploadAssignmentResource,
  deleteAssignmentResource,
} from "../../services/assignmentApi";

export function useAssignments(classId: string) {
  return useQuery({
    queryKey: ["assignments", classId],
    queryFn: () => listAssignments(classId),
    enabled: !!classId,
  });
}

export function useAssignment(assignmentId: number) {
  return useQuery({
    queryKey: ["assignment", assignmentId],
    queryFn: () => getAssignment(assignmentId),
    enabled: !!assignmentId,
  });
}

export function useCreateAssignment(classId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: {
      courseID: number;
      name: string;
      description?: string;
      start_date?: string;
      due_date?: string;
      is_anonymous?: boolean;
      individual_reviews?: boolean;
      group_reviews?: boolean;
    }) =>
      createAssignment(
        params.courseID,
        params.name,
        params.description,
        params.start_date,
        params.due_date,
        params.is_anonymous,
        params.individual_reviews,
        params.group_reviews
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignments", classId] });
    },
  });
}

export function useEditAssignment(assignmentId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      name?: string;
      description?: string;
      start_date?: string;
      due_date?: string;
      is_anonymous?: boolean;
      individual_reviews?: boolean;
      group_reviews?: boolean;
    }) => editAssignment(assignmentId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignment", assignmentId] });
    },
  });
}

export function useDeleteAssignment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (assignmentId: number) => deleteAssignment(assignmentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignments"] });
    },
  });
}



export function useAssignmentResources(assignmentId: number) {
  return useQuery({
    queryKey: ["assignment-resources", assignmentId],
    queryFn: () => listAssignmentResources(assignmentId),
    enabled: !!assignmentId,
  });
}

export function useUploadAssignmentResource(assignmentId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => uploadAssignmentResource(assignmentId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["assignment-resources", assignmentId],
      });
    },
  });
}

export function useDeleteAssignmentResource(assignmentId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (resourceId: number) => deleteAssignmentResource(resourceId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["assignment-resources", assignmentId],
      });
    },
  });
}
