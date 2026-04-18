import { useEffect } from "react";
import { Outlet, useNavigate } from "react-router-dom";

import Sidebar from "../ui/Sidebar";
import MobileHeader from "../ui/MobileHeader";
import { useAuth } from "../features/authentication/AuthProvider";

export default function ProtectedLayout() {
  const { isAuthenticated, isLoading, mustChangePassword } = useAuth();
  const navigate = useNavigate();

  useEffect(
    function () {
      if (!isAuthenticated && !isLoading) navigate("/");
      if (isAuthenticated && !isLoading && mustChangePassword) {
        navigate("/change-password");
      }
    },
    [isAuthenticated, isLoading, mustChangePassword, navigate]
  );

  if (isLoading)
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900" />
      </div>
    );

  if (!isAuthenticated) return null;

  return (
    <div className="flex flex-row min-h-screen bg-bg-primary">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0 bg-bg-secondary">
        <MobileHeader />
        <Outlet />
      </div>
    </div>
  );
}
