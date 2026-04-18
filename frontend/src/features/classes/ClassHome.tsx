import Button from "../../ui/Button";
import { useParams, Link } from "react-router-dom";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useAssignments, useCreateAssignment } from "../assignments/useAssignments";
import { isTeacher } from "../../util/login";
import { formatDueDate, getAssignmentStatus, getTeacherAssignmentStatus } from "../../util/assignmentDates";
import { useMyProgress } from "../reviews/useReviews";
import Modal from "../../ui/Modal";

function getStatusClasses(status: string): string {
  const base = "text-xs font-medium rounded-full px-2.5 py-0.5 whitespace-nowrap"
  if (status === "Upcoming" || status === "Open") return `${base} bg-emerald-50 text-emerald-700 border border-emerald-200`
  if (status === "Overdue" || status === "Closed") return `${base} bg-red-50 text-red-700 border border-red-200`
  if (status === "Submitted") return `${base} bg-blue-50 text-blue-700 border border-blue-200`
  return `${base} bg-slate-100 text-text-secondary border border-border`
}

interface AssignmentFormData {
  name: string;
  description: string;
  start_date: string;
  due_date: string;
  is_anonymous: boolean;
  individual_reviews: boolean;
  group_reviews: boolean;
}

const inputClass =
  "px-3 py-2 border border-border rounded-lg bg-bg-secondary text-text-primary text-sm w-full focus:outline-none focus:ring-2 focus:ring-btn-primary focus:border-btn-primary transition-colors";

