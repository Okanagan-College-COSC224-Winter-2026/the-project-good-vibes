import { BASE_URL, maybeHandleExpire } from "./apiBase";

export async function getCriteria(rubricID: number) {
  const resp = await fetch(`${BASE_URL}/rubric/${rubricID}/criteria`, {
    credentials: "include",
  });

  maybeHandleExpire(resp);

  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }

  return await resp.json();
}

export async function createCriteria(
  rubricID: number,
  question: string,
  scoreMax: number,
  _canComment: boolean,
  hasScore: boolean = true,
) {
  const response = await fetch(`${BASE_URL}/rubric/${rubricID}/criteria`, {
    method: "POST",
    body: JSON.stringify({ question, scoreMax, hasScore }),
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    throw new Error(`Response status: ${response.status}`);
  }
}

export async function createRubric(
  assignmentID: number,
  canComment: boolean,
  rubric_type: "individual" | "group" = "individual",
): Promise<{ id: number }> {
  const response = await fetch(`${BASE_URL}/rubric/create`, {
    method: "POST",
    body: JSON.stringify({ assignmentID, canComment, rubric_type }),
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    throw new Error(`Response status: ${response.status}`);
  }

  const data = await response.json();
  return { id: data.rubric.id };
}

export async function getRubric(rubricID: number) {
  const resp = await fetch(`${BASE_URL}/rubric/${rubricID}`, {
    credentials: "include",
  });

  maybeHandleExpire(resp);

  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }

  return await resp.json();
}

export async function getRubricForAssignment(
  assignmentID: number,
  rubric_type: "individual" | "group" = "individual",
) {
  const resp = await fetch(
    `${BASE_URL}/rubric/assignment/${assignmentID}?rubric_type=${rubric_type}`,
    { credentials: "include" }
  );

  maybeHandleExpire(resp);

  if (resp.status === 404) {
    return null;
  }

  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }

  return await resp.json();
}

export async function updateRubric(
  rubricID: number,
  payload: {
    canComment?: boolean;
    criteria: { question: string; scoreMax: number; hasScore: boolean }[];
  },
): Promise<{ reviews_deleted: number }> {
  const resp = await fetch(`${BASE_URL}/rubric/${rubricID}`, {
    method: "PUT",
    body: JSON.stringify(payload),
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  });

  maybeHandleExpire(resp);

  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }

  return await resp.json();
}

export async function deleteRubric(rubricID: number) {
  const resp = await fetch(`${BASE_URL}/rubric/${rubricID}`, {
    method: "DELETE",
    credentials: "include",
  });

  maybeHandleExpire(resp);

  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }

  return await resp.json();
}
