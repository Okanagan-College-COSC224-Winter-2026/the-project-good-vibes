import { useState } from "react";
import { useParams } from "react-router-dom";
import Modal from "../../ui/Modal";
import { useCourseGradeSummary, useReviewsForAssignment } from "./useReviews";

interface ReviewCriterion {
  id: number;
  reviewID: number;
  criterionRowID: number;
  criterion_name: string | null;
  score_max: number | null;
  grade: number | null;
  comments: string;
}

interface ReviewData {
  id: number;
  assignmentID: number;
  comments: string | null;
  review_type?: string;
  reviewer: { id: number | null; name: string; email: string | null };
  reviewee: { id: number | null; name: string; email: string | null; type?: string };
  criteria: ReviewCriterion[];
}

interface AssignmentSummary {
  id: number;
  name: string;
  individualReviewCount: number;
  individualAverage: number | null;
  individualMax: number | null;
  groupReviewCount: number;
  groupAverage: number | null;
  groupMax: number | null;
}

function getAssignmentPct(a: AssignmentSummary): number | null {
  const pcts: number[] = [];
  if (a.individualAverage != null && a.individualMax && a.individualMax > 0) {
    pcts.push(a.individualAverage / a.individualMax);
  }
  if (a.groupAverage != null && a.groupMax && a.groupMax > 0) {
    pcts.push(a.groupAverage / a.groupMax);
  }
  return pcts.length > 0 ? (pcts.reduce((s, p) => s + p, 0) / pcts.length) * 100 : null;
}

