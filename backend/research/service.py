from pathlib import Path
from threading import Lock
from typing import Optional

import pandas as pd

from backend.research.schemas import (
    DepartmentResearch,
    ProgramResearch,
    PublicationDistribution,
    ResearchDepartmentResponse,
    ResearchFilterOptionsResponse,
    ResearchOverviewResponse,
    ResearchParticipationDistribution,
    ResearchParticipationResponse,
    ResearchProgramResponse,
    ResearchPublicationResponse,
    ResearchStatusResponse,
)


class ResearchDataError(Exception):
    """Raised when the Research dataset cannot be loaded or validated."""


class ResearchService:
    REQUIRED_COLUMNS = {
        "Department",
        "Program",
        "Research_Participation",
        "Publications",
        "Faculty_Rating",
        "Mentorship_Score",
        "Infrastructure_Rating",
        "Admission_Year",
    }
    POSITIVE_PARTICIPATION = {
        "1", "true", "yes", "y", "participant", "participating", "active",
    }
    NEGATIVE_PARTICIPATION = {
        "0", "false", "no", "n", "non-participant", "nonparticipant",
        "not participating", "inactive",
    }

    def __init__(self, data_path: Optional[Path] = None):
        self.project_root = Path(__file__).resolve().parents[2]
        self.data_path = Path(data_path) if data_path else None
        self._dataframe = None
        self._load_lock = Lock()

    def _resolve_data_path(self) -> Path:
        if self.data_path is not None:
            return self.data_path

        candidates = (
            self.project_root / "data" / "research" / "preprocessed_strategic_planning.csv",
            # Keep compatibility with the dataset's current repository location.
            self.project_root / "data" / "student" / "research" / "preprocessed_strategic_planning.csv",
        )
        return next((path for path in candidates if path.is_file()), candidates[0])

    def _get_dataframe(self) -> pd.DataFrame:
        if self._dataframe is not None:
            return self._dataframe

        with self._load_lock:
            if self._dataframe is not None:
                return self._dataframe

            path = self._resolve_data_path()
            if not path.is_file():
                raise ResearchDataError("Research dataset is not available.")
            try:
                dataframe = pd.read_csv(path)
            except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
                raise ResearchDataError("Research dataset could not be read.") from exc

            missing_columns = self.REQUIRED_COLUMNS.difference(dataframe.columns)
            if missing_columns:
                missing = ", ".join(sorted(missing_columns))
                raise ResearchDataError(f"Research dataset is missing required columns: {missing}.")

            dataframe = dataframe.copy()
            for column in (
                "Publications", "Faculty_Rating", "Mentorship_Score",
                "Infrastructure_Rating", "Admission_Year",
            ):
                dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")
            dataframe["_participation"] = dataframe["Research_Participation"].map(
                self._normalize_participation
            )
            self._dataframe = dataframe
            return dataframe

    @classmethod
    def _normalize_participation(cls, value) -> str:
        if pd.isna(value) or not str(value).strip():
            return "Unknown"
        clean = " ".join(str(value).strip().lower().replace("_", " ").split())
        if clean in cls.POSITIVE_PARTICIPATION:
            return "Participating"
        if clean in cls.NEGATIVE_PARTICIPATION:
            return "Not participating"
        # Preserve unrecognized source categories rather than forcing them into yes/no.
        return str(value).strip()

    def _filtered_dataframe(
        self,
        department: Optional[str] = None,
        program: Optional[str] = None,
        admission_year: Optional[int] = None,
    ) -> pd.DataFrame:
        filtered = self._get_dataframe()
        if department and department.strip():
            filtered = filtered[filtered["Department"].astype(str).str.casefold() == department.strip().casefold()]
        if program and program.strip():
            filtered = filtered[filtered["Program"].astype(str).str.casefold() == program.strip().casefold()]
        if admission_year is not None:
            filtered = filtered[filtered["Admission_Year"] == admission_year]
        return filtered

    @staticmethod
    def _mean(dataframe: pd.DataFrame, column: str) -> Optional[float]:
        values = dataframe[column].dropna()
        if values.empty:
            return None
        return round(float(values.mean()), 2)

    @classmethod
    def _metrics(cls, dataframe: pd.DataFrame) -> dict:
        total_students = len(dataframe)
        publications = dataframe["Publications"].dropna()
        participants = int((dataframe["_participation"] == "Participating").sum())
        return {
            "total_students": total_students,
            "research_participants": participants,
            "research_participation_rate": round(participants / total_students * 100, 2) if total_students else 0.0,
            "total_publications": int(publications.sum()),
            "average_publications": round(float(publications.mean()), 2) if not publications.empty else 0.0,
            "students_with_publications": int((publications > 0).sum()),
            "average_faculty_rating": cls._mean(dataframe, "Faculty_Rating"),
            "average_mentorship_score": cls._mean(dataframe, "Mentorship_Score"),
            "average_infrastructure_rating": cls._mean(dataframe, "Infrastructure_Rating"),
        }

    def get_status(self) -> ResearchStatusResponse:
        """Report whether a valid local Research dataset is available."""
        try:
            self._get_dataframe()
        except ResearchDataError:
            return ResearchStatusResponse(module="research", status="not_ready")
        return ResearchStatusResponse(module="research", status="ready")

    def get_overview(self, department=None, program=None, admission_year=None) -> ResearchOverviewResponse:
        return ResearchOverviewResponse(**self._metrics(self._filtered_dataframe(department, program, admission_year)))

    def get_departments(self, department=None, program=None, admission_year=None) -> ResearchDepartmentResponse:
        dataframe = self._filtered_dataframe(department, program, admission_year)
        rows = []
        for name, group in dataframe.groupby("Department", dropna=True, sort=True):
            metrics = self._metrics(group)
            rows.append(DepartmentResearch(
                department=str(name),
                total_students=metrics["total_students"],
                research_participants=metrics["research_participants"],
                participation_rate=metrics["research_participation_rate"],
                total_publications=metrics["total_publications"],
                average_publications=metrics["average_publications"],
                average_faculty_rating=metrics["average_faculty_rating"],
                average_mentorship_score=metrics["average_mentorship_score"],
                average_infrastructure_rating=metrics["average_infrastructure_rating"],
            ))
        return ResearchDepartmentResponse(departments=rows)

    def get_programs(self, department=None, program=None, admission_year=None) -> ResearchProgramResponse:
        dataframe = self._filtered_dataframe(department, program, admission_year)
        rows = []
        for name, group in dataframe.groupby("Program", dropna=True, sort=True):
            metrics = self._metrics(group)
            rows.append(ProgramResearch(
                program=str(name),
                total_students=metrics["total_students"],
                research_participants=metrics["research_participants"],
                participation_rate=metrics["research_participation_rate"],
                total_publications=metrics["total_publications"],
                average_publications=metrics["average_publications"],
            ))
        return ResearchProgramResponse(programs=rows)

    def get_publications(self, department=None, program=None, admission_year=None) -> ResearchPublicationResponse:
        dataframe = self._filtered_dataframe(department, program, admission_year)
        values = dataframe["Publications"].dropna()
        if values.empty:
            return ResearchPublicationResponse(distribution=[])

        maximum = int(values.max())
        if maximum <= 5:
            buckets = [(value, f"{value} publication{'s' if value != 1 else ''}") for value in range(maximum + 1)]
        else:
            buckets = [(value, f"{value} publication{'s' if value != 1 else ''}") for value in range(5)]
            buckets.append((5, "5+ publications"))

        distribution = []
        for lower_bound, label in buckets:
            if label == "5+ publications":
                count = int((values >= lower_bound).sum())
            else:
                count = int((values == lower_bound).sum())
            distribution.append(PublicationDistribution(bucket=label, count=count))
        if dataframe["Publications"].isna().any():
            distribution.append(PublicationDistribution(bucket="Missing", count=int(dataframe["Publications"].isna().sum())))
        return ResearchPublicationResponse(distribution=distribution)

    def get_participation(self, department=None, program=None, admission_year=None) -> ResearchParticipationResponse:
        dataframe = self._filtered_dataframe(department, program, admission_year)
        counts = dataframe["_participation"].value_counts(dropna=False, sort=False)
        distribution = [
            ResearchParticipationDistribution(category=str(category), count=int(count))
            for category, count in counts.items()
        ]
        return ResearchParticipationResponse(distribution=distribution)

    def get_filter_options(self) -> ResearchFilterOptionsResponse:
        dataframe = self._get_dataframe()
        years = dataframe["Admission_Year"].dropna().astype(int).unique().tolist()
        return ResearchFilterOptionsResponse(
            departments=sorted(dataframe["Department"].dropna().astype(str).unique().tolist()),
            programs=sorted(dataframe["Program"].dropna().astype(str).unique().tolist()),
            admission_years=sorted(years),
        )


research_service = ResearchService()
