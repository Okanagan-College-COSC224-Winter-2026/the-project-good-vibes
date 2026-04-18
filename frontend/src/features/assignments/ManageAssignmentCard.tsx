import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import toast from "react-hot-toast";
import Modal from "../../ui/Modal";
import { useEditAssignment, useDeleteAssignment } from "./useAssignments";
import { cardClass, btnPrimary, btnDanger, inputClass, labelClass } from "./assignmentStyles";

interface ManageFormData {
  name: string;
  description: string;
  start_date: string;
  due_date: string;
  is_anonymous: boolean;
  individual_reviews: boolean;
  group_reviews: boolean;
}

function toDatetimeLocal(value?: string) {
  if (!value) return "";
  // Backend returns naive UTC datetimes (no Z suffix).
  // Append Z so JavaScript parses them as UTC, not local time.
  const normalized = value.endsWith("Z") || value.includes("+") ? value : value + "Z";
  const parsed = new Date(normalized);
  if (Number.isNaN(parsed.getTime())) return "";
  return new Date(parsed.getTime() - parsed.getTimezoneOffset() * 60000)
    .toISOString()
    .slice(0, 16);
}

interface Props {
  assignmentId: number;
  assignment: { name: string; description?: string; start_date?: string; due_date?: string; is_anonymous?: boolean; individual_reviews?: boolean; group_reviews?: boolean; courseID: number };
}

