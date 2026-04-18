import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getMySubmission,
  uploadMySubmission,
  deleteMySubmission,
} from "../../services/submissionApi";

export function useMySubmission(assignmentId: number, enabled = true) {
  return useQuery({
    queryKey: ["submission", assignmentId],
    queryFn: () => getMySubmission(assignmentId),
    enabled: enabled && !!assignmentId,
  });
}

export function useUploadSubmission(assignmentId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => uploadMySubmission(assignmentId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["submission", assignmentId],
      });
    },
  });
}

export function useDeleteSubmission(assignmentId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => deleteMySubmission(assignmentId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["submission", assignmentId],
      });
    },
  });
}
