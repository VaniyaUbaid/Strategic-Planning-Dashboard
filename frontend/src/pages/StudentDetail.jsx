import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, User, Award, Home, Calendar, BookOpen, Building } from "lucide-react";
import { api } from "../services/api";
import LoadingSpinner from "../components/common/LoadingSpinner";
import ErrorAlert from "../components/common/ErrorAlert";
import RiskOverviewCard from "../components/students/RiskOverviewCard";
import FactorsBreakdown from "../components/students/FactorsBreakdown";
import AcademicHistoryTable from "../components/students/AcademicHistoryTable";
import AcademicHistoryCharts from "../components/students/AcademicHistoryCharts";

export default function StudentDetail() {
  const { studentId } = useParams();

  const [profile, setProfile] = useState(null);
  const [risk, setRisk] = useState(null);
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStudentData = () => {
    setLoading(true);
    setError(null);

    Promise.all([
      api.getStudentProfile(studentId),
      api.getStudentRisk(studentId),
      api.getStudentHistory(studentId),
    ])
      .then(([profileRes, riskRes, historyRes]) => {
        setProfile(profileRes);
        setRisk(riskRes);
        setHistory(historyRes.history || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching student details:", err);
        setError(err.message || `Student '${studentId}' not found.`);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchStudentData();
  }, [studentId]);

  if (loading) return <LoadingSpinner message={`Loading risk & academic profile for ${studentId}...`} />;
  if (error) {
    return (
      <div>
        <Link to="/students" className="btn-secondary" style={{ marginBottom: "1.5rem" }}>
          <ArrowLeft size={16} /> Back to Student Directory
        </Link>
        <ErrorAlert message={error} onRetry={fetchStudentData} />
      </div>
    );
  }

  return (
    <div>
      {/* Navigation Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.5rem" }}>
        <Link to="/students" className="btn-secondary">
          <ArrowLeft size={16} /> Back to Student Directory
        </Link>

        <span style={{ fontSize: "0.85rem", color: "#64748b" }}>
          Prediction Target: Next Semester Dropout Risk
        </span>
      </div>

      {/* Top Grid: Profile Card & Risk Card */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "1.5rem", marginBottom: "1.5rem" }}>
        {/* Profile Card */}
        <div className="card">
          <div className="card-header">
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <User size={20} className="text-blue-600" />
              <h3 className="card-title">Student Profile</h3>
            </div>
            <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "#1e293b", backgroundColor: "#f1f5f9", padding: "0.2rem 0.6rem", borderRadius: "0.25rem" }}>
              {profile?.student_id}
            </span>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", fontSize: "0.9rem" }}>
            <div>
              <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 600 }}>PROGRAM</span>
              <p style={{ fontWeight: 600, color: "#0f172a" }}>{profile?.program || "N/A"}</p>
            </div>

            <div>
              <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 600 }}>DEPARTMENT</span>
              <p style={{ fontWeight: 600, color: "#0f172a" }}>
                {profile?.department_name ? `${profile.department_name} (${profile.department_id})` : profile?.department_id || "N/A"}
              </p>
            </div>

            <div>
              <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 600 }}>LATEST SEMESTER</span>
              <p style={{ fontWeight: 600, color: "#0f172a" }}>Semester {profile?.semester}</p>
            </div>

            <div>
              <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 600 }}>ACADEMIC YEAR</span>
              <p style={{ fontWeight: 600, color: "#0f172a" }}>{profile?.academic_year}</p>
            </div>

            <div>
              <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 600 }}>GENDER</span>
              <p style={{ fontWeight: 600, color: "#0f172a" }}>{profile?.gender || "N/A"}</p>
            </div>

            <div>
              <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 600 }}>ADMISSION YEAR</span>
              <p style={{ fontWeight: 600, color: "#0f172a" }}>{profile?.admission_year}</p>
            </div>

            <div>
              <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 600 }}>SCHOLARSHIP</span>
              <p style={{ fontWeight: 600, color: profile?.scholarship_status === 1 ? "#047857" : "#475569" }}>
                {profile?.scholarship_status === 1 ? "Active Scholarship" : "None"}
              </p>
            </div>

            <div>
              <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 600 }}>HOSTEL RESIDENT</span>
              <p style={{ fontWeight: 600, color: profile?.hostel_status === 1 ? "#2563eb" : "#475569" }}>
                {profile?.hostel_status === 1 ? "Yes" : "Day Scholar"}
              </p>
            </div>
          </div>
        </div>

        {/* Risk Card */}
        <RiskOverviewCard riskData={risk} />
      </div>

      {/* Feature Explainability Breakdown */}
      <div style={{ marginBottom: "2rem" }}>
        <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#0f172a", marginBottom: "1rem" }}>
          Feature-Level Risk Explainability Factors
        </h2>
        <FactorsBreakdown riskFactors={risk?.risk_factors} protectiveFactors={risk?.protective_factors} />
      </div>

      {/* Academic Progression Charts */}
      <div style={{ marginBottom: "2rem" }}>
        <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#0f172a", marginBottom: "1rem" }}>
          Academic Progression & Attendance Trends
        </h2>
        <AcademicHistoryCharts history={history} />
      </div>

      {/* Semester History Table */}
      <div className="card">
        <h3 className="card-title" style={{ marginBottom: "1rem" }}>
          Semester-by-Semester Performance Records
        </h3>
        <AcademicHistoryTable history={history} />
      </div>
    </div>
  );
}
