import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  submitReview,
  updateReview,
  getReview,
  getReviewsForAssignment,
  getMyReviewed,
  getMyProgress,
  getCourseGradeSummary,
} from "../../services/reviewApi";

export function useReview(
  assignmentId: number,
  revieweeId: number,
  review_type: "individual" | "group" = "individual"
) {
  return useQuery({
    queryKey: ["review", assignmentId, revieweeId, review_type],
    queryFn: async () => {
      const resp = await getReview(assignmentId, revieweeId, review_type);
      if (!resp.ok) return null;
      return resp.json();
    },
    enabled: !!assignmentId && revieweeId > 0,
  });
}

export function useReviewsForAssignment(
  assignmentId: number,
  review_type?: "individual" | "group"
) {
  return useQuery({
    queryKey: ["reviews", assignmentId, review_type],
    queryFn: () => getReviewsForAssignment(assignmentId, review_type),
    enabled: !!assignmentId,
  });
}

export function useMyProgress(courseId: number, enabled = true) {
  return useQuery({
    queryKey: ["my-progress", courseId],
    queryFn: () => getMyProgress(courseId),
    enabled: !!courseId && enabled,
  });
}

export function useCourseGradeSummary(courseId: number) {
  return useQuery({
    queryKey: ["grade-summary", courseId],
    queryFn: () => getCourseGradeSummary(courseId),
    enabled: !!courseId,
  });
}

export function useMyReviewed(
  assignmentId: number,
  review_type: "individual" | "group" = "individual"
) {
  return useQuery({
    queryKey: ["my-reviewed", assignmentId, review_type],
    queryFn: () => getMyReviewed(assignmentId, review_type),
    enabled: !!assignmentId,
  });
}

export function useSubmitReview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: {
      assignmentID: number;
      revieweeID: number;
      criteria: { criterionRowID: number; grade: number; comments: string }[];
      comments?: string;
      review_type?: "individual" | "group";
    }) =>
      submitReview(
        params.assignmentID,
        params.revieweeID,
        params.criteria,
        params.comments,
        params.review_type
      ),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["review", variables.assignmentID, variables.revieweeID],
      });
      queryClient.invalidateQueries({
        queryKey: ["reviews", variables.assignmentID],
      });
      queryClient.invalidateQueries({
        queryKey: ["my-reviewed", variables.assignmentID],
      });
    },
  });
}

export function useUpdateReview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: {
      reviewId: number;
      assignmentID: number;
      revieweeID: number;
      criteria: { criterionRowID: number; grade: number; comments: string }[];
      comments?: string;
    }) => updateReview(params.reviewId, params.criteria, params.comments),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["review", variables.assignmentID, variables.revieweeID],
      });
      queryClient.invalidateQueries({
        queryKey: ["reviews", variables.assignmentID],
      });
    },
  });
}
