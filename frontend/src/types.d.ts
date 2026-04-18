interface Course {
  id: number;
  teacherID: number;
  name: string;
  image_path?: string;
}

interface User {
  id: number;
  name: string;
  email: string;
  role: 'student' | 'teacher' | 'admin';
}

interface StudentGroups {
  groupID: number;
  userID: number;
  assignmentID: number;
}

interface CourseGroup{
  id: number;
  name: string;
  assignmentID: number;
}

interface GroupTable {
  [key: number]: GroupTableValue[];
}

interface GroupTableValue{
  groupID: number;
  userID: number;
  assignmentID: number;
}

interface Criterion {
  id: number;
  rubricID: number;
  question: string;
  scoreMax: number;
  hasScore: boolean;
}

interface Assignment {
  id: number;
  name: string;
  courseID: number;
  description?: string;
  start_date?: string;
  rubric?: string;
  due_date?: string;
  is_anonymous?: boolean;
  has_submitted?: boolean;
}

interface CourseWithAssignments extends Course {
  assignments?: Assignment[];
  assignmentCount?: number;
}