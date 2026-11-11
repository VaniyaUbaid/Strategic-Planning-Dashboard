import React from "react";
import { ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";

export default function DepartmentPerformanceHeader({ title, description, backTo, backLabel = "Back to Dashboard" }) {
  return (
    <header className="department-performance-heading">
      <div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      <Link to={backTo} className="btn-secondary">
        <ArrowLeft size={16} /> {backLabel}
      </Link>
    </header>
  );
}
