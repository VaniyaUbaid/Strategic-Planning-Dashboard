import React, { useState, useEffect } from "react";
import { Outlet, useLocation } from "react-router-dom";
import Sidebar from "./Sidebar";
import Header from "./Header";
import { api } from "../../services/api";

export default function Layout() {
  const location = useLocation();
  const [moduleStatus, setModuleStatus] = useState(null);

  useEffect(() => {
    api
      .getModulesStatus()
      .then((data) => setModuleStatus(data))
      .catch((err) => console.warn("Could not fetch module status:", err));
  }, []);

  const getPageTitle = (path) => {
    if (path === "/") return "Platform Overview";
    if (path === "/students/department-performance") return "Student Department Performance";
    if (path.startsWith("/students/")) return "Student Performance & Risk Analysis";
    if (path === "/students") return "Student Success & Dropout Risk Management";
    if (path === "/finance") return "Financial Intelligence Module";
    if (path === "/finance/department-performance") return "Finance Department Performance";
    if (path === "/research") return "Institutional Research Analytics";
    if (path === "/research/department-performance") return "Research Department Performance";
    if (path === "/decisions") return "Executive Decision Assistant";
    if (path === "/department-performance") return "Department Performance";
    return "Institutional Decision Platform";
  };

  return (
    <div className="app-container">
      <Sidebar moduleStatus={moduleStatus} />
      <div className="main-wrapper">
        <Header pageTitle={getPageTitle(location.pathname)} />
        <main className="content-area">
          <Outlet context={{ moduleStatus }} />
        </main>
      </div>
    </div>
  );
}
