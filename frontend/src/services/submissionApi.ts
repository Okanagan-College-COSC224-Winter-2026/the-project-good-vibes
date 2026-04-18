import { BASE_URL, maybeHandleExpire } from "./apiBase";

export async function getMySubmission(assignmentID: number) {
  const resp = await fetch(`${BASE_URL}/submission/${assignmentID}/mine`, {
    method: "GET",
    credentials: "include",
  });

  maybeHandleExpire(resp);

  if (!resp.ok) {
    const data = await resp.json().catch(() => null);
    throw new Error(data?.msg || `Response status: ${resp.status}`);
  }

  const data = await resp.json();
  if (data?.submission?.download_url?.startsWith("/")) {
    data.submission.download_url = `${BASE_URL}${data.submission.download_url}`;
  }
  return data.submission;
}

export async function uploadMySubmission(assignmentID: number, file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const resp = await fetch(`${BASE_URL}/submission/${assignmentID}/mine`, {
    method: "POST",
    body: formData,
    credentials: "include",
  });

  maybeHandleExpire(resp);

  if (!resp.ok) {
    const data = await resp.json().catch(() => null);
    throw new Error(data?.msg || `Response status: ${resp.status}`);
  }

  const data = await resp.json();
  if (data?.submission?.download_url?.startsWith("/")) {
    data.submission.download_url = `${BASE_URL}${data.submission.download_url}`;
  }
  return data;
}

export async function getStudentSubmission(assignmentID: number, studentID: number) {
  const resp = await fetch(
    `${BASE_URL}/submission/${assignmentID}/student/${studentID}`,
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
  if (data?.submission?.download_url?.startsWith("/")) {
    data.submission.download_url = `${BASE_URL}${data.submission.download_url}`;
  }
  return data.submission;
}

export async function deleteMySubmission(assignmentID: number) {
  const resp = await fetch(`${BASE_URL}/submission/${assignmentID}/mine`, {
    method: "DELETE",
    credentials: "include",
  });

  maybeHandleExpire(resp);

  if (!resp.ok) {
    const data = await resp.json().catch(() => null);
    throw new Error(data?.msg || `Response status: ${resp.status}`);
  }

  return await resp.json();
}
