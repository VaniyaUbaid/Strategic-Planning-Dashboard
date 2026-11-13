
# Institutional Decision Platform

### An Integrated Strategic Planning and Decision Support System for Higher Education Institutions

A centralized platform for institutional analytics, predictive insights, and data-driven decision-making.

---

## Overview

The **Institutional Decision Platform** is a web-based decision support system designed to help higher education institutions monitor, analyze, and evaluate institutional performance through a unified interface.

The platform integrates three major institutional domains:

- **Student Analytics:** Enrollment monitoring, student performance, and dropout-risk prediction.
- **Financial Analytics:** Budget utilization, revenue, expenditure, and fee collection analysis.
- **Research Analytics:** Faculty research profiles, publication statistics, and research productivity.

It also features an integrated **Decision Assistant** that retrieves information across these modules and provides evidence-based insights to support institutional planning.

The system supports two user roles: Administrator and Head of Department (HOD), with department-level access restrictions.

## Key Features

### 1. Student Dashboard

- Student enrollment analytics.
- Student Success and dropout-risk prediction.
- Student risk distribution and visualizations.
- Enrolled student directory with filtering and pagination.
- Department-level student performance.
- Individual student details and academic history.

### 2. Financial Analytics Dashboard

- Revenue and expenditure analysis.
- Budget allocation and utilization.
- Fee collection and outstanding fee analysis.
- Scholarship analytics.
- Department-wise financial comparisons.
- Financial risk insights.

### 3. Research Profile Dashboard

- Faculty research profiles.
- Publication statistics.
- Department-wise research comparisons.
- Faculty research productivity analysis.
- Research performance insights.

### 4. Decision Assistant

The Decision Assistant connects the three institutional modules to support informed decision-making.

- Processes natural-language institutional queries.
- Retrieves relevant student, financial, and research information.
- Supports cross-module analysis.
- Provides evidence-based responses.
- Respects Administrator and HOD access permissions.

### 5. Role-Based Access Control

| Role | Access |
|---|---|
| Administrator | Institution-wide dashboards and analytics |
| HOD | Department-specific dashboards and information |

Department-level restrictions are enforced by the backend to prevent unauthorized access to other departments' information.

---

## System Architecture

The platform follows a frontend-backend architecture.

```text
                         USERS
                           |
                           v
                     REACT FRONTEND
                           |
                           v
                     FASTAPI BACKEND
                           |
                AUTHENTICATION & AUTHORIZATION
                           |
              +------------+------------+
              |            |            |
              v            v            v
           STUDENT       FINANCE      RESEARCH
           SERVICE       SERVICE      SERVICE
              |            |            |
              v            v            v
           ML MODEL     SUPABASE     SUPABASE
           & LOCAL      DATABASE     DATABASE
           DATA
              |
              +------------------------+
                                       |
                                       v
                              DECISION ASSISTANT
                                       |
                                       v
                               INTEGRATED INSIGHTS
```

## Technology Stack

| Component | Technologies |
|---|---|
| Frontend | React, Vite, JavaScript |
| Backend | Python, FastAPI |
| Database | Supabase PostgreSQL |
| Authentication | Supabase Auth |
| Data Processing | Pandas, NumPy |
| Machine Learning | Scikit-learn |
| API Communication | REST APIs |
| Version Control | Git, GitHub |

---

## Machine Learning

The Student module incorporates a machine learning-based Student Success model to identify students who may be at risk of dropping out.

The model processes student academic and related features to generate risk predictions.

These predictions are integrated into the Student Dashboard to support early identification and institutional intervention.

**Note:** Model predictions are decision-support indicators and should not be treated as definitive judgments about individual students.

---

## Project Structure

The repository contains separate frontend and backend components.

```text
institutional-decision-platform/
│
├── backend/
│   ├── common/
│   ├── student/
│   ├── finance/
│   ├── research/
│   ├── decision/
│   └── main.py
│
├── frontend/
│   ├── public/
│   ├── src/
│   └── package.json
│
├── data/
│   └── student/
│
├── models/
│   └── student_success_model.joblib
│
├── tests/
│
├── requirements.txt
├── .gitignore
└── README.md
```

*The structure is representative. Refer to the repository for the complete directory structure.*

---

## Getting Started

### Prerequisites

Ensure that the following are installed:

- Python 3.10 or later (use the version supported by project dependencies).
- Node.js and npm.
- Git.
- A configured Supabase project.

### 1. Clone the Repository

```bash
git clone https://github.com/VaniyaUbaid/Strategic-Planning-Dashboard.git

cd Strategic-Planning-Dashboard
```

### 2. Backend Setup

Create and activate a virtual environment.

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```bash
pip install -r requirements.txt
```

Configure the environment variables expected by the backend.

Example:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_ROLE_KEY=your_server_side_secret_key
```

Use the exact environment variable names expected by the project configuration. Never commit secret keys or credentials to GitHub.

Start the backend:

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

### 3. Frontend Setup

Open another terminal:

```bash
cd frontend
npm install
```

Configure the frontend environment variables as required by the application, including the Supabase project URL and publishable/anon key if used by the frontend.

Start the development server:

```bash
npm run dev
```

Open the local URL displayed by Vite in your terminal.

---

## Configuration and Security

- Supabase is used for authentication and supported institutional data storage.
- Backend authorization validates authenticated users and their assigned roles.
- HOD access is restricted to the authorized department.
- Sensitive server-side credentials must remain in environment variables.
- Environment files and private credentials should never be committed to the repository.

## Testing

The backend includes tests for application functionality, role-based access, filtering, and Decision Assistant behavior.

Run backend tests:

```bash
pytest
```

Build the frontend:

```bash
cd frontend
npm run build
```

---

## Project Objectives Achieved

- Integrated student, financial, and faculty research analytics.
- Developed a centralized institutional dashboard.
- Implemented machine learning-based student risk prediction.
- Integrated a cross-module Decision Assistant.
- Implemented Administrator and HOD authentication and authorization.
- Enabled department-specific analytics and information access.
- Established a unified platform for institutional decision support.

## Future Scope

Potential enhancements include:

- Additional predictive analytics and forecasting models.
- Integration with more institutional information systems.
- Automated institutional reports.
- Advanced analytics and trend detection.
- Expanded decision-support capabilities.

## Disclaimer

This project was developed as an academic special project. Certain datasets may contain generated or seeded demonstration records. Such records should not be interpreted as verified institutional records.

## Contributors

**Project:** Institutional Decision Platform  
**Institution:** ICFAI Tech School, Hyderabad  
**Domain:** Computer Science and Engineering

---

<p align="center">
  <b>Institutional Decision Platform</b><br>
  Turning institutional data into actionable insights.
</p>
