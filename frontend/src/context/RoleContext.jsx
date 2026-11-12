import React, { createContext, useContext } from "react";
import { useAuth } from "./AuthContext";

const RoleContext = createContext(null);

export function RoleProvider({ children }) {
  const { role, department } = useAuth();

  const getRoleLabel = () => {
    if (role === "ADMINISTRATOR") return "Administrator (All Departments)";
    if (role === "HOD") return `HOD - ${department}`;
    return "No application role assigned";
  };

  return (
    <RoleContext.Provider
      value={{
        activeRole: role,
        userDepartment: department,
        getRoleLabel,
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
