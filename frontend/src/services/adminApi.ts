import { BASE_URL, maybeHandleExpire } from "./apiBase";

export const createTeacherAccount = async (
  name: string,
  email: string,
  password: string
) => {
  const response = await fetch(`${BASE_URL}/admin/users/create`, {
    method: "POST",
    body: JSON.stringify({
      name,
      email,
      password,
      role: "teacher",
      must_change_password: true,
    }),
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.msg || `Response status: ${response.status}`);
  }

  return await response.json();
};
