import React from "react";
import { useNavigate } from "react-router-dom";
import { Activity, Shield, LogOut } from "lucide-react";
import { useAuth } from "../../context/AuthContext";

export default function Header({ pageTitle = "Dashboard" }) {
  const { user, role, department, signOut } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await signOut();
    navigate("/login", { replace: true });
  };

  const isHod = role === "HOD";

  return (
    <header className="header-bar">
      <div>
        <h2 className="header-title">{pageTitle}</h2>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        {/* User Role Badge & Access Level Indicator */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
            backgroundColor: isHod ? "#fffbeb" : "#eff6ff",
            padding: "0.4rem 0.85rem",
            borderRadius: "0.5rem",
            border: `1px solid ${isHod ? "#fde68a" : "#bfdbfe"}`,
          }}
        >
          <Shield size={16} color={isHod ? "#d97706" : "#2563eb"} />
          <div style={{ display: "flex", flexDirection: "column" }}>
            <span style={{ fontSize: "0.8rem", fontWeight: 700, color: "#0f172a", lineHeight: 1.2 }}>
              {isHod ? `${department} HOD` : "Administrator"}
            </span>
            <span style={{ fontSize: "0.7rem", color: isHod ? "#b45309" : "#1d4ed8", fontWeight: 600 }}>
              {isHod ? `Department Access (${department})` : "Institution-wide Access"}
            </span>
          </div>
        </div>

        {/* User Email Indicator */}
        {user?.email && (
          <span style={{ fontSize: "0.8rem", color: "#64748b", fontWeight: 500 }}>
            {user.email}
          </span>
        )}

        {/* API Connected Status */}
        <div className="header-status">
          <span className="status-dot"></span>
          <Activity size={14} style={{ color: "#059669" }} />
          <span>API Connected</span>
        </div>

        {/* Logout Button */}
        <button
          type="button"
          onClick={handleLogout}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.4rem",
            padding: "0.45rem 0.75rem",
            borderRadius: "0.375rem",
            border: "1px solid #cbd5e1",
            backgroundColor: "#ffffff",
            color: "#64748b",
            fontSize: "0.8rem",
            fontWeight: 600,
            cursor: "pointer",
            transition: "all 0.15s ease",
          }}
          title="Sign out of platform"
        >
          <LogOut size={15} /> Sign Out
        </button>
      </div>
    </header>
  );
}
