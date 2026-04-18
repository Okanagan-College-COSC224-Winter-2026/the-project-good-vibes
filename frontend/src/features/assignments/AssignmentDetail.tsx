import { useState } from "react";
import { Link } from "react-router-dom";
import { useAssignmentDetail } from "./useAssignmentDetail";
import ManageAssignmentCard from "./ManageAssignmentCard";
import ManageResourcesCard from "./ManageResourcesCard";
import ManageRubricSection from "./ManageRubricSection";
import StudentSubmissionCard from "./StudentSubmissionCard";
import PeerReviewSection from "./PeerReviewSection";
import GroupReviewSection from "./GroupReviewSection";
import RubricDisplay from "../reviews/RubricDisplay";
import { formatDueDate } from "../../util/assignmentDates";

type ReviewTab = "individual" | "group";

const tabButtonClass = (active: boolean) =>
  `px-3 py-1.5 rounded-md text-xs font-medium transition-all cursor-pointer border-none no-underline ${
    active
      ? "bg-white text-text-primary shadow-sm"
      : "bg-transparent text-text-secondary hover:text-text-primary"
  }`;

export default function AssignmentDetail() {
  const {
    classId,
    assignmentId,
    assignment,
    teacherMode,
    isManageTab,
    rubricId,
    groupRubricId,
    review,
    groupReview,
    resourceList,
    groupMembers,
    otherGroups,
    mySubmission,
    revieweeID,
    setRevieweeID,
    groupRevieweeID,
    setGroupRevieweeID,
  } = useAssignmentDetail();

  const individualEnabled = assignment?.individual_reviews !== false;
  const groupEnabled = assignment?.group_reviews !== false;

  const [previewTab, setPreviewTab] = useState<ReviewTab>("individual");
  const [studentReviewTab, setStudentReviewTab] = useState<ReviewTab>(
    individualEnabled ? "individual" : "group"
  );

  return (
    <>
      <div className="p-4 md:p-8 w-full max-w-260 mx-auto flex flex-col gap-6">
        {/* Header row */}
        <div className="flex items-center justify-between gap-4">
          <h2 className="text-2xl font-semibold text-text-primary m-0">
            {assignment?.name ? assignment.name : `Assignment ${assignmentId}`}
          </h2>
          {teacherMode && (
            <div className="flex bg-bg-secondary rounded-lg p-0.5 shrink-0">
              <Link
                to={`/classes/${classId}/assignments/${assignmentId}`}
                className={tabButtonClass(!isManageTab)}
              >
                Preview
              </Link>
              <Link
                to={`/classes/${classId}/assignments/${assignmentId}/manage`}
                className={tabButtonClass(isManageTab)}
              >
                Manage
              </Link>
            </div>
          )}
        </div>

        {/* Detail card */}
        {!isManageTab && assignment && (
          <div className="bg-white rounded-xl border border-border shadow-sm overflow-hidden">
            <div className="bg-btn-primary px-5 md:px-8 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
              <span className="text-white font-medium text-sm">
                {assignment.name}
              </span>
              {(assignment.start_date || assignment.due_date) && (
                <span className="text-white/80 text-xs">
                  {assignment.start_date && formatDueDate(assignment.start_date)}
                  {assignment.start_date && assignment.due_date && " — "}
                  {assignment.due_date && formatDueDate(assignment.due_date)}
                </span>
              )}
            </div>

            <div className="px-5 md:px-8 py-5 flex flex-col gap-4">
              {assignment.description && (
                <div className="flex flex-col gap-1">
                  <span className="text-xs font-semibold text-text-secondary uppercase tracking-wide">Description</span>
                  <p className="text-sm text-text-primary leading-relaxed whitespace-pre-wrap m-0">
                    {assignment.description}
                  </p>
                </div>
              )}

              {(resourceList.length > 0 || teacherMode) && (
                <div className="flex flex-col gap-2 pt-3 border-t border-border">
                  <span className="text-xs font-semibold text-text-secondary uppercase tracking-wide">
                    Supporting Documents
                  </span>
                  {resourceList.length > 0 ? (
                    <ul className="m-0 p-0 list-none flex flex-col gap-1.5">
                      {resourceList.map((resource) => (
                        <li key={resource.id}>
                          <a href={resource.download_url} target="_blank" rel="noreferrer" className="text-btn-primary text-sm hover:underline">
                            {resource.original_name}
                          </a>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-text-secondary text-sm m-0">No supporting documents available.</p>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Teacher: Rubric previews on review tab — single tabbed card */}
        {teacherMode && !isManageTab && (rubricId || groupRubricId) && (
          <div className="bg-white rounded-xl border border-border shadow-sm overflow-hidden">
            <div className="px-5 md:px-8 py-4 border-b border-border flex items-center justify-between gap-4">
              <h3 className="text-base font-semibold text-text-primary m-0">Rubric</h3>
              {rubricId && groupRubricId && (
                <div className="flex bg-bg-secondary rounded-lg p-0.5">
                  <button onClick={() => setPreviewTab("individual")} className={tabButtonClass(previewTab === "individual")}>
                    Individual
                  </button>
                  <button onClick={() => setPreviewTab("group")} className={tabButtonClass(previewTab === "group")}>
                    Group
                  </button>
                </div>
              )}
            </div>
            <div className="px-5 md:px-8 py-5">
              {previewTab === "individual" && rubricId && (
                <RubricDisplay rubricId={rubricId} onCriterionSelect={() => {}} grades={review} />
              )}
              {previewTab === "group" && groupRubricId && (
                <RubricDisplay rubricId={groupRubricId} onCriterionSelect={() => {}} grades={groupReview} />
              )}
              {/* If only one type exists, show it regardless of tab */}
              {previewTab === "individual" && !rubricId && groupRubricId && (
                <RubricDisplay rubricId={groupRubricId} onCriterionSelect={() => {}} grades={groupReview} />
              )}
              {previewTab === "group" && !groupRubricId && rubricId && (
                <RubricDisplay rubricId={rubricId} onCriterionSelect={() => {}} grades={review} />
              )}
            </div>
          </div>
        )}

        {/* Management tab — cards */}
        {teacherMode && assignment && isManageTab && (
          <>
            <ManageAssignmentCard
              assignmentId={assignmentId}
              assignment={assignment}
            />
            <ManageResourcesCard
              assignmentId={assignmentId}
              resources={resourceList}
            />
            <ManageRubricSection
              assignmentId={assignmentId}
              rubricId={rubricId}
              groupRubricId={groupRubricId}
              review={review}
              groupReview={groupReview}
              onCriterionSelect={() => {}}
              onCommentChange={() => {}}
            />
          </>
        )}

        {/* Student view */}
        {!teacherMode && (
          <>
            <StudentSubmissionCard
              assignmentId={assignmentId}
              mySubmission={mySubmission}
            />
            {(individualEnabled || groupEnabled) && (
              <div className="bg-white rounded-2xl border border-border shadow-sm overflow-hidden">
                <div className="px-5 md:px-8 py-4 border-b border-border flex items-center justify-between gap-4">
                  <h3 className="text-base font-semibold text-text-primary m-0">Reviews</h3>
                  {individualEnabled && groupEnabled && (
                    <div className="flex bg-bg-secondary rounded-lg p-0.5">
                      <button onClick={() => setStudentReviewTab("individual")} className={tabButtonClass(studentReviewTab === "individual")}>
                        Individual
                      </button>
                      <button onClick={() => setStudentReviewTab("group")} className={tabButtonClass(studentReviewTab === "group")}>
                        Group
                      </button>
                    </div>
                  )}
                </div>
                <div className="px-5 md:px-8 py-5">
                  {studentReviewTab === "individual" && individualEnabled ? (
                    <PeerReviewSection
                      assignmentId={assignmentId}
                      rubricId={rubricId}
                      review={review}
                      groupMembers={groupMembers}
                      revieweeID={revieweeID}
                      setRevieweeID={setRevieweeID}
                    />
                  ) : groupEnabled ? (
                    <GroupReviewSection
                      assignmentId={assignmentId}
                      groupRubricId={groupRubricId}
                      otherGroups={otherGroups}
                      groupRevieweeID={groupRevieweeID}
                      setGroupRevieweeID={setGroupRevieweeID}
                    />
                  ) : null}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </>
  );
}