function ReviewCard({ review, idx }: { review: ReviewData; idx: number }) {
  const scoredCriteria = review.criteria.filter((c) => c.grade !== null);
  const total = scoredCriteria.reduce((sum, c) => sum + (c.grade ?? 0), 0);
  const totalMax = scoredCriteria
    .filter((c) => c.score_max !== null)
    .reduce((sum, c) => sum + (c.score_max ?? 0), 0);

  return (
    <div className="rounded-xl border border-border overflow-hidden">
      <div className="px-4 py-3 bg-bg-secondary flex justify-between items-center border-b border-border">
        <span className="font-semibold text-sm text-text-primary">Review {idx + 1}</span>
        <span className="text-xs text-text-secondary">by {review.reviewer.name}</span>
      </div>
      <div className="p-4">
        {review.criteria.length === 0 ? (
          <p className="text-text-secondary text-xs m-0">No criteria scores recorded.</p>
        ) : (
          <div className="flex flex-col gap-2">
            {review.criteria.map((crit) => (
              <div key={crit.id} className="flex justify-between items-center py-1.5">
                <span className="text-sm text-text-primary">
                  {crit.criterion_name || `Criterion ${crit.criterionRowID}`}
                </span>
                <span className="text-sm font-semibold text-text-primary">
                  {crit.grade !== null
                    ? `${crit.grade}${crit.score_max !== null ? ` / ${crit.score_max}` : ""}`
                    : "\u2014"}
                </span>
              </div>
            ))}
          </div>
        )}

        {scoredCriteria.length > 0 && (
          <div className="flex justify-between items-center mt-3 pt-3 border-t border-border">
            <span className="text-sm font-semibold text-text-primary">Total</span>
            <span className="text-sm font-bold text-btn-primary">
              {total}{totalMax > 0 ? ` / ${totalMax}` : ""}
            </span>
          </div>
        )}

        {review.comments && review.comments.trim() !== "" && (
          <div className="mt-3 pt-3 border-t border-border">
            <span className="text-xs font-semibold text-text-secondary uppercase tracking-wide">Comments</span>
            <p className="mt-1.5 text-sm text-text-primary leading-relaxed m-0">
              {review.comments}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function ReviewSection({ title, reviews }: { title: string; reviews: ReviewData[] }) {
  if (reviews.length === 0) return null;

  return (
    <div>
      <h4 className="text-sm font-semibold text-text-secondary uppercase tracking-wide m-0 mb-3">
        {title}
      </h4>
      <div className="flex flex-col gap-3">
        {reviews.map((review, idx) => (
          <ReviewCard key={review.id} review={review} idx={idx} />
        ))}
      </div>
    </div>
  );
}

function EyeIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

export default function ClassEvaluations() {
  const { id } = useParams();

  const [selectedAssignment, setSelectedAssignment] = useState<AssignmentSummary | null>(null);

  const { data: summaryData, isLoading: loading } = useCourseGradeSummary(Number(id));

  // Fetch both individual and group reviews when modal is open
  const { data: individualReviews = [], isLoading: indLoading } = useReviewsForAssignment(
    selectedAssignment?.id ?? 0,
    selectedAssignment ? "individual" : undefined
  );
  const { data: groupReviews = [], isLoading: grpLoading } = useReviewsForAssignment(
    selectedAssignment?.id ?? 0,
    selectedAssignment ? "group" : undefined
  );
  const modalLoading = indLoading || grpLoading;

  const summaries: AssignmentSummary[] = summaryData?.assignments ?? [];

  const coursePct = (() => {
    const pcts = summaries.map(getAssignmentPct).filter((p): p is number => p !== null);
    return pcts.length > 0 ? pcts.reduce((s, p) => s + p, 0) / pcts.length : null;
  })();

  return (
    <>
      <div className="p-4 md:p-8 w-full max-w-260 mx-auto flex flex-col gap-6">
        <h2 className="text-2xl font-semibold text-text-primary m-0">My Evaluations</h2>

        {loading ? (
          <p className="text-text-secondary text-sm">Loading evaluations...</p>
        ) : summaries.length === 0 ? (
          <div className="bg-white rounded-2xl border border-border shadow-sm overflow-hidden">
            <div className="px-5 md:px-8 py-8 flex flex-col items-center gap-2">
              <span className="text-3xl">📋</span>
              <p className="text-text-secondary text-sm m-0">No assignments in this course yet.</p>
            </div>
          </div>
        ) : (
          <>
            <div className="bg-white rounded-2xl border border-border shadow-sm overflow-hidden">
              <div className="px-5 md:px-8 py-4 border-b border-border flex items-center justify-between">
                <h3 className="text-base font-semibold text-text-primary m-0">Assignment</h3>
                <h3 className="text-base font-semibold text-text-primary m-0">Grade</h3>
              </div>
              <div className="divide-y divide-border">
                {summaries.map((s) => {
                  const pct = getAssignmentPct(s);
                  const hasReviews = s.individualReviewCount > 0 || s.groupReviewCount > 0;

                  return (
                    <div
                      key={s.id}
                      className="px-5 md:px-8 py-4 flex items-center justify-between gap-3"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div className={`w-2 h-2 rounded-full shrink-0 ${hasReviews ? "bg-btn-primary" : "bg-gray-300"}`} />
                        <span className="font-medium text-text-primary text-sm truncate">{s.name}</span>
                      </div>
                      <div className="flex items-center shrink-0">
                        <div className="w-8 flex items-center justify-center">
                          {hasReviews && (
                            <button
                              onClick={() => setSelectedAssignment(s)}
                              className="bg-transparent border-none cursor-pointer text-text-secondary hover:text-btn-primary transition-colors p-1 rounded-lg hover:bg-bg-secondary"
                              title="View reviews"
                            >
                              <EyeIcon />
                            </button>
                          )}
                        </div>
                        <div className="w-16 text-right">
                          {pct !== null ? (
                            <span className="font-semibold text-btn-primary bg-btn-primary/10 px-2.5 py-0.5 rounded-full text-xs">
                              {pct.toFixed(0)}%
                            </span>
                          ) : (
                            <span className="text-text-secondary text-xs">--</span>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {coursePct !== null && (
                <div className="px-5 md:px-8 py-4 bg-bg-secondary border-t border-border flex items-center justify-between gap-2">
                  <span className="text-sm font-semibold text-text-primary">Course Total</span>
                  <span className="font-bold text-btn-primary text-sm">
                    {coursePct.toFixed(0)}%
                  </span>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Review detail modal — shows both individual and group reviews */}
      <Modal
        isOpen={selectedAssignment !== null}
        onClose={() => setSelectedAssignment(null)}
        title={`Reviews: ${selectedAssignment?.name || ""}`}
      >
        {modalLoading ? (
          <p className="text-text-secondary text-sm">Loading reviews...</p>
        ) : (individualReviews as ReviewData[]).length === 0 && (groupReviews as ReviewData[]).length === 0 ? (
          <p className="text-text-secondary text-sm">No reviews found.</p>
        ) : (
          <div className="flex flex-col gap-5">
            <ReviewSection title="Individual Reviews" reviews={individualReviews as ReviewData[]} />
            <ReviewSection title="Group Reviews" reviews={groupReviews as ReviewData[]} />
          </div>
        )}
      </Modal>
    </>
  );
}
