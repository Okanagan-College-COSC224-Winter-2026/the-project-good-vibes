import { useState } from "react";
import { useLocation, useParams } from "react-router-dom";

import { isTeacher, getUserId } from "../../util/login";
import {
  useAssignment,
  useAssignmentResources,
} from "./useAssignments";
import { useRubricForAssignment } from "../reviews/useRubric";
import { useMySubmission } from "../reviews/useSubmission";
import { useMyGroup, useGroups } from "../groups/useGroups";
import { useReview } from "../reviews/useReviews";

export interface AssignmentResourceItem {
  id: number;
  assignmentID: number;
  uploaderID: number;
  original_name: string;
  download_url: string;
  created_at?: string;
}

export interface GroupMember {
  id: number;
  name: string;
  email: string;
}

export interface CourseGroupItem {
  id: number;
  name: string;
  courseID: number;
}

export function useAssignmentDetail() {
  const { id: classId, assignmentId: assignmentIdParam } = useParams();
  const assignmentId = Number(assignmentIdParam);
  const location = useLocation();

  const [revieweeID, setRevieweeID] = useState<number>(0);
  const [groupRevieweeID, setGroupRevieweeID] = useState<number>(0);

  const teacherMode = isTeacher();
  const isManageTab = teacherMode && location.pathname.endsWith("/manage");

  const { data: assignment } = useAssignment(assignmentId);
  const courseID = assignment?.courseID ?? 0;

  // Individual rubric
  const { data: rubricData } = useRubricForAssignment(assignmentId, "individual");
  // Group rubric
  const { data: groupRubricData } = useRubricForAssignment(assignmentId, "group");

  const { data: mySubmission } = useMySubmission(assignmentId, !teacherMode);
  const { data: resources } = useAssignmentResources(assignmentId);
  const { data: myGroupData } = useMyGroup(courseID);
  const { data: allGroups } = useGroups(courseID);

  // Individual review lookup
  const { data: reviewData } = useReview(assignmentId, revieweeID, "individual");
  // Group review lookup
  const { data: groupReviewData } = useReview(assignmentId, groupRevieweeID, "group");

  const rubricId: number | null = rubricData ? rubricData.id : null;
  const groupRubricId: number | null = groupRubricData ? groupRubricData.id : null;
  const review: number[] = reviewData?.grades ?? [];
  const groupReview: number[] = groupReviewData?.grades ?? [];
  const currentUserId = getUserId();
  const resourceList: AssignmentResourceItem[] = resources ?? [];

  const groupMembers: GroupMember[] = myGroupData?.members
    ? myGroupData.members.filter((m: GroupMember) => m.id !== currentUserId)
    : [];

  const myGroupId: number | null = myGroupData?.id ?? null;

  // Other groups for group review (exclude own group)
  const otherGroups: CourseGroupItem[] = (allGroups ?? []).filter(
    (g: CourseGroupItem) => g.id !== myGroupId
  );

  return {
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
    myGroupId,
    mySubmission,
    revieweeID,
    setRevieweeID,
    groupRevieweeID,
    setGroupRevieweeID,
  };
}