export default function ClassHome() {
  const { id } = useParams();
  const courseId = Number(id);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const teacherMode = isTeacher();
  const { data: assignments = [] } = useAssignments(String(id));
  const { data: progressData } = useMyProgress(courseId, !teacherMode);
  const { mutate: createAssignment, isPending, isSuccess, isError, error } = useCreateAssignment(String(id));

  // Build a lookup map: assignment_id → { completed, required }
  const progressMap = new Map<number, { completed: number; required: number }>();
  if (progressData?.assignments) {
    for (const a of progressData.assignments) {
      progressMap.set(a.assignment_id, {
        completed: a.individual_completed + a.group_completed,
        required: a.individual_required + a.group_required,
      });
    }
  }

  const { register, handleSubmit, reset, formState: { errors } } = useForm<AssignmentFormData>({
    defaultValues: {
      name: "",
      description: "",
      start_date: "",
      due_date: "",
      is_anonymous: true,
      individual_reviews: true,
      group_reviews: true,
    },
  });

  function onSubmit(data: AssignmentFormData) {
    createAssignment(
      {
        courseID: courseId,
        name: data.name,
        description: data.description || undefined,
        start_date: data.start_date || undefined,
        due_date: data.due_date || undefined,
        is_anonymous: data.is_anonymous,
        individual_reviews: data.individual_reviews,
        group_reviews: data.group_reviews,
      },
      {
        onSuccess: () => {
          reset();
          setIsModalOpen(false);
        },
      }
    );
  }

  function handleOpenModal() {
    reset();
    setIsModalOpen(true);
  }

  function handleCloseModal() {
    reset();
    setIsModalOpen(false);
  }

  return (
    <>
      {isSuccess && !isModalOpen && (
        <div className="mx-4 md:mx-6 mt-4 px-4 py-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm">
          Assignment created successfully!
        </div>
      )}

      {isError && (
        <div className="mx-4 md:mx-6 mt-4 px-4 py-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
          {error instanceof Error ? error.message : "Error creating assignment."}
        </div>
      )}

      <div className="p-4 md:p-6 w-full">
        <div className="flex flex-col items-stretch w-full gap-5">
          <div className="flex justify-between items-center gap-4">
            <h3 className="m-0 text-text-primary text-base font-semibold">Assignments</h3>
            {teacherMode && (
              <Button onClick={handleOpenModal}>+ New Assignment</Button>
            )}
          </div>

          <div className="bg-white rounded-2xl border border-border shadow-sm overflow-hidden">
            <div className="px-5 md:px-8 py-4 border-b border-border">
              <h3 className="text-base font-semibold text-text-primary m-0">All Assignments</h3>
            </div>

            {assignments.length === 0 ? (
              <div className="px-5 md:px-8 py-8 flex flex-col items-center gap-2">
                <span className="text-3xl">📝</span>
                <p className="text-text-secondary text-sm m-0">No assignments yet.</p>
              </div>
            ) : (
              <div className="divide-y divide-border">
                {assignments.map((assignment: Assignment) => {
                  const status = teacherMode
                    ? getTeacherAssignmentStatus(assignment.due_date)
                    : getAssignmentStatus(assignment.due_date, assignment.has_submitted);
                  const progress = progressMap.get(assignment.id);
                  const isComplete = progress && progress.required > 0 && progress.completed >= progress.required;
                  return (
                    <Link
                      key={assignment.id}
                      to={`/classes/${id}/assignments/${assignment.id}`}
                      className="px-5 md:px-8 py-4 flex items-center justify-between gap-4 no-underline text-inherit transition-colors hover:bg-btn-primary/[0.03] group"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
                          status === "Submitted" ? "bg-blue-500" : status === "Upcoming" || status === "Open" ? "bg-emerald-500" : status === "Overdue" || status === "Closed" ? "bg-red-400" : "bg-gray-300"
                        }`} />
                        <div className="min-w-0">
                          <span className="font-medium text-sm text-text-primary group-hover:text-btn-primary transition-colors block truncate">
                            {assignment.name}
                          </span>
                          <span className="text-xs text-text-secondary mt-0.5 block">
                            Due: {formatDueDate(assignment.due_date)}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        {!teacherMode && progress && progress.required > 0 && (
                          <span className={`text-xs font-medium rounded-full px-2.5 py-0.5 whitespace-nowrap ${
                            isComplete
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                              : "bg-amber-50 text-amber-700 border border-amber-200"
                          }`}>
                            {progress.completed}/{progress.required} reviews
                          </span>
                        )}
                        <span className={getStatusClasses(status)}>{status}</span>
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        <Modal isOpen={isModalOpen} onClose={handleCloseModal} title="Create New Assignment">
          <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
            <label className="flex flex-col gap-1.5">
              <span className="text-text-primary text-sm font-medium">Assignment Name</span>
              <input
                type="text"
                placeholder="Enter assignment name..."
                className={inputClass}
                disabled={isPending}
                {...register("name", { required: "Assignment name is required" })}
              />
              {errors.name && <span className="text-red-500 text-xs">{errors.name.message}</span>}
            </label>

            <label className="flex flex-col gap-1.5">
              <span className="text-text-primary text-sm font-medium">Description</span>
              <textarea
                className={`${inputClass} min-h-[110px] resize-y font-[inherit]`}
                placeholder="Enter assignment description..."
                disabled={isPending}
                {...register("description")}
              />
            </label>

            <label className="flex flex-col gap-1.5">
              <span className="text-text-primary text-sm font-medium">Start Date</span>
              <input type="datetime-local" className={inputClass} disabled={isPending} {...register("start_date")} />
            </label>

            <label className="flex flex-col gap-1.5">
              <span className="text-text-primary text-sm font-medium">Due Date</span>
              <input type="datetime-local" className={inputClass} disabled={isPending} {...register("due_date")} />
            </label>

            <div className="flex flex-col gap-2.5">
              <span className="text-sm font-medium text-text-primary">Review Settings</span>
              <label className="flex flex-row items-center gap-2 cursor-pointer text-sm text-text-primary">
                <input type="checkbox" className="w-4 h-4 accent-btn-primary" disabled={isPending} {...register("individual_reviews")} />
                Individual reviews
              </label>
              <label className="flex flex-row items-center gap-2 cursor-pointer text-sm text-text-primary">
                <input type="checkbox" className="w-4 h-4 accent-btn-primary" disabled={isPending} {...register("group_reviews")} />
                Group reviews
              </label>
              <label className="inline-flex flex-row items-center gap-2.5 cursor-pointer mt-1 self-start">
                <span className="flex flex-col">
                  <span className="text-sm text-text-primary">Anonymous</span>
                  <span className="text-xs text-text-secondary">Hide reviewer identity from students</span>
                </span>
                <span className="relative inline-flex items-center shrink-0">
                  <input type="checkbox" className="sr-only peer" disabled={isPending} {...register("is_anonymous")} />
                  <div className="w-9 h-5 bg-gray-300 rounded-full peer peer-checked:bg-btn-primary peer-disabled:opacity-50 transition-colors after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:after:translate-x-full" />
                </span>
              </label>
            </div>

            <div className="flex gap-3 mt-2 justify-end pt-2 border-t border-border">
              <Button onClick={handleCloseModal} type="secondary">Cancel</Button>
              <button
                type="submit"
                disabled={isPending}
                className="inline-flex items-center justify-center px-4 py-2.5 rounded-lg bg-btn-primary text-white text-sm font-semibold border-none cursor-pointer transition-all duration-150 hover:brightness-110 active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {isPending ? "Creating..." : "Create Assignment"}
              </button>
            </div>
          </form>
        </Modal>

      </div>
    </>
  );
}
