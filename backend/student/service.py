import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from fastapi import HTTPException

import json
from backend.student.schemas import (
    AcademicYearAnalyticsItem,
    DepartmentAnalyticsItem,
    DepartmentOption,
    DetailedOverviewResponse,
    FeatureFactor,
    FilterOptionsResponse,
    HodOverviewResponse,
    InstitutionalOverviewResponse,
    ModelFeatureInsight,
    OverviewRiskDistribution,
    PaginatedDetailedStudentListResponse,
    PaginatedStudentListResponse,
    RiskDistribution,
    SemesterAnalyticsItem,
    SemesterHistoryItem,
    SimpleFilterOptionsResponse,
    StudentDetailedListItem,
    StudentHistoryResponse,
    StudentModelInsightsResponse,
    StudentProfileResponse,
    StudentRiskResponse,
    StudentSummaryItem,
)



class StudentService:
    DEPT_MAP = {
        "CSE": "Computer Science & Engineering",
        "AIML": "AI & Machine Learning",
        "BBA": "Business Administration",
        "ECE": "Electronics & Communication",
        "EEE": "Electrical & Electronics",
        "ME": "Mechanical Engineering",
        "BT": "Biotechnology",
        "MATH": "Mathematics",
        "CHEM": "Chemistry",
        "PHY": "Physics",
    }

    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[2]
        self.data_path = self.project_root / "data" / "student" / "dropout_model_dataset_v2.csv"
        self.model_path = self.project_root / "models" / "student_success_model.joblib"

        self.pipeline = None
        self.df = None
        self.student_groups: Dict[str, pd.DataFrame] = {}
        self.unique_student_ids: List[str] = []

        self._load_resources()

    def get_dept_name(self, dept_id: Optional[str]) -> str:
        if not dept_id:
            return "All Departments"
        return self.DEPT_MAP.get(dept_id.upper(), dept_id.upper())

    def normalize_department(self, dept_input: Optional[str]) -> Optional[str]:
        if not dept_input or str(dept_input).strip().upper() in ["ALL", "NONE", "", "NULL"]:
            return None

        clean_input = str(dept_input).strip().upper()
        if clean_input in self.DEPT_MAP:
            return clean_input

        # Partial or alias matching
        for code, name in self.DEPT_MAP.items():
            if clean_input in name.upper() or name.upper() in clean_input:
                return code
            if clean_input in code:
                return code

        # Common aliases
        alias_map = {
            "COMPUTER SCIENCE": "CSE",
            "COMPUTER SCIENCE & ENGINEERING": "CSE",
            "ELECTRONICS": "ECE",
            "MECHANICAL": "ME",
            "ELECTRICAL": "EEE",
            "CIVIL": "BT", # fallback mapping if CIVIL passed
        }
        for alias, code in alias_map.items():
            if alias in clean_input:
                return code

        return clean_input

    def _load_resources(self):
        """Pre-loads ML pipeline model and dataset once at startup."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found at: {self.model_path}")
        if not self.data_path.exists():
            raise FileNotFoundError(f"Dataset file not found at: {self.data_path}")

        print(f"[StudentService] Loading model from: {self.model_path}")
        self.pipeline = joblib.load(self.model_path)

        print(f"[StudentService] Loading dataset from: {self.data_path}")
        df_raw = pd.read_csv(self.data_path)

        # Feature engineering matching model training
        if "date_of_birth" in df_raw.columns:
            df_raw["date_of_birth"] = pd.to_datetime(df_raw["date_of_birth"], errors="coerce")
            df_raw["age"] = df_raw["academic_year"] - df_raw["date_of_birth"].dt.year
            df_raw = df_raw.drop(columns=["date_of_birth"])

        bool_cols = ["scholarship_status", "hostel_status"]
        for col in bool_cols:
            if col in df_raw.columns:
                df_raw[col] = df_raw[col].astype(int)

        self.df = df_raw.sort_values(by=["student_id", "semester"]).reset_index(drop=True)

        # Precompute ML model risk probabilities & levels across dataset
        print(f"[StudentService] Running ML model risk inference on all {len(self.df):,} semester records...")
        X_all = self.df.drop(
            columns=["future_dropout", "student_id", "state"],
            errors="ignore",
        )
        probs = self.pipeline.predict_proba(X_all)[:, 1]
        self.df["dropout_probability"] = np.round(probs, 4)

        risk_levels = []
        for p in probs:
            if p >= 0.60:
                risk_levels.append("HIGH")
            elif p >= 0.40:
                risk_levels.append("MEDIUM")
            else:
                risk_levels.append("LOW")
        self.df["risk_level"] = risk_levels

        self.unique_student_ids = sorted(self.df["student_id"].unique().tolist())

        # Pre-group by student_id for fast detail lookup
        self.student_groups = {
            student_id: group.copy()
            for student_id, group in self.df.groupby("student_id")
        }
        print(f"[StudentService] Cached {len(self.unique_student_ids):,} unique students with pre-computed risk predictions.")

    def get_risk_level(self, prob: float) -> str:
        if prob >= 0.60:
            return "HIGH"
        elif prob >= 0.40:
            return "MEDIUM"
        else:
            return "LOW"

    def filter_records(
        self,
        role: str = "ADMINISTRATOR",
        user_dept: Optional[str] = None,
        department: Optional[str] = None,
        academic_year: Optional[int] = None,
        semester: Optional[int] = None,
        risk_level: Optional[str] = None,
        search: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Enforces security role scope and dynamic filtering parameters.
        Returns filtered DataFrame of latest student records per student matching criteria.
        """
        user_role = role.upper() if role else "ADMINISTRATOR"
        target_df = self.df.copy()

        # Security Enforcement for HOD and PROFESSOR
        if user_role in ["HOD", "PROFESSOR"]:
            if not user_dept:
                user_dept = "CSE"  # default fallback mock department
            assigned_dept = self.normalize_department(user_dept)

            if department:
                req_dept = self.normalize_department(department)
                if req_dept and req_dept != assigned_dept:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Access denied. {user_role} is restricted to '{self.get_dept_name(assigned_dept)}' department."
                    )

            target_df = target_df[target_df["department_id"] == assigned_dept]
        else:
            # ADMINISTRATOR role filtering
            if department:
                norm_dept = self.normalize_department(department)
                if norm_dept:
                    target_df = target_df[target_df["department_id"] == norm_dept]

        # Dynamic Filters
        if academic_year is not None and str(academic_year).strip() not in ["", "0"]:
            target_df = target_df[target_df["academic_year"] == int(academic_year)]

        if semester is not None and str(semester).strip() not in ["", "0"]:
            target_df = target_df[target_df["semester"] == int(semester)]

        if risk_level and str(risk_level).strip().upper() not in ["ALL", "NONE", ""]:
            target_df = target_df[target_df["risk_level"] == str(risk_level).strip().upper()]

        if search and str(search).strip():
            query = str(search).strip().lower()
            target_df = target_df[target_df["student_id"].str.lower().str.contains(query)]

        if target_df.empty:
            return pd.DataFrame()

        # Pick latest matching semester record per student for clean unique student view
        latest_filtered = target_df.sort_values(by=["student_id", "semester"]).groupby("student_id").last().reset_index()
        return latest_filtered

    def get_available_departments(self, role: str = "ADMINISTRATOR", user_dept: Optional[str] = None) -> List[DepartmentOption]:
        user_role = role.upper() if role else "ADMINISTRATOR"
        if user_role in ["HOD", "PROFESSOR"]:
            assigned_dept = self.normalize_department(user_dept) or "CSE"
            return [DepartmentOption(id=assigned_dept, name=self.get_dept_name(assigned_dept))]

        unique_depts = sorted(self.df["department_id"].unique().tolist())
        return [DepartmentOption(id=dept, name=self.get_dept_name(dept)) for dept in unique_depts]

    def get_available_years(
        self,
        role: str = "ADMINISTRATOR",
        user_dept: Optional[str] = None,
        department: Optional[str] = None,
    ) -> List[int]:
        user_role = role.upper() if role else "ADMINISTRATOR"
        filtered = self.df.copy()

        if user_role in ["HOD", "PROFESSOR"]:
            assigned_dept = self.normalize_department(user_dept) or "CSE"
            filtered = filtered[filtered["department_id"] == assigned_dept]
        elif department:
            norm_dept = self.normalize_department(department)
            if norm_dept:
                filtered = filtered[filtered["department_id"] == norm_dept]

        if filtered.empty:
            return []
        return sorted([int(y) for y in filtered["academic_year"].unique()])

    def get_available_semesters(
        self,
        role: str = "ADMINISTRATOR",
        user_dept: Optional[str] = None,
        department: Optional[str] = None,
        academic_year: Optional[int] = None,
    ) -> List[int]:
        user_role = role.upper() if role else "ADMINISTRATOR"
        filtered = self.df.copy()

        if user_role in ["HOD", "PROFESSOR"]:
            assigned_dept = self.normalize_department(user_dept) or "CSE"
            filtered = filtered[filtered["department_id"] == assigned_dept]
        elif department:
            norm_dept = self.normalize_department(department)
            if norm_dept:
                filtered = filtered[filtered["department_id"] == norm_dept]

        if academic_year is not None and str(academic_year).strip() not in ["", "0"]:
            filtered = filtered[filtered["academic_year"] == int(academic_year)]

        if filtered.empty:
            return []
        return sorted([int(s) for s in filtered["semester"].unique()])

    def compute_risk_distribution(self, df_records: pd.DataFrame) -> RiskDistribution:
        total = len(df_records)
        if total == 0:
            return RiskDistribution(high_count=0, medium_count=0, low_count=0, high_pct=0.0, medium_pct=0.0, low_pct=0.0)

        high_c = int((df_records["risk_level"] == "HIGH").sum())
        med_c = int((df_records["risk_level"] == "MEDIUM").sum())
        low_c = int((df_records["risk_level"] == "LOW").sum())

        return RiskDistribution(
            high_count=high_c,
            medium_count=med_c,
            low_count=low_c,
            high_pct=round((high_c / total) * 100, 1),
            medium_pct=round((med_c / total) * 100, 1),
            low_pct=round((low_c / total) * 100, 1),
        )

    def get_simple_filters(
        self,
        department: Optional[str] = None,
        academic_year: Optional[int] = None,
    ) -> SimpleFilterOptionsResponse:
        depts = sorted(self.df["department_id"].unique().tolist())

        filtered = self.df.copy()
        if department:
            norm_dept = self.normalize_department(department)
            if norm_dept:
                filtered = filtered[filtered["department_id"] == norm_dept]

        years = sorted([int(y) for y in filtered["academic_year"].unique()])

        if academic_year is not None and str(academic_year).strip() not in ["", "0"]:
            filtered = filtered[filtered["academic_year"] == int(academic_year)]

        semesters = sorted([int(s) for s in filtered["semester"].unique()])

        return SimpleFilterOptionsResponse(
            departments=depts,
            academic_years=years,
            semesters=semesters,
            risk_levels=["LOW", "MEDIUM", "HIGH"],
        )

    def get_admin_overview(
        self,
        role: str = "ADMINISTRATOR",
        user_dept: Optional[str] = None,
        department: Optional[str] = None,
        academic_year: Optional[int] = None,
        semester: Optional[int] = None,
        risk_level: Optional[str] = None,
    ) -> DetailedOverviewResponse:
        filtered_df = self.filter_records(
            role=role,
            user_dept=user_dept,
            department=department,
            academic_year=academic_year,
            semester=semester,
            risk_level=risk_level,
        )

        total_students = len(filtered_df)
        if total_students == 0:
            return DetailedOverviewResponse(
                user_role=role,
                department_filter=department,
                academic_year_filter=academic_year,
                semester_filter=semester,
                total_students=0,
                average_gpa=0.0,
                average_attendance=0.0,
                average_dropout_probability=0.0,
                model_status="active",
                risk_distribution=OverviewRiskDistribution(
                    low=0, medium=0, high=0, high_count=0, medium_count=0, low_count=0, high_pct=0.0, medium_pct=0.0, low_pct=0.0
                ),
                high_risk_count=0,
                medium_risk_count=0,
                low_risk_count=0,
                students_with_backlogs=0,
                students_fee_pending=0,
                total_fee_pending_amount=0.0,
                department_chart=[],
                semester_chart=[],
                academic_year_chart=[],
            )

        avg_gpa = round(float(filtered_df["cumulative_gpa"].mean()), 2)
        avg_att = round(float(filtered_df["attendance_percentage"].mean()), 1)
        avg_dropout_prob = round(float(filtered_df["dropout_probability"].mean()), 2)
        raw_risk_dist = self.compute_risk_distribution(filtered_df)

        risk_dist = OverviewRiskDistribution(
            low=raw_risk_dist.low_count,
            medium=raw_risk_dist.medium_count,
            high=raw_risk_dist.high_count,
            high_count=raw_risk_dist.high_count,
            medium_count=raw_risk_dist.medium_count,
            low_count=raw_risk_dist.low_count,
            high_pct=raw_risk_dist.high_pct,
            medium_pct=raw_risk_dist.medium_pct,
            low_pct=raw_risk_dist.low_pct,
        )

        backlogs_c = int((filtered_df["backlog_count"] > 0).sum())
        fee_pending_c = int((filtered_df["fee_pending_amount"] > 0).sum())
        total_fee_pending_amt = round(float(filtered_df["fee_pending_amount"].sum()), 2)

        # Department Comparison Chart Data
        dept_chart_items = []
        for dept_id, group in filtered_df.groupby("department_id"):
            g_dist = self.compute_risk_distribution(group)
            dept_chart_items.append(
                DepartmentAnalyticsItem(
                    department_id=dept_id,
                    department_name=self.get_dept_name(dept_id),
                    total_students=len(group),
                    avg_gpa=round(float(group["cumulative_gpa"].mean()), 2),
                    avg_attendance=round(float(group["attendance_percentage"].mean()), 1),
                    high_risk_count=g_dist.high_count,
                    medium_risk_count=g_dist.medium_count,
                    low_risk_count=g_dist.low_count,
                    students_with_backlogs=int((group["backlog_count"] > 0).sum()),
                    students_fee_pending=int((group["fee_pending_amount"] > 0).sum()),
                    total_fee_pending=round(float(group["fee_pending_amount"].sum()), 2),
                )
            )
        dept_chart_items.sort(key=lambda x: x.total_students, reverse=True)

        # Semester Chart Data
        sem_chart_items = []
        for sem_num, group in filtered_df.groupby("semester"):
            g_dist = self.compute_risk_distribution(group)
            sem_chart_items.append(
                SemesterAnalyticsItem(
                    semester=int(sem_num),
                    total_students=len(group),
                    avg_gpa=round(float(group["cumulative_gpa"].mean()), 2),
                    avg_attendance=round(float(group["attendance_percentage"].mean()), 1),
                    high_risk_count=g_dist.high_count,
                    medium_risk_count=g_dist.medium_count,
                    low_risk_count=g_dist.low_count,
                )
            )
        sem_chart_items.sort(key=lambda x: x.semester)

        # Academic Year Chart Data
        year_chart_items = []
        for yr_num, group in filtered_df.groupby("academic_year"):
            g_dist = self.compute_risk_distribution(group)
            year_chart_items.append(
                AcademicYearAnalyticsItem(
                    academic_year=int(yr_num),
                    total_students=len(group),
                    avg_gpa=round(float(group["cumulative_gpa"].mean()), 2),
                    avg_attendance=round(float(group["attendance_percentage"].mean()), 1),
                    high_risk_count=g_dist.high_count,
                )
            )
        year_chart_items.sort(key=lambda x: x.academic_year)

        return DetailedOverviewResponse(
            user_role=role,
            department_filter=department,
            academic_year_filter=academic_year,
            semester_filter=semester,
            total_students=total_students,
            average_gpa=avg_gpa,
            average_attendance=avg_att,
            average_dropout_probability=avg_dropout_prob,
            model_status="active",
            risk_distribution=risk_dist,
            high_risk_count=risk_dist.high_count,
            medium_risk_count=risk_dist.medium_count,
            low_risk_count=risk_dist.low_count,
            students_with_backlogs=backlogs_c,
            students_fee_pending=fee_pending_c,
            total_fee_pending_amount=total_fee_pending_amt,
            department_chart=dept_chart_items,
            semester_chart=sem_chart_items,
            academic_year_chart=year_chart_items,
        )

    def get_hod_overview(
        self,
        role: str = "HOD",
        user_dept: Optional[str] = "CSE",
        academic_year: Optional[int] = None,
        semester: Optional[int] = None,
        risk_level: Optional[str] = None,
    ) -> HodOverviewResponse:
        norm_dept = self.normalize_department(user_dept) or "CSE"
        dept_name = self.get_dept_name(norm_dept)

        filtered_df = self.filter_records(
            role="HOD",
            user_dept=norm_dept,
            department=norm_dept,
            academic_year=academic_year,
            semester=semester,
            risk_level=risk_level,
        )

        avail_years = self.get_available_years(role="HOD", user_dept=norm_dept)
        avail_sems = self.get_available_semesters(role="HOD", user_dept=norm_dept, academic_year=academic_year)

        total_students = len(filtered_df)
        if total_students == 0:
            return HodOverviewResponse(
                user_role=role,
                department_id=norm_dept,
                department_name=dept_name,
                academic_year_filter=academic_year,
                semester_filter=semester,
                risk_level_filter=risk_level,
                total_students=0,
                avg_gpa=0.0,
                avg_attendance=0.0,
                risk_distribution=RiskDistribution(high_count=0, medium_count=0, low_count=0, high_pct=0.0, medium_pct=0.0, low_pct=0.0),
                high_risk_count=0,
                medium_risk_count=0,
                low_risk_count=0,
                students_at_risk=0,
                students_with_backlogs=0,
                students_fee_pending=0,
                total_fee_pending_amount=0.0,
                available_years=avail_years,
                available_semesters=avail_sems,
                semester_breakdown=[],
                academic_year_breakdown=[],
            )

        avg_gpa = round(float(filtered_df["cumulative_gpa"].mean()), 2)
        avg_att = round(float(filtered_df["attendance_percentage"].mean()), 1)
        risk_dist = self.compute_risk_distribution(filtered_df)

        students_at_risk = risk_dist.high_count + risk_dist.medium_count
        backlogs_c = int((filtered_df["backlog_count"] > 0).sum())
        fee_pending_c = int((filtered_df["fee_pending_amount"] > 0).sum())
        total_fee_pending_amt = round(float(filtered_df["fee_pending_amount"].sum()), 2)

        sem_breakdown = []
        for sem_num, group in filtered_df.groupby("semester"):
            g_dist = self.compute_risk_distribution(group)
            sem_breakdown.append(
                SemesterAnalyticsItem(
                    semester=int(sem_num),
                    total_students=len(group),
                    avg_gpa=round(float(group["cumulative_gpa"].mean()), 2),
                    avg_attendance=round(float(group["attendance_percentage"].mean()), 1),
                    high_risk_count=g_dist.high_count,
                    medium_risk_count=g_dist.medium_count,
                    low_risk_count=g_dist.low_count,
                )
            )
        sem_breakdown.sort(key=lambda x: x.semester)

        yr_breakdown = []
        for yr_num, group in filtered_df.groupby("academic_year"):
            g_dist = self.compute_risk_distribution(group)
            yr_breakdown.append(
                AcademicYearAnalyticsItem(
                    academic_year=int(yr_num),
                    total_students=len(group),
                    avg_gpa=round(float(group["cumulative_gpa"].mean()), 2),
                    avg_attendance=round(float(group["attendance_percentage"].mean()), 1),
                    high_risk_count=g_dist.high_count,
                )
            )
        yr_breakdown.sort(key=lambda x: x.academic_year)

        return HodOverviewResponse(
            user_role=role,
            department_id=norm_dept,
            department_name=dept_name,
            academic_year_filter=academic_year,
            semester_filter=semester,
            risk_level_filter=risk_level,
            total_students=total_students,
            avg_gpa=avg_gpa,
            avg_attendance=avg_att,
            risk_distribution=risk_dist,
            high_risk_count=risk_dist.high_count,
            medium_risk_count=risk_dist.medium_count,
            low_risk_count=risk_dist.low_count,
            students_at_risk=students_at_risk,
            students_with_backlogs=backlogs_c,
            students_fee_pending=fee_pending_c,
            total_fee_pending_amount=total_fee_pending_amt,
            available_years=avail_years,
            available_semesters=avail_sems,
            semester_breakdown=sem_breakdown,
            academic_year_breakdown=yr_breakdown,
        )

    def get_filtered_students(
        self,
        role: str = "ADMINISTRATOR",
        user_dept: Optional[str] = None,
        department: Optional[str] = None,
        academic_year: Optional[int] = None,
        semester: Optional[int] = None,
        risk_level: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedDetailedStudentListResponse:
        filtered_df = self.filter_records(
            role=role,
            user_dept=user_dept,
            department=department,
            academic_year=academic_year,
            semester=semester,
            risk_level=risk_level,
            search=search,
        )

        total_students = len(filtered_df)
        if total_students == 0:
            return PaginatedDetailedStudentListResponse(
                total_students=0,
                page=1,
                page_size=page_size,
                total_pages=1,
                students=[],
            )

        total_pages = max(1, math.ceil(total_students / page_size))
        page = max(1, min(page, total_pages))
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        page_df = filtered_df.iloc[start_idx:end_idx]

        students = []
        for _, row in page_df.iterrows():
            dept_id = str(row["department_id"])
            fee_amt = float(row.get("fee_pending_amount", 0.0))
            fee_status = str(row.get("fee_payment_status", "Paid"))

            students.append(
                StudentDetailedListItem(
                    student_id=str(row["student_id"]),
                    program=str(row.get("program", "")) if pd.notna(row.get("program")) else "N/A",
                    department_id=dept_id,
                    department_name=self.get_dept_name(dept_id),
                    semester=int(row["semester"]),
                    academic_year=int(row["academic_year"]),
                    gpa=float(round(row["cumulative_gpa"], 2)),
                    attendance_percentage=float(round(row["attendance_percentage"], 1)),
                    backlog_count=int(row["backlog_count"]),
                    fee_pending_amount=float(round(fee_amt, 2)),
                    fee_payment_status=fee_status,
                    risk_level=str(row["risk_level"]),
                    dropout_probability=float(round(row["dropout_probability"], 4)),
                )
            )

        return PaginatedDetailedStudentListResponse(
            total_students=total_students,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            students=students,
        )

    def get_student_records(self, student_id: str) -> pd.DataFrame:
        if student_id not in self.student_groups:
            raise HTTPException(
                status_code=404,
                detail=f"Student '{student_id}' not found in dataset."
            )
        return self.student_groups[student_id]

    def get_student_risk(self, student_id: str) -> StudentRiskResponse:
        student_records = self.get_student_records(student_id)
        latest_record = student_records.iloc[[-1]].copy()
        semester_num = int(latest_record["semester"].values[0])

        X_record = latest_record.drop(
            columns=[
                "future_dropout",
                "student_id",
                "dropout_probability",
                "risk_level",
                "state",
            ],
            errors="ignore",
        )

        # Predict probabilities
        prob = float(self.pipeline.predict_proba(X_record)[0, 1])
        retention_prob = float(1.0 - prob)
        risk_level = self.get_risk_level(prob)

        # Feature level contributions
        preprocessor = self.pipeline.named_steps["preprocessor"]
        classifier = self.pipeline.named_steps["classifier"]

        X_trans = preprocessor.transform(X_record)
        feature_names = preprocessor.get_feature_names_out()
        coefs = classifier.coef_[0]

        contributions = coefs * X_trans[0]

        known_cats = [
            "fee_payment_status", "internship_status", "department_id", "program",
            "specialization", "admission_type", "gender", "scholarship_type",
            "family_income_band"
        ]

        factors = []
        for name, val_trans, contrib in zip(feature_names, X_trans[0], contributions):
            if abs(contrib) < 1e-6:
                continue

            if name.startswith("num__"):
                raw_feature = name.replace("num__", "")
                student_val = latest_record[raw_feature].values[0] if raw_feature in latest_record.columns else val_trans
                if isinstance(student_val, (float, np.floating)):
                    display_val = float(round(student_val, 2))
                elif isinstance(student_val, (int, np.integer)):
                    display_val = int(student_val)
                else:
                    display_val = str(student_val)

                factors.append(
                    FeatureFactor(
                        feature=raw_feature,
                        value=display_val,
                        contribution=round(float(contrib), 4),
                        direction="increases_risk" if contrib > 0 else "reduces_risk"
                    )
                )

            elif name.startswith("cat__"):
                matched_cat = None
                for cat in known_cats:
                    prefix = f"cat__{cat}_"
                    if name.startswith(prefix):
                        matched_cat = cat
                        cat_val = name[len(prefix):]
                        break

                if matched_cat and val_trans > 0:
                    factors.append(
                        FeatureFactor(
                            feature=matched_cat,
                            value=cat_val,
                            contribution=round(float(contrib), 4),
                            direction="increases_risk" if contrib > 0 else "reduces_risk"
                        )
                    )

        risk_factors = sorted(
            [f for f in factors if f.direction == "increases_risk"],
            key=lambda x: x.contribution,
            reverse=True
        )[:5]

        protective_factors = sorted(
            [f for f in factors if f.direction == "reduces_risk"],
            key=lambda x: x.contribution
        )[:5]

        return StudentRiskResponse(
            student_id=student_id,
            semester=semester_num,
            dropout_probability=round(prob, 4),
            retention_probability=round(retention_prob, 4),
            risk_level=risk_level,
            risk_factors=risk_factors,
            protective_factors=protective_factors,
        )

    def get_student_profile(self, student_id: str) -> StudentProfileResponse:
        student_records = self.get_student_records(student_id)
        latest_record = student_records.iloc[-1]
        dept_id = str(latest_record.get("department_id", "")) if pd.notna(latest_record.get("department_id")) else None

        return StudentProfileResponse(
            student_id=student_id,
            program=str(latest_record.get("program", "")) if pd.notna(latest_record.get("program")) else None,
            specialization=str(latest_record.get("specialization", "")) if pd.notna(latest_record.get("specialization")) else None,
            department_id=dept_id,
            department_name=self.get_dept_name(dept_id),
            semester=int(latest_record["semester"]),
            academic_year=int(latest_record["academic_year"]),
            gender=str(latest_record.get("gender", "")) if pd.notna(latest_record.get("gender")) else None,
            admission_year=int(latest_record["admission_year"]),
            hostel_status=int(latest_record["hostel_status"]),
            scholarship_status=int(latest_record["scholarship_status"]),
        )

    def get_student_history(self, student_id: str) -> StudentHistoryResponse:
        student_records = self.get_student_records(student_id)
        history_items = []

        for _, row in student_records.iterrows():
            history_items.append(
                SemesterHistoryItem(
                    semester=int(row["semester"]),
                    academic_year=int(row["academic_year"]),
                    attendance_percentage=float(round(row["attendance_percentage"], 2)),
                    semester_gpa=float(round(row["semester_gpa"], 2)),
                    cumulative_gpa=float(round(row["cumulative_gpa"], 2)),
                    backlog_count=int(row["backlog_count"]),
                    courses_failed=int(row["courses_failed"]),
                    courses_passed=int(row["courses_passed"]),
                    internal_marks_percentage=float(round(row["internal_marks_percentage"], 2)),
                    assignments_completed_pct=float(round(row["assignments_completed_pct"], 2)),
                    fee_pending_amount=float(round(row["fee_pending_amount"], 2)),
                    historical_dropout_label=int(row["future_dropout"]),
                )
            )

        return StudentHistoryResponse(
            student_id=student_id,
            history=history_items,
        )

    def get_paginated_students(self, page: int = 1, page_size: int = 20) -> PaginatedStudentListResponse:
        total_students = len(self.unique_student_ids)
        total_pages = max(1, math.ceil(total_students / page_size))

        page = max(1, min(page, total_pages))
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        page_student_ids = self.unique_student_ids[start_idx:end_idx]

        summaries = []
        for sid in page_student_ids:
            records = self.student_groups[sid]
            latest = records.iloc[-1]
            summaries.append(
                StudentSummaryItem(
                    student_id=sid,
                    program=str(latest.get("program", "")) if pd.notna(latest.get("program")) else None,
                    department_id=str(latest.get("department_id", "")) if pd.notna(latest.get("department_id")) else None,
                    latest_semester=int(latest["semester"]),
                    latest_academic_year=int(latest["academic_year"]),
                )
            )

        return PaginatedStudentListResponse(
            total_students=total_students,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            students=summaries,
        )

    def clean_feature_label(self, raw: str) -> str:
        name = raw
        if name.startswith("num__"):
            name = name.replace("num__", "")
        elif name.startswith("cat__"):
            name = name.replace("cat__", "")
        parts = name.split("_")
        readable = " ".join(parts).title()
        readable = (
            readable.replace("Gpa", "GPA")
            .replace("Pct", "%")
            .replace("Id", "ID")
            .replace("Status", "Status")
        )
        return readable

    def get_model_insights(self) -> StudentModelInsightsResponse:
        preprocessor = self.pipeline.named_steps["preprocessor"]
        classifier = self.pipeline.named_steps["classifier"]

        feature_names = preprocessor.get_feature_names_out()
        coefs = classifier.coef_[0]

        risk_factors = []
        protective_factors = []

        for feat, coef in zip(feature_names, coefs):
            if abs(coef) < 0.05:
                continue
            disp_name = self.clean_feature_label(feat)
            item = ModelFeatureInsight(
                raw_feature=feat,
                feature_name=disp_name,
                coefficient=round(float(coef), 4),
                direction="increases_risk" if coef > 0 else "reduces_risk",
            )
            if coef > 0:
                risk_factors.append(item)
            else:
                protective_factors.append(item)

        risk_factors = sorted(risk_factors, key=lambda x: x.coefficient, reverse=True)[:8]
        protective_factors = sorted(protective_factors, key=lambda x: x.coefficient)[:8]

        accuracy = 0.7509
        roc_auc = 0.8204
        pr_auc = 0.3273
        precision = 0.2467
        recall = 0.6344
        f1 = 0.3552
        high_thresh = 0.60
        med_thresh = 0.40

        results_csv = self.project_root / "models" / "student_model_results.csv"
        if results_csv.exists():
            try:
                res_df = pd.read_csv(results_csv)
                log_reg = res_df[res_df["Model"].str.contains("Logistic", case=False, na=False)]
                if not log_reg.empty:
                    accuracy = round(float(log_reg["Accuracy"].values[0]), 4)
                    roc_auc = round(float(log_reg["ROC_AUC"].values[0]), 4)
                    pr_auc = round(float(log_reg["PR_AUC"].values[0]), 4)
            except Exception:
                pass

        config_json = self.project_root / "models" / "risk_threshold_config.json"
        if config_json.exists():
            try:
                with open(config_json) as f:
                    cfg = json.load(f)
                    high_thresh = float(cfg.get("high_min", 0.60))
                    med_thresh = float(cfg.get("low_max", 0.40))
                    high_m = cfg.get("metrics", {}).get("high_threshold", {})
                    if high_m:
                        precision = round(float(high_m.get("precision", precision)), 4)
                        recall = round(float(high_m.get("recall", recall)), 4)
                        f1 = round(float(high_m.get("f1", f1)), 4)
            except Exception:
                pass

        return StudentModelInsightsResponse(
            model_name="Logistic Regression",
            accuracy=accuracy,
            roc_auc=roc_auc,
            pr_auc=pr_auc,
            precision=precision,
            recall=recall,
            f1_score=f1,
            high_risk_threshold=high_thresh,
            medium_risk_threshold=med_thresh,
            explanation="Student Success risk is estimated using a Logistic Regression model based on student academic, financial, and institutional features.",
            threshold_reasoning="LOW (< 0.40) filters out safe students. MEDIUM (0.40 to 0.59) triggers light advising. HIGH (>= 0.60) captures urgent high-probability dropouts.",
            risk_factors=risk_factors,
            protective_factors=protective_factors,
        )


# Singleton instance
student_service = StudentService()
