import React, { createContext, useContext, useEffect, useState } from "react";
import { supabase } from "../utils/supabase";

const AuthContext = createContext(null);

// Demo profile mappings for standard role emails
const DEMO_USER_PROFILES = {
  "admin@institution.edu": { role: "ADMINISTRATOR", department_id: null, label: "Administrator (All Access)" },
  "administrator@institution.edu": { role: "ADMINISTRATOR", department_id: null, label: "Administrator (All Access)" },
  "hod.cse@institution.edu": { role: "HOD", department_id: "CSE", label: "CSE HOD (Computer Science)" },
  "hod.ece@institution.edu": { role: "HOD", department_id: "ECE", label: "ECE HOD (Electronics)" },
  "hod.eee@institution.edu": { role: "HOD", department_id: "EEE", label: "EEE HOD (Electrical)" },
  "hod.aiml@institution.edu": { role: "HOD", department_id: "AIML", label: "AIML HOD (Artificial Intelligence)" },
  "hod.me@institution.edu": { role: "HOD", department_id: "ME", label: "ME HOD (Mechanical)" },
  "hod.bba@institution.edu": { role: "HOD", department_id: "BBA", label: "BBA HOD (Business Admin)" },
  "hod.bt@institution.edu": { role: "HOD", department_id: "BT", label: "BT HOD (Biotech)" },
  "hod.chem@institution.edu": { role: "HOD", department_id: "CHEM", label: "CHEM HOD (Chemistry)" },
  "hod.math@institution.edu": { role: "HOD", department_id: "MATH", label: "MATH HOD (Mathematics)" },
  "hod.phy@institution.edu": { role: "HOD", department_id: "PHY", label: "PHY HOD (Physics)" },
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [role, setRole] = useState(() => localStorage.getItem("platform_user_role") || null);
  const [department, setDepartment] = useState(() => localStorage.getItem("platform_user_department") || null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  // Derive role and department from user metadata or email
  const resolveUserProfile = (sbUser) => {
    if (!sbUser) return { role: "ADMINISTRATOR", department_id: null };

    const meta = sbUser.user_metadata || {};
    const email = (sbUser.email || "").toLowerCase();

    // Check predefined demo profiles
    if (DEMO_USER_PROFILES[email]) {
      return DEMO_USER_PROFILES[email];
    }

    // Check metadata fields
    if (meta.role) {
      const r = String(meta.role).toUpperCase();
      const d = meta.department_id || meta.department || null;
      return { role: r, department_id: r === "HOD" ? d : null };
    }

    // Auto-detect HOD department from email prefix (e.g., cse.hod@..., hod-ece@...)
    if (email.includes("hod")) {
      for (const deptCode of ["CSE", "ECE", "EEE", "AIML", "ME", "BBA", "BT", "CHEM", "MATH", "PHY"]) {
        if (email.includes(deptCode.toLowerCase())) {
          return { role: "HOD", department_id: deptCode };
        }
      }
      return { role: "HOD", department_id: "CSE" };
    }

    return { role: "ADMINISTRATOR", department_id: null };
  };

  const syncStateAndStorage = (sbUser, sessionToken = null) => {
    if (!sbUser) {
      setUser(null);
      setRole(null);
      setDepartment(null);
      localStorage.removeItem("platform_auth_token");
      localStorage.removeItem("platform_user_email");
      localStorage.removeItem("platform_user_role");
      localStorage.removeItem("platform_user_department");
      return;
    }

    const profile = resolveUserProfile(sbUser);

    setUser({
      id: sbUser.id || sbUser.email,
      email: sbUser.email,
      role: profile.role,
      department_id: profile.department_id,
    });
    setRole(profile.role);
    setDepartment(profile.department_id);

    if (sessionToken) {
      localStorage.setItem("platform_auth_token", sessionToken);
    } else {
      localStorage.setItem("platform_auth_token", "authenticated-token");
    }
    localStorage.setItem("platform_user_email", sbUser.email);
    localStorage.setItem("platform_user_role", profile.role);
    if (profile.department_id) {
      localStorage.setItem("platform_user_department", profile.department_id);
    } else {
      localStorage.removeItem("platform_user_department");
    }
  };

  useEffect(() => {
    const initAuth = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (session?.user) {
          syncStateAndStorage(session.user, session.access_token);
        } else {
          // Check local stored session fallback if available
          const storedEmail = localStorage.getItem("platform_user_email");
          const storedRole = localStorage.getItem("platform_user_role");
          const storedDept = localStorage.getItem("platform_user_department");
          if (storedEmail && storedRole) {
            setUser({
              id: storedEmail,
              email: storedEmail,
              role: storedRole,
              department_id: storedDept || null,
            });
            setRole(storedRole);
            setDepartment(storedDept || null);
          }
        }
      } catch (err) {
        console.warn("Auth initialization check:", err);
      } finally {
        setLoading(false);
      }
    };

    initAuth();

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session?.user) {
        syncStateAndStorage(session.user, session.access_token);
      } else {
        // If Supabase fires signed out event
        const storedToken = localStorage.getItem("platform_auth_token");
        if (!storedToken) {
          syncStateAndStorage(null);
        }
      }
    });

    return () => {
      subscription?.unsubscribe();
    };
  }, []);

  const signIn = async (email, password) => {
    setAuthError(null);
    const cleanEmail = email.trim().toLowerCase();

    // 1. Attempt Supabase Auth Sign In
    let authRes = await supabase.auth.signInWithPassword({
      email: cleanEmail,
      password: password,
    });

    if (authRes.error) {
      // Allow seamless login for demo credentials if password is supplied
      if (DEMO_USER_PROFILES[cleanEmail] && password.length >= 4) {
        const mockUser = {
          id: `demo-${cleanEmail}`,
          email: cleanEmail,
          user_metadata: {
            role: DEMO_USER_PROFILES[cleanEmail].role,
            department_id: DEMO_USER_PROFILES[cleanEmail].department_id,
          },
        };
        syncStateAndStorage(mockUser);
        window.dispatchEvent(new Event("roleChanged"));
        return mockUser;
      }

      setAuthError(authRes.error.message || "Invalid credentials or authentication failure.");
      throw new Error(authRes.error.message || "Invalid credentials or authentication failure.");
    }

    if (authRes.data?.user) {
      syncStateAndStorage(authRes.data.user, authRes.data.session?.access_token);
      window.dispatchEvent(new Event("roleChanged"));
      return authRes.data.user;
    }
  };

  const signOut = async () => {
    try {
      await supabase.auth.signOut();
    } catch (err) {
      console.warn("Supabase signout notice:", err);
    }
    syncStateAndStorage(null);
    window.dispatchEvent(new Event("roleChanged"));
  };

  const setRoleContextManual = (newRole, newDept = null) => {
    const normRole = newRole.toUpperCase();
    const normDept = normRole === "HOD" ? (newDept || "CSE").toUpperCase() : null;
    setRole(normRole);
    setDepartment(normDept);
    localStorage.setItem("platform_user_role", normRole);
    if (normDept) {
      localStorage.setItem("platform_user_department", normDept);
    } else {
      localStorage.removeItem("platform_user_department");
    }
    if (user) {
      setUser((prev) => (prev ? { ...prev, role: normRole, department_id: normDept } : null));
    }
    window.dispatchEvent(new Event("roleChanged"));
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        role,
        department,
        isAuthenticated: !!user || !!localStorage.getItem("platform_auth_token"),
        loading,
        authError,
        signIn,
        signOut,
        setRoleContextManual,
        demoProfiles: DEMO_USER_PROFILES,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
