import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { RoleProvider } from "./context/RoleContext";
import Layout from "./components/layout/Layout";
import Login from "./pages/Login";
import Overview from "./pages/Overview";
import Students from "./pages/Students";
import StudentDirectory from "./pages/StudentDirectory";
import StudentDetail from "./pages/StudentDetail";
import Finance from "./pages/Finance";
import Research from "./pages/Research";
import Decisions from "./pages/Decisions";
import DepartmentPerformance from "./pages/DepartmentPerformance";
import StudentDepartmentPerformance from "./pages/StudentDepartmentPerformance";
import FinanceDepartmentPerformance from "./pages/FinanceDepartmentPerformance";
import ResearchDepartmentPerformance from "./pages/ResearchDepartmentPerformance";
import LoadingSpinner from "./components/common/LoadingSpinner";

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  if (loading) {
    return <LoadingSpinner message="Checking authentication session..." />;
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default function App() {
  return (
    <AuthProvider>
      <RoleProvider>
        <BrowserRouter>
          <Routes>
            {/* Public Login Route */}
            <Route path="/login" element={<Login />} />

            {/* Protected Application Routes */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Overview />} />
              <Route path="students" element={<Students />} />
              <Route path="students/department-performance" element={<StudentDepartmentPerformance />} />
              <Route path="students/directory" element={<StudentDirectory />} />
              <Route path="students/:studentId" element={<StudentDetail />} />
              <Route path="finance" element={<Finance />} />
              <Route path="finance/department-performance" element={<FinanceDepartmentPerformance />} />
              <Route path="research" element={<Research />} />
              <Route path="research/department-performance" element={<ResearchDepartmentPerformance />} />
              <Route path="decisions" element={<Decisions />} />
              <Route path="department-performance" element={<DepartmentPerformance />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </RoleProvider>
    </AuthProvider>
  );
}
