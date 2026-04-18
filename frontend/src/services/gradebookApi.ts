import { BASE_URL, maybeHandleExpire } from "./apiBase";

export const getGradebook = async (courseId: number) => {
  const response = await fetch(`${BASE_URL}/gradebook/course/${courseId}`, {
    method: "GET",
    credentials: "include",
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.msg || `Response status: ${response.status}`);
  }
  return await response.json();
};

export const setGradeOverride = async (
  courseId: number,
  studentID: number,
  assignmentID: number,
  overrideScore: number
) => {
  const response = await fetch(`${BASE_URL}/gradebook/course/${courseId}/override`, {
    method: "PUT",
    body: JSON.stringify({ studentID, assignmentID, overrideScore }),
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.msg || `Response status: ${response.status}`);
  }
  return await response.json();
};

export const clearGradeOverride = async (
  courseId: number,
  studentID: number,
  assignmentID: number
) => {
  const response = await fetch(`${BASE_URL}/gradebook/course/${courseId}/override`, {
    method: "DELETE",
    body: JSON.stringify({ studentID, assignmentID }),
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.msg || `Response status: ${response.status}`);
  }
  return await response.json();
};

export const getStudentReviews = async (
  courseId: number,
  studentID: number,
  assignmentID: number
) => {
  const response = await fetch(
    `${BASE_URL}/gradebook/course/${courseId}/reviews?studentID=${studentID}&assignmentID=${assignmentID}`,
    {
      method: "GET",
      credentials: "include",
    }
  );

  maybeHandleExpire(response);

  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.msg || `Response status: ${response.status}`);
  }
  return await response.json();
};
