import { BASE_URL, maybeHandleExpire } from "./apiBase";

export const submitReview = async (
  assignmentID: number,
  revieweeID: number,
  criteria: { criterionRowID: number; grade: number; comments: string }[],
  comments: string = "",
  review_type: "individual" | "group" = "individual"
) => {
  const response = await fetch(`${BASE_URL}/review/submit`, {
    method: "POST",
    body: JSON.stringify({ assignmentID, revieweeID, comments, criteria, review_type }),
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

export const updateReview = async (
  reviewId: number,
  criteria: { criterionRowID: number; grade: number; comments: string }[],
  comments?: string
) => {
  const body: Record<string, unknown> = { criteria };
  if (comments !== undefined) body.comments = comments;

  const response = await fetch(`${BASE_URL}/review/${reviewId}`, {
    method: "PUT",
    body: JSON.stringify(body),
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

export const getReview = async (
  assignmentID: number,
  revieweeID: number,
  review_type: "individual" | "group" = "individual"
) => {
  const resp = await fetch(
    `${BASE_URL}/review/lookup?assignmentID=${assignmentID}&revieweeID=${revieweeID}&review_type=${review_type}`,
    { credentials: "include" }
  );

  maybeHandleExpire(resp);
  return resp;
};

export const getReviewsForAssignment = async (
  assignmentID: number,
  review_type?: "individual" | "group"
) => {
  const url = new URL(`${BASE_URL}/review/assignment/${assignmentID}`);
  if (review_type) {
    url.searchParams.set("review_type", review_type);
  }
  const resp = await fetch(url.toString(), {
    credentials: "include",
  });

  maybeHandleExpire(resp);

  if (!resp.ok) {
    const data = await resp.json().catch(() => null);
    throw new Error(data?.msg || `Response status: ${resp.status}`);
  }

  return await resp.json();
};

export const getMyReviewed = async (
  assignmentID: number,
  review_type: "individual" | "group" = "individual"
): Promise<number[]> => {
  const resp = await fetch(
    `${BASE_URL}/review/assignment/${assignmentID}/my-reviewed?review_type=${review_type}`,
    { credentials: "include" }
  );

  maybeHandleExpire(resp);

  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }

  const data = await resp.json();
  return data.reviewee_ids;
};

export interface AssignmentProgress {
  assignment_id: number;
  individual_completed: number;
  individual_required: number;
  group_completed: number;
  group_required: number;
}

export const getMyProgress = async (
  courseID: number
): Promise<{ assignments: AssignmentProgress[] }> => {
  const resp = await fetch(
    `${BASE_URL}/review/course/${courseID}/my-progress`,
    { credentials: "include" }
  );

  maybeHandleExpire(resp);

  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }

  return await resp.json();
};

export const getCourseGradeSummary = async (
  courseID: number,
  studentID?: number
) => {
  const url = new URL(`${BASE_URL}/review/course/${courseID}/summary`);
  if (studentID !== undefined) {
    url.searchParams.set("studentID", String(studentID));
  }
  const resp = await fetch(url.toString(), {
    credentials: "include",
  });

  maybeHandleExpire(resp);

  if (!resp.ok) {
    const data = await resp.json().catch(() => null);
    throw new Error(data?.msg || `Response status: ${resp.status}`);
  }

  return await resp.json();
};
