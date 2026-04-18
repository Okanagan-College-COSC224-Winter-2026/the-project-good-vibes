import { BASE_URL, maybeHandleExpire } from "./apiBase";

export const listStuGroup = async (courseId: number) => {
  const resp = await fetch(`${BASE_URL}/groups/course/${courseId}/my-group`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  });

  maybeHandleExpire(resp);

  if (resp.status === 404) {
    return null;
  }

  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }

  return await resp.json();
};

export const listGroups = async (courseId: number) => {
  const resp = await fetch(`${BASE_URL}/groups/course/${courseId}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  });

  maybeHandleExpire(resp);

  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }

  return await resp.json();
};

export const listUnassignedStudents = async (courseId: number) => {
  const resp = await fetch(
    `${BASE_URL}/groups/course/${courseId}/unassigned`,
    {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
    }
  );

  maybeHandleExpire(resp);

  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }

  return await resp.json();
};

export const listGroupMembers = async (groupId: number) => {
  const resp = await fetch(`${BASE_URL}/groups/${groupId}/members`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  });

  maybeHandleExpire(resp);

  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }

  return await resp.json();
};

export const addGroupMember = async (groupId: number, userId: number) => {
  const resp = await fetch(`${BASE_URL}/groups/members/add`, {
    method: "POST",
    body: JSON.stringify({ groupID: groupId, userID: userId }),
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  });

  maybeHandleExpire(resp);

  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }

  return await resp.json();
};

export const removeGroupMember = async (groupId: number, userId: number) => {
  const resp = await fetch(`${BASE_URL}/groups/members/remove`, {
    method: "POST",
    body: JSON.stringify({ groupID: groupId, userID: userId }),
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  });

  maybeHandleExpire(resp);

  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }

  return await resp.json();
};

export const createGroup = async (courseId: number, name: string) => {
  const response = await fetch(`${BASE_URL}/groups/create`, {
    method: "POST",
    body: JSON.stringify({ courseID: courseId, name }),
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    throw new Error(`Response status: ${response.status}`);
  }

  return await response.json();
};

export const deleteGroup = async (groupId: number) => {
  const resp = await fetch(`${BASE_URL}/groups/${groupId}`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  });

  maybeHandleExpire(resp);

  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }

  return await resp.json();
};
