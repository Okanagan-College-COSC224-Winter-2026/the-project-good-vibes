import { useState } from "react";
import { useParams } from "react-router-dom";
import { useGradebook, useSetGradeOverride, useClearGradeOverride } from "./useGradebook";
import GradeCell from "./GradeCell";
import ReviewDetailModal from "./ReviewDetailModal";

interface GradeData {
  individualAverage: number | null;
  individualMax: number | null;
  groupAverage: number | null;
  groupMax: number | null;
  overrideScore: number | null;
  effectiveGrade: number | null;
  effectiveMax: number | null;
}

interface ProgressData {
  completed: number;
  required: number;
}

interface StudentRow {
  id: number;
  name: string;
  email: string;
  grades: Record<string, GradeData>;
  courseTotal: { earned: number; max: number };
  reviewProgress?: Record<string, ProgressData>;
  reviewTotal?: ProgressData;
}

interface AssignmentCol {
  id: number;
  name: string;
}

interface ModalTarget {
  studentId: number;
  studentName: string;
  assignmentId: number;
  assignmentName: string;
}

export default function Gradebook() {
  const { id } = useParams();
  const courseId = Number(id);

  const { data, isLoading } = useGradebook(courseId);
  const setOverride = useSetGradeOverride(courseId);
  const clearOverride = useClearGradeOverride(courseId);

  const [modalTarget, setModalTarget] = useState<ModalTarget | null>(null);
  const [viewMode, setViewMode] = useState<"grades" | "reviews">("grades");

  const assignments: AssignmentCol[] = data?.assignments ?? [];
  const students: StudentRow[] = data?.students ?? [];

  if (isLoading) {
    return (
      <div className="p-4 md:p-8 w-full mx-auto">
        <h2 className="text-2xl font-semibold text-text-primary m-0 mb-6">Gradebook</h2>
        <p className="text-text-secondary text-sm">Loading gradebook...</p>
      </div>
    );
  }

  if (assignments.length === 0 && students.length === 0) {
    return (
      <div className="p-4 md:p-8 w-full mx-auto">
        <h2 className="text-2xl font-semibold text-text-primary m-0 mb-6">Gradebook</h2>
        <div className="bg-white rounded-2xl border border-border shadow-sm overflow-hidden">
          <div className="px-5 md:px-8 py-8 flex flex-col items-center gap-2">
            <p className="text-text-secondary text-sm m-0">
              No students or assignments in this course yet.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="p-4 md:p-8 w-full mx-auto flex flex-col gap-6">
        <div className="flex items-center justify-between gap-4">
          <h2 className="text-2xl font-semibold text-text-primary m-0">Gradebook</h2>
          <div className="flex rounded-lg border border-border overflow-hidden text-sm">
            <button
              onClick={() => setViewMode("grades")}
              className={`px-3.5 py-1.5 font-medium border-none cursor-pointer transition-colors ${
                viewMode === "grades"
                  ? "bg-btn-primary text-white"
                  : "bg-white text-text-secondary hover:bg-bg-secondary"
              }`}
            >
              Grades
            </button>
            <button
              onClick={() => setViewMode("reviews")}
              className={`px-3.5 py-1.5 font-medium border-none cursor-pointer transition-colors ${
                viewMode === "reviews"
                  ? "bg-btn-primary text-white"
                  : "bg-white text-text-secondary hover:bg-bg-secondary"
              }`}
            >
              Reviews
            </button>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-border shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-max border-collapse text-sm">
              <thead>
                <tr className="bg-bg-secondary border-b border-border">
                  <th className="text-left px-4 py-3 font-semibold text-text-primary sticky left-0 bg-bg-secondary z-10 min-w-[200px] border-r border-border">
                    Student
                  </th>
                  {assignments.map((a) => (
                    <th
                      key={a.id}
                      className="text-center px-4 py-3 font-semibold text-text-primary min-w-[120px]"
                    >
                      {a.name}
                    </th>
                  ))}
                  <th className="text-center px-4 py-3 font-semibold text-text-primary min-w-[120px] sticky right-0 bg-bg-secondary z-10 border-l border-border">
                    {viewMode === "grades" ? "Course Total" : "Total Reviews"}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {students.map((student) => {
                  const pcts = assignments
                    .map((a) => student.grades[String(a.id)])
                    .filter((g) => g?.effectiveGrade != null && g?.effectiveMax && g.effectiveMax > 0)
                    .map((g) => g.effectiveGrade! / g.effectiveMax!);
                  const totalPct = pcts.length > 0
                    ? (pcts.reduce((s, p) => s + p, 0) / pcts.length * 100).toFixed(0)
                    : null;

                  return (
                    <tr
                      key={student.id}
                      className="hover:bg-bg-secondary/50 transition-colors"
                    >
                      <td className="px-4 py-3 sticky left-0 bg-white z-10 border-r border-border">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-btn-primary/10 text-btn-primary flex items-center justify-center text-xs font-semibold shrink-0">
                            {student.name.charAt(0)}
                          </div>
                          <div className="min-w-0">
                            <div className="font-medium text-text-primary truncate">
                              {student.name}
                            </div>
                            <div className="text-xs text-text-secondary truncate">
                              {student.email}
                            </div>
                          </div>
                        </div>
                      </td>

                      {viewMode === "grades" ? (
                        <>
                          {assignments.map((a) => {
                            const grade = student.grades[String(a.id)];
                            return (
                              <GradeCell
                                key={a.id}
                                effectiveGrade={grade?.effectiveGrade ?? null}
                                effectiveMax={grade?.effectiveMax ?? null}
                                isOverridden={grade?.overrideScore != null}
                                onSetOverride={(score) =>
                                  setOverride.mutate({
                                    studentID: student.id,
                                    assignmentID: a.id,
                                    overrideScore: score,
                                  })
                                }
                                onClearOverride={() =>
                                  clearOverride.mutate({
                                    studentID: student.id,
                                    assignmentID: a.id,
                                  })
                                }
                                onClickDetails={() =>
                                  setModalTarget({
                                    studentId: student.id,
                                    studentName: student.name,
                                    assignmentId: a.id,
                                    assignmentName: a.name,
                                  })
                                }
                              />
                            );
                          })}
                          <td className="px-4 py-3 text-center sticky right-0 bg-white z-10 border-l border-border">
                            <span className="font-bold text-btn-primary text-sm">
                              {totalPct !== null ? `${totalPct}%` : "--"}
                            </span>
                          </td>
                        </>
                      ) : (
                        <>
                          {assignments.map((a) => {
                            const p = student.reviewProgress?.[String(a.id)];
                            if (!p || p.required === 0) {
                              return (
                                <td key={a.id} className="px-4 py-3 text-center text-text-secondary">
                                  --
                                </td>
                              );
                            }
                            const done = p.completed >= p.required;
                            return (
                              <td key={a.id} className="px-4 py-3 text-center">
                                <span className={`text-sm font-medium ${done ? "text-emerald-600" : "text-amber-600"}`}>
                                  {p.completed}/{p.required}
                                </span>
                              </td>
                            );
                          })}
                          <td className="px-4 py-3 text-center sticky right-0 bg-white z-10 border-l border-border">
                            {(() => {
                              const rt = student.reviewTotal;
                              if (!rt || rt.required === 0) return <span className="text-text-secondary">--</span>;
                              const done = rt.completed >= rt.required;
                              return (
                                <span className={`text-sm font-bold ${done ? "text-emerald-600" : "text-amber-600"}`}>
                                  {rt.completed}/{rt.required}
                                </span>
                              );
                            })()}
                          </td>
                        </>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <ReviewDetailModal
        isOpen={modalTarget !== null}
        onClose={() => setModalTarget(null)}
        courseId={courseId}
        studentId={modalTarget?.studentId ?? 0}
        assignmentId={modalTarget?.assignmentId ?? 0}
        studentName={modalTarget?.studentName ?? ""}
        assignmentName={modalTarget?.assignmentName ?? ""}
      />
    </>
  );
}
