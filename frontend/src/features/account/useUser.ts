import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getUser, updateUserProfile, uploadUserAvatar, deleteAccount, getUserAvatarUrl } from "../../services/userApi";
import { changePassword } from "../../services/authApi";

export function useUser() {
  return useQuery({
    queryKey: ["user"],
    queryFn: getUser,
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { name?: string; email?: string }) =>
      updateUserProfile(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["user"] });
    },
  });
}

export function useUploadAvatar() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => uploadUserAvatar(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["user"] });
    },
  });
}

export function useChangePassword() {
  return useMutation({
    mutationFn: (params: { currentPassword: string; newPassword: string }) =>
      changePassword(params.currentPassword, params.newPassword),
  });
}

export function useDeleteAccount() {
  return useMutation({
    mutationFn: (password: string) => deleteAccount(password),
  });
}

export { getUserAvatarUrl };
