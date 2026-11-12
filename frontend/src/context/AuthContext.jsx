import React, { createContext, useContext, useEffect, useRef, useState } from "react";
import { supabase } from "../utils/supabase";
import { api } from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [role, setRole] = useState(null);
  const [department, setDepartment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(null);
  const sessionRequest = useRef(0);

  const clearSession = () => {
    sessionRequest.current += 1;
    setUser(null);
    setRole(null);
    setDepartment(null);
    setAuthError(null);
    localStorage.removeItem("platform_auth_token");
    localStorage.removeItem("platform_user_email");
    localStorage.removeItem("platform_user_role");
    localStorage.removeItem("platform_user_department");
  };

  const applySession = async (session) => {
    const requestId = ++sessionRequest.current;
    if (!session?.access_token || !session.user) {
      clearSession();
      return null;
    }

    localStorage.setItem("platform_auth_token", session.access_token);
    try {
      const verifiedUser = await api.getCurrentUser(session.access_token);
      if (requestId !== sessionRequest.current) return null;

      const profile = {
        id: verifiedUser.user_id,
        email: verifiedUser.email || session.user.email || "",
      };
      setUser(profile);
      setRole(verifiedUser.role);
      setDepartment(verifiedUser.department_id);
      setAuthError(null);
      localStorage.setItem("platform_user_email", profile.email);
      localStorage.setItem("platform_user_role", verifiedUser.role);
      if (verifiedUser.department_id) {
        localStorage.setItem("platform_user_department", verifiedUser.department_id);
      } else {
        localStorage.removeItem("platform_user_department");
      }
      return verifiedUser;
    } catch (error) {
      if (requestId !== sessionRequest.current) return null;
      setUser(null);
      setRole(null);
      setDepartment(null);
      setAuthError(error.message || "Your account could not be authorized.");
      localStorage.removeItem("platform_user_email");
      localStorage.removeItem("platform_user_role");
      localStorage.removeItem("platform_user_department");
      return null;
    }
  };

  useEffect(() => {
    let active = true;
    const initialize = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (active) await applySession(session);
      } catch (error) {
        if (active) {
          clearSession();
          setAuthError(error.message || "Unable to restore the Supabase session.");
        }
      } finally {
        if (active) setLoading(false);
      }
    };

    initialize();
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === "INITIAL_SESSION" || event === "SIGNED_IN") return;
      if (event === "SIGNED_OUT" || !session) {
        clearSession();
        return;
      }
      void applySession(session);
    });

    return () => {
      active = false;
      sessionRequest.current += 1;
      subscription?.unsubscribe();
    };
  }, []);

  const signIn = async (email, password) => {
    setAuthError(null);
    const { data, error } = await supabase.auth.signInWithPassword({
      email: email.trim().toLowerCase(),
      password,
    });
    if (error) {
      setAuthError(error.message);
      throw new Error(error.message);
    }
    if (!data.session) {
      const message = "Supabase sign-in did not return an authenticated session.";
      setAuthError(message);
      throw new Error(message);
    }

    const verifiedUser = await applySession(data.session);
    if (!verifiedUser) {
      const message = "Your account is authenticated but has no valid application role assignment.";
      setAuthError(message);
      throw new Error(message);
    }
    return data.user;
  };

  const signOut = async () => {
    try {
      const { error } = await supabase.auth.signOut();
      if (error) throw error;
    } finally {
      clearSession();
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        role,
        department,
        isAuthenticated: Boolean(user && role && localStorage.getItem("platform_auth_token")),
        loading,
        authError,
        signIn,
        signOut,
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