export default function ManageAssignmentCard({ assignmentId, assignment }: Props) {
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isCascadeModalOpen, setIsCascadeModalOpen] = useState(false);
  const [pendingPayload, setPendingPayload] = useState<Record<string, unknown> | null>(null);

  const { register, handleSubmit, reset, watch } = useForm<ManageFormData>({
    defaultValues: { name: "", description: "", start_date: "", due_date: "", is_anonymous: true, individual_reviews: true, group_reviews: true },
  });

  const { mutate: editAssignment, isPending: isSaving } = useEditAssignment(assignmentId);
  const { mutate: deleteAssignment, isPending: isDeleting } = useDeleteAssignment();

  useEffect(() => {
    reset({
      name: assignment.name || "",
      description: assignment.description || "",
      start_date: toDatetimeLocal(assignment.start_date),
      due_date: toDatetimeLocal(assignment.due_date),
      is_anonymous: assignment.is_anonymous ?? true,
      individual_reviews: assignment.individual_reviews ?? true,
      group_reviews: assignment.group_reviews ?? true,
    });
  }, [assignment, reset]);

  // Build a human-readable warning about which review types are being disabled
  function getCascadeWarnings(data: ManageFormData): string[] {
    const warnings: string[] = [];
    if (assignment.individual_reviews && !data.individual_reviews) {
      warnings.push("Individual reviews");
    }
    if (assignment.group_reviews && !data.group_reviews) {
      warnings.push("Group reviews");
    }
    return warnings;
  }

  function buildPayload(data: ManageFormData) {
    const payload: Record<string, unknown> = {
      name: data.name,
      description: data.description,
      is_anonymous: data.is_anonymous,
      individual_reviews: data.individual_reviews,
      group_reviews: data.group_reviews,
    };
    if (data.start_date) payload.start_date = new Date(data.start_date).toISOString();
    if (data.due_date) payload.due_date = new Date(data.due_date).toISOString();
    return payload;
  }

  function savePayload(payload: Record<string, unknown>) {
    editAssignment(payload, {
      onSuccess: () => toast.success("Assignment updated successfully."),
      onError: (error) =>
        toast.error(error instanceof Error ? error.message : "Failed to update assignment."),
    });
  }

  function onSubmit(data: ManageFormData) {
    if (data.start_date && data.due_date) {
      const start = new Date(data.start_date);
      const due = new Date(data.due_date);

      if (start > due) {
        toast.error("Due date cannot be before start date.");
        return;
      }
    }

    const payload = buildPayload(data);
    const warnings = getCascadeWarnings(data);

    if (warnings.length > 0) {
      setPendingPayload(payload);
      setIsCascadeModalOpen(true);
      return;
    }

    savePayload(payload);
  }

  return (
    <>
      <div className={cardClass}>
        <div className="px-5 md:px-8 py-4 border-b border-border">
          <h3 className="text-base font-semibold text-text-primary m-0">Manage Assignment</h3>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="px-5 md:px-8 py-5 flex flex-col gap-4">
          <label className={labelClass}>
            Name
            <input type="text" className={inputClass} disabled={isSaving} {...register("name")} />
          </label>

          <label className={labelClass}>
            Description
            <textarea className={`${inputClass} min-h-[90px] resize-y`} disabled={isSaving} {...register("description")} />
          </label>

          <label className={labelClass}>
            Start date
            <input type="datetime-local" className={inputClass} disabled={isSaving} {...register("start_date")} />
          </label>

          <label className={labelClass}>
            Due date
            <input type="datetime-local" className={inputClass} disabled={isSaving} {...register("due_date")} />
          </label>

          <div className="flex flex-col gap-2.5">
            <span className="text-sm font-medium text-text-primary">Review Settings</span>
            <label className="flex flex-row items-center gap-2 cursor-pointer text-sm text-text-primary">
              <input type="checkbox" className="w-4 h-4 accent-btn-primary" disabled={isSaving} {...register("individual_reviews")} />
              Individual reviews
            </label>
            <label className="flex flex-row items-center gap-2 cursor-pointer text-sm text-text-primary">
              <input type="checkbox" className="w-4 h-4 accent-btn-primary" disabled={isSaving} {...register("group_reviews")} />
              Group reviews
            </label>
            <label className="inline-flex flex-row items-center gap-2.5 cursor-pointer mt-1 self-start">
              <span className="flex flex-col">
                <span className="text-sm text-text-primary">Anonymous</span>
                <span className="text-xs text-text-secondary">Hide reviewer identity from students</span>
              </span>
              <span className="relative inline-flex items-center shrink-0">
                <input type="checkbox" className="sr-only peer" disabled={isSaving} {...register("is_anonymous")} />
                <div className="w-9 h-5 bg-gray-300 rounded-full peer peer-checked:bg-btn-primary peer-disabled:opacity-50 transition-colors after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:after:translate-x-full" />
              </span>
            </label>
          </div>

          <div className="flex gap-3 flex-wrap pt-4 border-t border-border">
            <button type="submit" disabled={isSaving} className={btnPrimary}>
              {isSaving ? "Saving..." : "Save Changes"}
            </button>
            <button type="button" className={btnDanger} onClick={() => setIsDeleteModalOpen(true)}>
              Delete Assignment
            </button>
          </div>
        </form>
      </div>

      <Modal isOpen={isDeleteModalOpen} onClose={() => setIsDeleteModalOpen(false)} title="Delete Assignment">
        <div className="flex flex-col gap-4">
          <p className="text-sm text-text-secondary m-0">
            Are you sure you want to delete <strong className="text-text-primary">{assignment.name}</strong>? This will remove all submissions, reviews, and rubrics associated with it. This action cannot be undone.
          </p>
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
                deleteAssignment(assignmentId, {
                  onSuccess: () => {
                    toast.success("Assignment deleted.");
                    window.location.href = `/classes/${assignment.courseID}/home`;
                  },
                  onError: (error) => {
                    toast.error(error instanceof Error ? error.message : "Failed to delete assignment.");
                    setIsDeleteModalOpen(false);
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

      <Modal
        isOpen={isCascadeModalOpen}
        onClose={() => { setIsCascadeModalOpen(false); setPendingPayload(null); }}
        title="Disable Review Type"
      >
        <div className="flex flex-col gap-4">
          <p className="text-sm text-text-secondary m-0">
            You are about to disable{" "}
            <strong className="text-text-primary">
              {getCascadeWarnings(watch()).join(" and ").toLowerCase()}
            </strong>{" "}
            for this assignment. This will permanently delete the associated rubric and all submitted reviews of that type. This action cannot be undone.
          </p>
          <div className="flex gap-3 justify-end pt-2 border-t border-border">
            <button
              onClick={() => { setIsCascadeModalOpen(false); setPendingPayload(null); }}
              className="inline-flex items-center px-4 py-2 rounded-lg border border-border text-sm font-medium text-text-secondary hover:bg-bg-secondary transition-colors cursor-pointer bg-transparent"
            >
              Cancel
            </button>
            <button
              disabled={isSaving}
              onClick={() => {
                if (pendingPayload) {
                  savePayload(pendingPayload);
                  setIsCascadeModalOpen(false);
                  setPendingPayload(null);
                }
              }}
              className="inline-flex items-center px-4 py-2 rounded-lg bg-red-600 text-white text-sm font-semibold border-none cursor-pointer transition-all duration-150 hover:bg-red-700 active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {isSaving ? "Saving..." : "Disable & Delete"}
            </button>
          </div>
        </div>
      </Modal>
    </>
  );
}
