import React, { createContext, useContext, useEffect, useState } from "react";
import { useAuth } from "./AuthContext";

const RoleContext = createContext();

export const DEMO_ROLES = [
  { role: "ADMINISTRATOR", department: null, label: "👑 Administrator (All Departments)" },
  { role: "HOD", department: "CSE", label: "🏫 HOD - Computer Science (CSE)" },
  { role: "HOD", department: "ECE", label: "🏫 HOD - Electronics (ECE)" },
  { role: "HOD", department: "AIML", label: "🏫 HOD - Artificial Intelligence (AIML)" },
  { role: "HOD", department: "ME", label: "🏫 HOD - Mechanical Eng (ME)" },
  { role: "HOD", department: "BBA", label: "🏫 HOD - Business Admin (BBA)" },
];

export function RoleProvider({ children }) {
  const auth = useAuth();

  const activeRole = auth?.role || localStorage.getItem("platform_user_role") || "ADMINISTRATOR";
  const userDepartment = auth?.department || localStorage.getItem("platform_user_department") || "CSE";

  const setRoleContext = (r, d = null) => {
    if (auth?.setRoleContextManual) {
      auth.setRoleContextManual(r, d);
    } else {
      localStorage.setItem("platform_user_role", r);
      if (d) {
        localStorage.setItem("platform_user_department", d);
      } else {
        localStorage.removeItem("platform_user_department");
      }
    }
  };

  const getRoleLabel = () => {
    if (activeRole === "ADMINISTRATOR" || activeRole === "ADMIN") {
      return "👑 Administrator (All Departments)";
    }
    if (activeRole === "HOD") {
      return `🏫 HOD - ${userDepartment || "Department"}`;
    }
    return `👤 User (${activeRole})`;
  };

  return (
    <RoleContext.Provider
      value={{
        activeRole,
        userDepartment,
        setRoleContext,
        getRoleLabel,
        demoRoles: DEMO_ROLES,
      }}
    >
      {children}
    </RoleContext.Provider>
  );
}

export function useRole() {
  const context = useContext(RoleContext);
  if (!context) {
    throw new Error("useRole must be used within a RoleProvider");
  }
  return context;
}
