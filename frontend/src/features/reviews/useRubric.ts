import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getRubricForAssignment,
  getRubric,
  getCriteria,
  createRubric,
  createCriteria,
  updateRubric,
  deleteRubric,
} from "../../services/rubricApi";

export function useRubricForAssignment(
  assignmentId: number,
  rubric_type: "individual" | "group" = "individual"
) {
  return useQuery({
    queryKey: ["rubric", "assignment", assignmentId, rubric_type],
    queryFn: () => getRubricForAssignment(assignmentId, rubric_type),
    enabled: !!assignmentId,
  });
}

export function useRubric(rubricId: number | null) {
  return useQuery({
    queryKey: ["rubric", rubricId],
    queryFn: () => getRubric(rubricId!),
    enabled: rubricId !== null,
  });
}

export function useCriteria(rubricId: number | null) {
  return useQuery({
    queryKey: ["criteria", rubricId],
    queryFn: () => getCriteria(rubricId!),
    enabled: rubricId !== null,
  });
}

export function useCreateRubric(
  assignmentId: number,
  rubric_type: "individual" | "group" = "individual"
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: {
      canComment: boolean;
      criteria: { question: string; scoreMax: number; hasScore: boolean }[];
    }) =>
      createRubric(assignmentId, params.canComment, rubric_type).then(async ({ id }) => {
        await Promise.all(
          params.criteria.map((c) =>
            createCriteria(id, c.question, c.scoreMax, params.canComment, c.hasScore)
          )
        );
        return id;
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["rubric", "assignment", assignmentId, rubric_type],
      });
    },
  });
}

export function useUpdateRubric(
  assignmentId: number,
  rubric_type: "individual" | "group" = "individual"
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: {
      rubricId: number;
      canComment?: boolean;
      criteria: { question: string; scoreMax: number; hasScore: boolean }[];
    }) => updateRubric(params.rubricId, { canComment: params.canComment, criteria: params.criteria }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["rubric", "assignment", assignmentId, rubric_type],
      });
      queryClient.invalidateQueries({ queryKey: ["criteria"] });
    },
  });
}

export function useDeleteRubric(
  assignmentId: number,
  rubric_type: "individual" | "group" = "individual"
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (rubricId: number) => deleteRubric(rubricId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["rubric", "assignment", assignmentId, rubric_type],
      });
    },
  });
}
