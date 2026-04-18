import { useState, useEffect, ChangeEvent } from "react";
import { useQuery } from "@tanstack/react-query";
import toast from "react-hot-toast";
import Modal from "../../ui/Modal";
import RubricDisplay from "../reviews/RubricDisplay";
import { useSubmitReview, useReview, useUpdateReview, useMyReviewed } from "../reviews/useReviews";
import { useCriteria } from "../reviews/useRubric";
import { listGroupMembers } from "../../services/groupApi";
import { getStudentSubmission } from "../../services/submissionApi";
import { btnPrimary } from "./assignmentStyles";
import type { CourseGroupItem } from "./useAssignmentDetail";

interface SelectedCriterion {
  row: number;
  column: number;
}

interface Props {
  assignmentId: number;
  groupRubricId: number | null;
  otherGroups: CourseGroupItem[];
  groupRevieweeID: number;
  setGroupRevieweeID: (id: number) => void;
}

export default function GroupReviewSection({
  assignmentId,
  groupRubricId,
  otherGroups,
  groupRevieweeID,
  setGroupRevieweeID,
}: Props) {
  const [selectedCriteria, setSelectedCriteria] = useState<SelectedCriterion[]>([]);
  const [reviewComment, setReviewComment] = useState("");
  const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);
  const [selectedGroupName, setSelectedGroupName] = useState("");

  const { data: reviewedIds = [] } = useMyReviewed(assignmentId, "group");
  const { mutate: submitReview, isPending: isSubmitting } = useSubmitReview();
  const { mutate: updateReviewMut, isPending: isUpdating } = useUpdateReview();
  const { data: existingReview } = useReview(assignmentId, groupRevieweeID, "group");
  const { data: rubricCriteria = [] } = useCriteria(groupRubricId);

  const isEditing = existingReview?.review !== undefined && existingReview?.review !== null;
  const isPending = isSubmitting || isUpdating;

  // Seed selectedCriteria from existing review when data loads
  useEffect(() => {
    if (isEditing && existingReview?.criteria && rubricCriteria.length > 0 && isReviewModalOpen) {
      const seeded = existingReview.criteria.map((c: { criterionRowID: number; grade: number }) => ({
        row: c.criterionRowID,
        column: c.grade,
      }));
      setSelectedCriteria(seeded);
      setReviewComment(existingReview.review.comments || "");
    }
  }, [isEditing, existingReview, rubricCriteria, isReviewModalOpen]);

  function handleCriterionSelect(row: number, column: number) {
    setSelectedCriteria((prev) => {
      const filtered = prev.filter((c) => c.row !== row);
      return [...filtered, { row, column }];
    });
  }

  function handleRadioChange(event: ChangeEvent<HTMLInputElement>) {
    const selectedID = Number(event.target.value);
    setGroupRevieweeID(selectedID);
    const group = otherGroups.find((g) => g.id === selectedID);
    setSelectedGroupName(group?.name || "");
    setSelectedCriteria([]);
    setReviewComment("");
    setIsReviewModalOpen(true);
  }

  function handleSubmitOrUpdate(closeModal?: boolean) {
    const criteriaPayload = selectedCriteria.map((c) => ({
      criterionRowID: c.row,
      grade: c.column,
      comments: "",
    }));

    if (isEditing) {
      updateReviewMut(
        {
          reviewId: existingReview.review.id,
          assignmentID: assignmentId,
          revieweeID: groupRevieweeID,
          criteria: criteriaPayload,
          comments: reviewComment,
        },
        {
          onSuccess: () => {
            if (closeModal) setIsReviewModalOpen(false);
            toast.success("Group review updated successfully.");
          },
          onError: (error) => {
            toast.error(error instanceof Error ? error.message : "Failed to update review.");
          },
        }
      );
    } else {
      submitReview(
        {
          assignmentID: assignmentId,
          revieweeID: groupRevieweeID,
          criteria: criteriaPayload,
          comments: reviewComment,
          review_type: "group",
        },
        {
          onSuccess: () => {
            if (closeModal) setIsReviewModalOpen(false);
            toast.success("Group review submitted successfully.");
          },
          onError: (error) => {
            toast.error(error instanceof Error ? error.message : "Failed to submit review.");
          },
        }
      );
    }
  }

  // Fetch a group member's ID to look up the group's submission
  const { data: groupMembers } = useQuery({
    queryKey: ["groupMembers", groupRevieweeID],
    queryFn: () => listGroupMembers(groupRevieweeID),
    enabled: isReviewModalOpen && groupRevieweeID > 0,
  });

  const firstMemberId = groupMembers?.[0]?.id ?? 0;

  const { data: groupSubmission } = useQuery({
    queryKey: ["studentSubmission", assignmentId, firstMemberId],
    queryFn: () => getStudentSubmission(assignmentId, firstMemberId),
    enabled: isReviewModalOpen && firstMemberId > 0,
  });

  // Only pre-populate grades from an existing review; new reviews use Criterion's internal state
  const displayGrades: number[] = isEditing
    ? existingReview.criteria?.map((c: { grade: number }) => c.grade) ?? []
    : [];

  return (
    <>
      <div>
        <div className="flex flex-col gap-4">
          <p className="text-sm text-text-secondary m-0">Select a group to review</p>
          {otherGroups.length === 0 ? (
            <p className="text-text-secondary text-sm m-0">No other groups found in this course.</p>
          ) : (
            <div className="flex flex-col gap-2">
              {otherGroups.map((group) => (
                <label key={group.id} className="flex items-center gap-2.5 cursor-pointer text-sm text-text-primary py-1">
                  <input
                    type="radio"
                    id={`group-${group.id}`}
                    value={group.id}
                    name="reviewGroup"
                    onChange={handleRadioChange}
                    className="w-4 h-4 accent-btn-primary"
                  />
                  {group.name}
                  {reviewedIds.includes(group.id) && (
                    <span className="text-xs text-emerald-600 font-medium">(reviewed)</span>
                  )}
                </label>
              ))}
            </div>
          )}
        </div>
      </div>

      <Modal
        isOpen={isReviewModalOpen}
        onClose={() => setIsReviewModalOpen(false)}
        title={`${isEditing ? "Edit" : "Review"}: ${selectedGroupName}`}
      >
        <div className="mb-4">
          <h4 className="text-sm font-semibold text-text-secondary uppercase tracking-wide m-0 mb-3">
            Submission
          </h4>
          {groupSubmission ? (
            <div className="flex items-center gap-2 px-4 py-3 bg-bg-secondary rounded-xl border border-border">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-btn-primary shrink-0">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
              <a
                href={groupSubmission.download_url}
                className="text-sm font-medium text-btn-primary hover:underline"
                download
              >
                {groupSubmission.filename}
              </a>
            </div>
          ) : (
            <p className="text-sm text-text-secondary m-0">No file submitted by this group yet.</p>
          )}
        </div>
        <RubricDisplay
          rubricId={groupRubricId}
          onCriterionSelect={handleCriterionSelect}
          onCommentChange={setReviewComment}
          grades={displayGrades}
          comment={reviewComment}
        />
        <div className="flex justify-end pt-4 mt-2 border-t border-border">
          <button className={btnPrimary} disabled={isPending || rubricCriteria.length === 0} onClick={() => handleSubmitOrUpdate(true)}>
            {isPending ? "Saving..." : isEditing ? "Update Review" : "Submit Review"}
          </button>
        </div>
      </Modal>
    </>
  );
}
