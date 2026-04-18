import { useState, useEffect } from "react";
import toast from "react-hot-toast";
import RubricCreator from "../reviews/RubricCreator";
import RubricDisplay from "../reviews/RubricDisplay";
import Modal from "../../ui/Modal";
import { useDeleteRubric, useUpdateRubric, useRubric, useCriteria } from "../reviews/useRubric";
import { cardClass, btnDanger, btnPrimary } from "./assignmentStyles";

interface Props {
  assignmentId: number;
  rubricId: number | null;
  groupRubricId: number | null;
  review: number[];
  groupReview: number[];
  onCriterionSelect: (row: number, column: number) => void;
  onCommentChange: (comment: string) => void;
}

type RubricTab = "individual" | "group";

interface EditCriterion {
  question: string;
  scoreMax: number;
  hasScore: boolean;
}

function RubricEditor({
  criteria,
  canComment: initialCanComment,
  onSave,
  onCancel,
  isSaving,
}: {
  criteria: EditCriterion[];
  canComment: boolean;
  onSave: (canComment: boolean, criteria: EditCriterion[]) => void;
  onCancel: () => void;
  isSaving: boolean;
}) {
  const [editCriteria, setEditCriteria] = useState<EditCriterion[]>(criteria);
  const [canComment, setCanComment] = useState(initialCanComment);

  const handleQuestionChange = (index: number, value: string) => {
    const updated = [...editCriteria];
    updated[index] = { ...updated[index], question: value };
    setEditCriteria(updated);
  };

  const handleScoreMaxChange = (index: number, value: number) => {
    const updated = [...editCriteria];
    updated[index] = { ...updated[index], scoreMax: Math.min(100, Math.max(1, value)) };
    setEditCriteria(updated);
  };

  const handleHasScoreChange = (index: number, value: boolean) => {
    const updated = [...editCriteria];
    updated[index] = {...updated[index], hasScore: value, scoreMax: value ? Math.max(1, updated[index].scoreMax) : 1};
    setEditCriteria(updated);
  };

  const handleAdd = () => setEditCriteria(prev => [...prev, { question: "", scoreMax: 1, hasScore: true }]);

  const handleRemove = (index: number) => setEditCriteria(prev => prev.filter((_, i) => i !== index));

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <h2 className="text-lg font-semibold text-text-primary m-0">Edit Rubric</h2>
        <label className="flex items-center gap-2.5 text-sm text-text-secondary cursor-pointer select-none">
          <div
            className={`relative w-9 h-5 rounded-full transition-colors ${canComment ? "bg-btn-primary" : "bg-gray-300"}`}
            onClick={() => setCanComment(prev => !prev)}
          >
            <div className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${canComment ? "translate-x-4" : ""}`} />
          </div>
          Allow comments
        </label>
      </div>

      <div className="flex flex-col gap-3">
        {editCriteria.map((item, index) => (
          <div key={index} className="group flex flex-col gap-3 p-4 bg-bg-secondary rounded-xl border border-border hover:border-btn-primary/30 transition-colors">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-text-secondary uppercase tracking-wide">
                Criterion {index + 1}
              </span>
              {editCriteria.length > 1 && (
                <button
                  onClick={() => handleRemove(index)}
                  className="text-xs px-2.5 py-1 rounded-md text-red-600 bg-red-50 hover:bg-red-100 border border-red-200 cursor-pointer transition-colors"
                >
                  Remove
                </button>
              )}
            </div>
            <input
              type="text"
              value={item.question}
              onChange={(e) => handleQuestionChange(index, e.target.value)}
              placeholder="e.g. How well did the student communicate their ideas?"
              className="w-full px-3.5 py-2.5 border border-border rounded-lg bg-white text-sm text-text-primary placeholder:text-text-secondary/50 focus:outline-none focus:ring-2 focus:ring-btn-primary/30 focus:border-btn-primary transition-all"
            />
            <div className="flex flex-wrap items-center gap-4">
              <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer">
                <input
                  type="checkbox"
                  checked={item.hasScore}
                  onChange={(e) => handleHasScoreChange(index, e.target.checked)}
                  className="w-4 h-4 accent-btn-primary"
                />
                Scored
              </label>
              {item.hasScore && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-text-secondary">Max:</span>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={item.scoreMax}
                    onChange={(e) => handleScoreMaxChange(index, Number(e.target.value))}
                    className="w-16 px-2.5 py-1.5 border border-border rounded-lg bg-white text-sm text-text-primary text-center focus:outline-none focus:ring-2 focus:ring-btn-primary/30 focus:border-btn-primary transition-all"
                  />
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <button
        onClick={handleAdd}
        className="w-full py-3 border-2 border-dashed border-border rounded-xl text-sm font-medium text-text-secondary hover:border-btn-primary/40 hover:text-btn-primary hover:bg-btn-primary/5 transition-all cursor-pointer bg-transparent"
      >
        + Add Criterion
      </button>

      <div className="flex gap-3 justify-end pt-2">
        <button
          onClick={onCancel}
          className="inline-flex items-center px-4 py-2 rounded-lg border border-border text-sm font-medium text-text-secondary hover:bg-bg-secondary transition-colors cursor-pointer bg-transparent"
        >
          Cancel
        </button>
        <button
          onClick={() => {
            const emptyQuestions = editCriteria.some(c => !c.question.trim());
            if (emptyQuestions) {
              toast.error("Please fill in all criterion questions.");
              return;
            }
            onSave(canComment, editCriteria);
          }}
          disabled={isSaving}
          className={btnPrimary + " disabled:opacity-60 disabled:cursor-not-allowed"}
        >
          {isSaving ? "Saving..." : "Save Changes"}
        </button>
      </div>
    </div>
  );
}

function RubricTabContent({
  assignmentId,
  rubricId,
  rubricType,
  review,
  onCriterionSelect,
  onCommentChange,
  onDeleteRequest,
  onEditRequest,
}: {
  assignmentId: number;
  rubricId: number | null;
  rubricType: RubricTab;
  review: number[];
  onCriterionSelect: (row: number, column: number) => void;
  onCommentChange: (comment: string) => void;
  onDeleteRequest: () => void;
  onEditRequest: () => void;
}) {
  if (rubricId) {
    return (
      <>
        <RubricDisplay rubricId={rubricId} onCriterionSelect={onCriterionSelect} onCommentChange={onCommentChange} grades={review} />
        <div className="mt-5 pt-4 border-t border-border flex items-center gap-3">
          <button className={btnPrimary} onClick={onEditRequest}>
            Edit Rubric
          </button>
          <button className={btnDanger} onClick={onDeleteRequest}>
            Delete Rubric
          </button>
        </div>
      </>
    );
  }

  return <RubricCreator id={assignmentId} rubricType={rubricType} />;
}

export default function ManageRubricSection({
  assignmentId,
  rubricId,
  groupRubricId,
  review,
  groupReview,
  onCriterionSelect,
  onCommentChange,
}: Props) {
  const [activeTab, setActiveTab] = useState<RubricTab>("individual");
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaveModalOpen, setIsSaveModalOpen] = useState(false);
  const [pendingSave, setPendingSave] = useState<{ canComment: boolean; criteria: EditCriterion[] } | null>(null);

  const currentRubricId = activeTab === "individual" ? rubricId : groupRubricId;
  const label = activeTab === "group" ? "Group Rubric" : "Individual Rubric";

  // Fetch rubric data (includes review_count) and criteria for edit mode
  const { data: rubricInfo } = useRubric(currentRubricId);
  const { data: criteriaData = [] } = useCriteria(currentRubricId);
  const reviewCount: number = rubricInfo?.review_count ?? 0;

  const { mutate: deleteIndividual, isPending: isDeletingIndividual } = useDeleteRubric(assignmentId, "individual");
  const { mutate: deleteGroup, isPending: isDeletingGroup } = useDeleteRubric(assignmentId, "group");
  const { mutate: updateIndividual, isPending: isUpdatingIndividual } = useUpdateRubric(assignmentId, "individual");
  const { mutate: updateGroup, isPending: isUpdatingGroup } = useUpdateRubric(assignmentId, "group");

  const deleteRubric = activeTab === "individual" ? deleteIndividual : deleteGroup;
  const updateRubric = activeTab === "individual" ? updateIndividual : updateGroup;
  const isDeleting = isDeletingIndividual || isDeletingGroup;
  const isUpdating = isUpdatingIndividual || isUpdatingGroup;

  // Exit edit mode when switching tabs
  useEffect(() => {
    setIsEditing(false);
  }, [activeTab]);

  const handleSaveRequest = (canComment: boolean, criteria: EditCriterion[]) => {
    if (reviewCount > 0) {
      setPendingSave({ canComment, criteria });
      setIsSaveModalOpen(true);
    } else {
      performUpdate(canComment, criteria);
    }
  };

  const performUpdate = (canComment: boolean, criteria: EditCriterion[]) => {
    if (!currentRubricId) return;
    updateRubric(
      { rubricId: currentRubricId, canComment, criteria },
      {
        onSuccess: () => {
          setIsEditing(false);
          setIsSaveModalOpen(false);
          setPendingSave(null);
          toast.success("Rubric updated successfully.");
        },
        onError: (error) => {
          setIsSaveModalOpen(false);
          setPendingSave(null);
          toast.error(error instanceof Error ? error.message : "Failed to update rubric.");
        },
      }
    );
  };

  const tabs: { key: RubricTab; label: string }[] = [
    { key: "individual", label: "Individual" },
    { key: "group", label: "Group" },
  ];

  return (
    <>
      <div className={cardClass}>
        <div className="px-5 md:px-8 py-4 border-b border-border flex items-center justify-between gap-4">
          <h3 className="text-base font-semibold text-text-primary m-0">Rubrics</h3>
          <div className="flex bg-bg-secondary rounded-lg p-0.5">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all cursor-pointer border-none ${
                  activeTab === tab.key
                    ? "bg-white text-text-primary shadow-sm"
                    : "bg-transparent text-text-secondary hover:text-text-primary"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
        <div className="px-5 md:px-8 py-5">
          {isEditing && currentRubricId ? (
            <RubricEditor
              criteria={criteriaData.map((c: Criterion) => ({
                question: c.question,
                scoreMax: c.scoreMax,
                hasScore: c.hasScore,
              }))}
              canComment={rubricInfo?.canComment ?? false}
              onSave={handleSaveRequest}
              onCancel={() => setIsEditing(false)}
              isSaving={isUpdating}
            />
          ) : (
            <RubricTabContent
              assignmentId={assignmentId}
              rubricId={activeTab === "individual" ? rubricId : groupRubricId}
              rubricType={activeTab}
              review={activeTab === "individual" ? review : groupReview}
              onCriterionSelect={onCriterionSelect}
              onCommentChange={onCommentChange}
              onDeleteRequest={() => setIsDeleteModalOpen(true)}
              onEditRequest={() => setIsEditing(true)}
            />
          )}
        </div>
      </div>

      {/* Delete confirmation modal */}
      <Modal isOpen={isDeleteModalOpen} onClose={() => setIsDeleteModalOpen(false)} title={`Delete ${label}`}>
        <div className="flex flex-col gap-4">
          <p className="text-sm text-text-secondary m-0">
            Are you sure you want to delete this rubric? All criteria will be permanently removed. This action cannot be undone.
          </p>
          {reviewCount > 0 && (
            <div className="flex items-start gap-3 p-3 bg-red-50 border border-red-200 rounded-lg">
              <span className="text-red-500 text-lg leading-none mt-0.5">&#9888;</span>
              <p className="text-sm text-red-700 m-0 font-medium">
                {reviewCount} review{reviewCount !== 1 ? "s" : ""} completed with this rubric will also be permanently deleted.
              </p>
            </div>
          )}
          <div className="flex gap-3 justify-end pt-2 border-t border-border">
            <button
              onClick={() => setIsDeleteModalOpen(false)}
              className="inline-flex items-center px-4 py-2 rounded-lg border border-border text-sm font-medium text-text-secondary hover:bg-bg-secondary transition-colors cursor-pointer bg-transparent"
            >
              Cancel
            </button>
            <button
              disabled={isDeleting}
              onClick={() => {
                if (!currentRubricId) return;
                deleteRubric(currentRubricId, {
                  onSuccess: () => {
                    setIsDeleteModalOpen(false);
                    toast.success("Rubric deleted successfully.");
                  },
                  onError: (error) => {
                    setIsDeleteModalOpen(false);
                    toast.error(error instanceof Error ? error.message : "Failed to delete rubric.");
                  },
                });
              }}
              className="inline-flex items-center px-4 py-2 rounded-lg bg-red-600 text-white text-sm font-semibold border-none cursor-pointer transition-all duration-150 hover:bg-red-700 active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {isDeleting ? "Deleting..." : "Delete"}
            </button>
          </div>
        </div>
      </Modal>

      {/* Save/update confirmation modal (shown when reviews exist) */}
      <Modal isOpen={isSaveModalOpen} onClose={() => { setIsSaveModalOpen(false); setPendingSave(null); }} title={`Update ${label}`}>
        <div className="flex flex-col gap-4">
          <p className="text-sm text-text-secondary m-0">
            Updating this rubric will replace all existing criteria with your changes.
          </p>
          <div className="flex items-start gap-3 p-3 bg-red-50 border border-red-200 rounded-lg">
            <span className="text-red-500 text-lg leading-none mt-0.5">&#9888;</span>
            <p className="text-sm text-red-700 m-0 font-medium">
              {reviewCount} review{reviewCount !== 1 ? "s" : ""} completed with the current rubric will be permanently deleted because the criteria are changing.
            </p>
          </div>
          <div className="flex gap-3 justify-end pt-2 border-t border-border">
            <button
              onClick={() => { setIsSaveModalOpen(false); setPendingSave(null); }}
              className="inline-flex items-center px-4 py-2 rounded-lg border border-border text-sm font-medium text-text-secondary hover:bg-bg-secondary transition-colors cursor-pointer bg-transparent"
            >
              Cancel
            </button>
            <button
              disabled={isUpdating}
              onClick={() => {
                if (pendingSave) {
                  performUpdate(pendingSave.canComment, pendingSave.criteria);
                }
              }}
              className="inline-flex items-center px-4 py-2 rounded-lg bg-red-600 text-white text-sm font-semibold border-none cursor-pointer transition-all duration-150 hover:bg-red-700 active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {isUpdating ? "Updating..." : "Update & Delete Reviews"}
            </button>
          </div>
        </div>
      </Modal>
    </>
  );
}
