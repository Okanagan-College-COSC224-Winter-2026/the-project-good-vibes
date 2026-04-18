import { BASE_URL, maybeHandleExpire } from "./apiBase";

export async function createClass(name: string) {
  const response = await fetch(`${BASE_URL}/class/create_class`, {
    method: "POST",
    body: JSON.stringify({ name }),
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    throw new Error(`Response status: ${response.status}`);
  }

  return await response.json();
}

export async function listClasses() {
  const response = await fetch(`${BASE_URL}/class/classes`, {
    method: "GET",
    credentials: "include",
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    throw new Error(`Response status: ${response.status}`);
  }

  return await response.json();
}

export async function importStudentsForCourse(
  courseID: number,
  students: string,
) {
  const response = await fetch(`${BASE_URL}/class/enroll_students`, {
    method: "POST",
    body: JSON.stringify({
      students,
      class_id: courseID,
    }),
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  });

  maybeHandleExpire(response);

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.msg || `Response status: ${response.status}`);
  }

  return data;
}

export async function searchCourses(query: string) {
  const response = await fetch(
    `${BASE_URL}/class/search?q=${encodeURIComponent(query)}`,
    { credentials: "include" }
  );

  maybeHandleExpire(response);

  if (!response.ok) {
    throw new Error(`Response status: ${response.status}`);
  }

  return await response.json();
}

export async function updateCourse(
  courseId: number,
  data: { name?: string },
) {
  const response = await fetch(`${BASE_URL}/class/${courseId}`, {
    method: "PUT",
    body: JSON.stringify(data),
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    throw new Error(`Response status: ${response.status}`);
  }

  return await response.json();
}

export async function uploadCourseImage(courseId: number, file: File) {
  const formData = new FormData();
  formData.append("image", file);

  const response = await fetch(`${BASE_URL}/class/${courseId}/image`, {
    method: "POST",
    body: formData,
    credentials: "include",
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    throw new Error(`Response status: ${response.status}`);
  }

  return await response.json();
}

export function getCourseImageUrl(courseId: number) {
  return `${BASE_URL}/class/${courseId}/image`;
}

export async function deleteCourse(courseId: number) {
  const response = await fetch(`${BASE_URL}/class/${courseId}`, {
    method: "DELETE",
    credentials: "include",
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    throw new Error(`Response status: ${response.status}`);
  }

  return await response.json();
}

export async function listCourseMembers(classId: string) {
  const response = await fetch(`${BASE_URL}/class/members`, {
    method: "POST",
    body: JSON.stringify({ id: classId }),
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    throw new Error(`Response status: ${response.status}`);
  }

  return await response.json();
}
