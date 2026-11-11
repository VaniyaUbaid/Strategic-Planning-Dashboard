import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  GraduationCap,
  DollarSign,
  Microscope,
  BrainCircuit,
  Building2,
  LogOut,
  UserCheck,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";

export default function Sidebar({ moduleStatus }) {
  const { user, role, department, signOut } = useAuth();
  const navigate = useNavigate();

  const isStudentReady = moduleStatus?.student === "ready";
  const isFinanceReady = moduleStatus?.finance === "ready";
  const isResearchReady = moduleStatus?.research === "ready";
  const isDecisionReady = moduleStatus?.decision_assistant === "ready";

  const isHod = role === "HOD";

  const handleSignOut = async () => {
    await signOut();
    navigate("/login", { replace: true });
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <Building2 className="text-blue-500" size={28} />
        <div>
          <h1 className="sidebar-brand">Institutional Decision Platform</h1>
          <p style={{ fontSize: "0.75rem", color: "#94a3b8" }}>Enterprise Intelligence</p>
        </div>
      </div>

      <nav className="sidebar-nav">
        <NavLink
          to="/"
          end
          className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
        >
          <LayoutDashboard size={20} />
          <span>Overview</span>
        </NavLink>

        <NavLink
          to="/students"
          className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
        >
          <GraduationCap size={20} />
          <span>Students</span>
          <span className={`nav-item-badge ${isStudentReady ? "badge-ready" : "badge-soon"}`}>
            {isStudentReady ? "READY" : "SOON"}
          </span>
        </NavLink>

        <NavLink
          to="/finance"
          className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
        >
          <DollarSign size={20} />
          <span>Finance</span>
          <span className={`nav-item-badge ${isFinanceReady ? "badge-ready" : "badge-soon"}`}>
            {isFinanceReady ? "READY" : "SOON"}
          </span>
        </NavLink>

        <NavLink
          to="/research"
          className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
        >
          <Microscope size={20} />
          <span>Research</span>
          <span className={`nav-item-badge ${isResearchReady ? "badge-ready" : "badge-soon"}`}>
            {isResearchReady ? "READY" : "SOON"}
          </span>
        </NavLink>

        <NavLink
          to="/decisions"
          className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
        >
          <BrainCircuit size={20} />
          <span>Decision Assistant</span>
          <span className={`nav-item-badge ${isDecisionReady ? "badge-ready" : "badge-soon"}`}>
            {isDecisionReady ? "READY" : "SOON"}
          </span>
        </NavLink>
      </nav>

      {/* User Profile & Role Indicator */}
      <div style={{ padding: "1rem 1.25rem", borderTop: "1px solid #1e293b", backgroundColor: "#0f172a" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.75rem" }}>
          <div style={{ padding: "0.5rem", borderRadius: "50%", backgroundColor: isHod ? "#b45309" : "#1d4ed8", color: "#ffffff" }}>
            <UserCheck size={16} />
          </div>
          <div style={{ minWidth: 0, flexGrow: 1 }}>
            <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "#ffffff", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {isHod ? `${department || "CSE"} HOD` : "Administrator"}
            </div>
            <div style={{ fontSize: "0.75rem", color: "#94a3b8", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {user?.email || (isHod ? `hod.${(department || "cse").toLowerCase()}@institution.edu` : "admin@institution.edu")}
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={handleSignOut}
          style={{
            width: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "0.5rem",
            padding: "0.45rem",
            borderRadius: "0.375rem",
            border: "1px solid #334155",
            backgroundColor: "#1e293b",
            color: "#cbd5e1",
            fontSize: "0.8rem",
            fontWeight: 600,
            cursor: "pointer",
            transition: "all 0.15s ease",
          }}
        >
          <LogOut size={15} /> Sign Out
        </button>
      </div>
    </aside>
  );
}
