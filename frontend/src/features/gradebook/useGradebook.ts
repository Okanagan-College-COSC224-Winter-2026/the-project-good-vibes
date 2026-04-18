import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getGradebook,
  setGradeOverride,
  clearGradeOverride,
  getStudentReviews,
} from "../../services/gradebookApi";

export function useGradebook(courseId: number) {
  return useQuery({
    queryKey: ["gradebook", courseId],
    queryFn: () => getGradebook(courseId),
    enabled: !!courseId,
  });
}

export function useSetGradeOverride(courseId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: {
      studentID: number;
      assignmentID: number;
      overrideScore: number;
    }) =>
      setGradeOverride(
        courseId,
        params.studentID,
        params.assignmentID,
        params.overrideScore
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["gradebook", courseId] });
    },
  });
}

export function useClearGradeOverride(courseId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: { studentID: number; assignmentID: number }) =>
      clearGradeOverride(courseId, params.studentID, params.assignmentID),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["gradebook", courseId] });
    },
  });
}

export function useStudentReviews(
  courseId: number,
  studentId: number,
  assignmentId: number
) {
  return useQuery({
    queryKey: ["student-reviews", courseId, studentId, assignmentId],
    queryFn: () => getStudentReviews(courseId, studentId, assignmentId),
    enabled: !!courseId && !!studentId && !!assignmentId,
  });
}
