import { BrowserRouter, Route, Routes } from "react-router-dom";

import ClassHome from "./features/classes/ClassHome";
import ClassLayout from "./layouts/ClassLayout";
import ProtectedLayout from "./layouts/ProtectedLayout";
import GroupManager from "./features/groups/GroupManager";
import ClassMembers from "./features/classes/ClassMembers";
import LoginForm from "./features/authentication/LoginForm";
import SignupForm from "./features/authentication/SignupForm";
import UpdateAccount from "./features/account/UpdateAccount";
import CreateTeacher from "./features/account/CreateTeacher";
import CreateClassForm from "./features/classes/CreateClassForm";
import DashboardLayout from "./features/dashboard/DashboardLayout";
import ClassSettings from "./features/classes/ClassSettings";
import ClassEvaluations from "./features/reviews/ClassEvaluations";
import Gradebook from "./features/gradebook/Gradebook";
import AssignmentDetail from "./features/assignments/AssignmentDetail";
import ChangePasswordForm from "./features/authentication/ChangePasswordForm";
import { AuthProvider } from "./features/authentication/AuthProvider";
import { Toaster } from "react-hot-toast";


function App() {
  return (
    <AuthProvider>
      <Toaster
        position="top-center"
        toastOptions={{
          duration: 3000,
          style: {
            borderRadius: "12px",
            padding: "12px 16px",
            fontSize: "14px",
            fontWeight: 500,
            boxShadow: "0 4px 20px rgba(0,0,0,0.08)",
          },
          success: {
            iconTheme: { primary: "#10b981", secondary: "#fff" },
          },
          error: {
            iconTheme: { primary: "#ef4444", secondary: "#fff" },
          },
        }}
      />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LoginForm />} />
          <Route path="/register" element={<SignupForm />} />
          <Route path="/change-password" element={<ChangePasswordForm />} />

          <Route element={<ProtectedLayout />}>
            <Route path="/home" element={<DashboardLayout />} />
            <Route path="/admin/create-teacher" element={<CreateTeacher />} />
            <Route path="/profile/:id" element={<UpdateAccount />} />
            <Route path="/classes/create" element={<CreateClassForm />} />

            <Route path="/classes/:id" element={<ClassLayout />}>
              <Route path="home" element={<ClassHome />} />
              <Route path="members" element={<ClassMembers />} />
              <Route path="groups" element={<GroupManager />} />
              <Route path="evaluations" element={<ClassEvaluations />} />
              <Route path="gradebook" element={<Gradebook />} />
              <Route path="settings" element={<ClassSettings />} />
              <Route path="assignments/:assignmentId" element={<AssignmentDetail />} />
              <Route path="assignments/:assignmentId/manage" element={<AssignmentDetail />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
