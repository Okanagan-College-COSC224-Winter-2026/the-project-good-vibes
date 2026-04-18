import { BASE_URL, maybeHandleExpire } from "./apiBase";

export const tryLogin = async (email: string, password: string) => {
  try {
    const response = await fetch(`${BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
      credentials: "include",
    });

    if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
    }

    const json = await response.json();
    localStorage.setItem("user", JSON.stringify(json));
    return json;
  } catch (error) {
    console.error(error);
  }

  return false;
};

export const tryRegister = async (
  name: string,
  email: string,
  password: string
) => {
  try {
    const response = await fetch(`${BASE_URL}/auth/register`, {
      method: "POST",
      body: JSON.stringify({ name, email, password }),
      headers: { "Content-Type": "application/json" },
    });
    const data = await response.json().catch(() => null);

    if (!response.ok) {
      const msg =
        (data && (data.msg as string)) ||
        (data && data.errors && JSON.stringify(data.errors)) ||
        `Response status: ${response.status}`;
      throw new Error(msg);
    }

    return data;
  } catch (error) {
    console.error(error);
    throw error;
  }
};

export const changePassword = async (
  currentPassword: string,
  newPassword: string
) => {
  const response = await fetch(`${BASE_URL}/auth/change-password`, {
    method: "PUT",
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
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

export const getUserId = async () => {
  const resp = await fetch(`${BASE_URL}/user_id`, {
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
