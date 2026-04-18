import { useState, useEffect, ChangeEvent } from "react";
import toast from "react-hot-toast";
import Modal from "../../ui/Modal";
import RubricDisplay from "../reviews/RubricDisplay";
import { useSubmitReview, useReview, useUpdateReview, useMyReviewed } from "../reviews/useReviews";
import { useCriteria } from "../reviews/useRubric";
import { btnPrimary } from "./assignmentStyles";
import type { GroupMember } from "./useAssignmentDetail";

interface SelectedCriterion {
  row: number;
  column: number;
}

interface Props {
  assignmentId: number;
  rubricId: number | null;
  review: number[];
  groupMembers: GroupMember[];
  revieweeID: number;
  setRevieweeID: (id: number) => void;
}

export default function PeerReviewSection({ assignmentId, rubricId, review, groupMembers, revieweeID, setRevieweeID }: Props) {
  const [selectedCriteria, setSelectedCriteria] = useState<SelectedCriterion[]>([]);
  const [reviewComment, setReviewComment] = useState("");
  const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);
  const [selectedMemberName, setSelectedMemberName] = useState("");

  const { data: reviewedIds = [] } = useMyReviewed(assignmentId, "individual");
  const { mutate: submitReview, isPending: isSubmitting } = useSubmitReview();
  const { mutate: updateReviewMut, isPending: isUpdating } = useUpdateReview();
  const { data: existingReview } = useReview(assignmentId, revieweeID, "individual");
  const { data: rubricCriteria = [] } = useCriteria(rubricId);

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
    setRevieweeID(selectedID);
    const member = groupMembers.find((m) => m.id === selectedID);
    setSelectedMemberName(member?.name || "");
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
          revieweeID: revieweeID,
          criteria: criteriaPayload,
          comments: reviewComment,
        },
        {
          onSuccess: () => {
            if (closeModal) setIsReviewModalOpen(false);
            toast.success("Review updated successfully.");
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
          revieweeID,
          criteria: criteriaPayload,
          comments: reviewComment,
        },
        {
          onSuccess: () => {
            if (closeModal) setIsReviewModalOpen(false);
            toast.success("Review submitted successfully.");
          },
          onError: (error) => {
            toast.error(error instanceof Error ? error.message : "Failed to submit review.");
          },
        }
      );
    }
  }

  // Determine grades to display — from existing review or local state
  const displayGrades: number[] = isEditing
    ? existingReview.criteria?.map((c: { grade: number }) => c.grade) ?? []
    : review;

  return (
    <>
      <div>
        <div className="flex flex-col gap-4">
          <p className="text-sm text-text-secondary m-0">Select a group member to review</p>
          {groupMembers.length === 0 ? (
            <p className="text-text-secondary text-sm m-0">No group members found. You may not be assigned to a group yet.</p>
          ) : (
            <div className="flex flex-col gap-2">
              {groupMembers.map((member) => (
                <label key={member.id} className="flex items-center gap-2.5 cursor-pointer text-sm text-text-primary py-1">
                  <input
                    type="radio"
                    id={member.id.toString()}
                    value={member.id}
                    name="groupMembers"
                    onChange={handleRadioChange}
                    className="w-4 h-4 accent-btn-primary"
                  />
                  {member.name}
                  {reviewedIds.includes(member.id) && (
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
        title={`${isEditing ? "Edit" : "Review"}: ${selectedMemberName}`}
      >
        <RubricDisplay
          rubricId={rubricId}
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
