import { BASE_URL, maybeHandleExpire } from "./apiBase";

export const listAssignments = async (classId: string) => {
  const resp = await fetch(`${BASE_URL}/assignment/${classId}`, {
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

export const getAssignment = async (assignmentId: number) => {
  const resp = await fetch(
    `${BASE_URL}/assignment/detail/${assignmentId}`,
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

export const createAssignment = async (
  courseID: number,
  name: string,
  description?: string,
  start_date?: string,
  due_date?: string,
  is_anonymous: boolean = true,
  individual_reviews: boolean = true,
  group_reviews: boolean = true
) => {
  const response = await fetch(
    `${BASE_URL}/assignment/create_assignment`,
    {
      method: "POST",
      body: JSON.stringify({
        courseID,
        name,
        description,
        start_date,
        due_date,
        is_anonymous,
        individual_reviews,
        group_reviews,
      }),
      headers: { "Content-Type": "application/json" },
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

export const editAssignment = async (
  assignmentID: number,
  payload: {
    name?: string;
    description?: string;
    start_date?: string;
    due_date?: string;
    rubric?: string;
    is_anonymous?: boolean;
    individual_reviews?: boolean;
    group_reviews?: boolean;
  }
) => {
  const response = await fetch(
    `${BASE_URL}/assignment/edit_assignment/${assignmentID}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
      headers: { "Content-Type": "application/json" },
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

export const deleteAssignment = async (assignmentID: number) => {
  const response = await fetch(
    `${BASE_URL}/assignment/delete_assignment/${assignmentID}`,
    {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
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

export const listAssignmentResources = async (assignmentID: number) => {
  const resp = await fetch(
    `${BASE_URL}/assignment-resource/assignment/${assignmentID}`,
    {
      method: "GET",
      credentials: "include",
    }
  );

  maybeHandleExpire(resp);

  if (!resp.ok) {
    const data = await resp.json().catch(() => null);
    throw new Error(data?.msg || `Response status: ${resp.status}`);
  }

  const data = await resp.json();
  const resources = data?.resources || [];
  return resources.map(
    (resource: {
      id: number;
      assignmentID: number;
      uploaderID: number;
      original_name: string;
      download_url?: string;
      created_at?: string;
    }) => ({
      ...resource,
      download_url: resource.download_url?.startsWith("/")
        ? `${BASE_URL}${resource.download_url}`
        : resource.download_url,
    })
  );
};

export const uploadAssignmentResource = async (
  assignmentID: number,
  file: File
) => {
  const formData = new FormData();
  formData.append("file", file);

  const resp = await fetch(
    `${BASE_URL}/assignment-resource/assignment/${assignmentID}`,
    {
      method: "POST",
      body: formData,
      credentials: "include",
    }
  );

  maybeHandleExpire(resp);

  if (!resp.ok) {
    const data = await resp.json().catch(() => null);
    throw new Error(data?.msg || `Response status: ${resp.status}`);
  }

  const data = await resp.json();
  const resource = data?.resource;
  if (resource?.download_url?.startsWith("/")) {
    resource.download_url = `${BASE_URL}${resource.download_url}`;
  }
  return data;
};

export const deleteAssignmentResource = async (resourceID: number) => {
  const resp = await fetch(`${BASE_URL}/assignment-resource/${resourceID}`, {
    method: "DELETE",
    credentials: "include",
  });

  maybeHandleExpire(resp);

  if (!resp.ok) {
    const data = await resp.json().catch(() => null);
    throw new Error(data?.msg || `Response status: ${resp.status}`);
  }

  return await resp.json();
};
