// Re-exports from organized service modules.
// New code should import directly from services/.

export { tryLogin, tryRegister, changePassword } from "../services/authApi";
export { createClass, listClasses, importStudentsForCourse, listCourseMembers } from "../services/classApi";
export {
  listAssignments,
  getAssignment,
  createAssignment,
  editAssignment,
  deleteAssignment,
  listAssignmentResources,
  uploadAssignmentResource,
  deleteAssignmentResource,
} from "../services/assignmentApi";
export {
  listStuGroup,
  listGroups,
  listUnassignedStudents,
  listGroupMembers,
  addGroupMember,
  removeGroupMember,
  createGroup,
  deleteGroup,
} from "../services/groupApi";
export {
  getCriteria,
  createCriteria,
  createRubric,
  getRubric,
  getRubricForAssignment,
  deleteRubric,
} from "../services/rubricApi";
export {
  getMySubmission,
  uploadMySubmission,
  deleteMySubmission,
} from "../services/submissionApi";
export {
  submitReview,
  getReview,
  getReviewsForAssignment,
  getCourseGradeSummary,
} from "../services/reviewApi";
export { createTeacherAccount } from "../services/adminApi";
export {
  getUser,
  updateUserProfile,
  uploadUserAvatar,
  getUserAvatarUrl,
} from "../services/userApi";
export { maybeHandleExpire } from "../services/apiBase";
