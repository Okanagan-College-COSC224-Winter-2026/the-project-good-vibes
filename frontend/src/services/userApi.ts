import { BASE_URL, maybeHandleExpire } from "./apiBase";

export const getUser = async () => {
  const response = await fetch(`${BASE_URL}/user/`, {
    credentials: "include",
  });
  maybeHandleExpire(response);
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.msg || `Response status: ${response.status}`);
  }
  return response.json();
};

export const updateUserProfile = async (data: {
  name?: string;
  email?: string;
}) => {
  const response = await fetch(`${BASE_URL}/user/`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  maybeHandleExpire(response);
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.msg || `Response status: ${response.status}`);
  }
  const updated = await response.json();
  localStorage.setItem("user", JSON.stringify(updated));
  return updated;
};

export const uploadUserAvatar = async (file: File) => {
  const formData = new FormData();
  formData.append("avatar", file);
  const response = await fetch(`${BASE_URL}/user/avatar`, {
    method: "POST",
    credentials: "include",
    body: formData,
  });
  maybeHandleExpire(response);
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.msg || `Response status: ${response.status}`);
  }
  const updated = await response.json();
  localStorage.setItem("user", JSON.stringify(updated));
  return updated;
};

export const deleteAccount = async (password: string) => {
  const response = await fetch(`${BASE_URL}/user/`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ password }),
  });
  maybeHandleExpire(response);
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.msg || `Response status: ${response.status}`);
  }
  return response.json();
};

export const changeRequiredPassword = async (
  currentPassword: string,
  newPassword: string
) => {
  const response = await fetch(`${BASE_URL}/user/password`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.msg || `Response status: ${response.status}`);
  }

  return response.json();
};

export const getUserAvatarUrl = (userId: number) =>
  `${BASE_URL}/user/avatar/${userId}`;
