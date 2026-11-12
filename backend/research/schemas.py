from typing import List, Optional

from pydantic import BaseModel, Field


class ResearchStatusResponse(BaseModel):
    module: str = Field("research", example="research")
    status: str = Field("ready", example="ready")


class ResearchOverviewResponse(BaseModel):
    total_students: int
    research_participants: int
    research_participation_rate: float
    total_publications: int
    average_publications: float
    students_with_publications: int
    average_faculty_rating: Optional[float] = None
    average_mentorship_score: Optional[float] = None
    average_infrastructure_rating: Optional[float] = None


class DepartmentResearch(BaseModel):
    department: str
    total_students: int
    research_participants: int
    participation_rate: float
    total_publications: int
    average_publications: float
    average_faculty_rating: Optional[float] = None
    average_mentorship_score: Optional[float] = None
    average_infrastructure_rating: Optional[float] = None


class ResearchDepartmentResponse(BaseModel):
    departments: List[DepartmentResearch]


class ProgramResearch(BaseModel):
    program: str
    total_students: int
    research_participants: int
    participation_rate: float
    total_publications: int
    average_publications: float


class ResearchProgramResponse(BaseModel):
    programs: List[ProgramResearch]


class PublicationDistribution(BaseModel):
    bucket: str
    count: int


class ResearchPublicationResponse(BaseModel):
    distribution: List[PublicationDistribution]


class ResearchParticipationDistribution(BaseModel):
    category: str
    count: int


class ResearchParticipationResponse(BaseModel):
    distribution: List[ResearchParticipationDistribution]


class ResearchFilterOptionsResponse(BaseModel):
    departments: List[str]
    programs: List[str]
    admission_years: List[int]


class FacultyResearchDepartment(BaseModel):
    department: str
    total_faculty: int
    faculty_researchers: int
    publications: int
    average_publications_per_faculty: float = 0.0
    participation_rate: float
    total_citations: int
    research_grants: float
    average_faculty_rating: Optional[float] = None
    faculty_rating_count: int
    average_mentorship_score: Optional[float] = None
    mentorship_score_count: int


class FacultyPublicationTrend(BaseModel):
    academic_year: str
    publications: int
    citations: int


class FacultyDepartmentPublicationTrend(BaseModel):
    department: str
    academic_year: str
    publications: int


class FacultyResearcher(BaseModel):
    faculty_id: str
    faculty_name: str
    department: str
    publications: int
    citations: int


class FacultyResearchOverview(BaseModel):
    selected_department: Optional[str] = None
    selected_academic_year: Optional[str] = None
    total_faculty: int
    faculty_researchers: int
    publishing_faculty_count: int
    total_publications: int
    average_publications_per_faculty: float
    faculty_participation_rate: float
    total_citations: int
    average_citations_per_faculty: float
    average_citations_per_publishing_faculty: Optional[float] = None
    total_research_grants: float
    average_faculty_rating: Optional[float] = None
    faculty_rating_count: int
    average_mentorship_score: Optional[float] = None
    mentorship_score_count: int
    is_synthetic: bool = True


class FacultyResearchAnalyticsResponse(BaseModel):
    overview: FacultyResearchOverview
    departments: List[FacultyResearchDepartment]
    publication_trends: List[FacultyPublicationTrend]
    department_publication_trends: List[FacultyDepartmentPublicationTrend] = Field(default_factory=list)
    top_researchers: List[FacultyResearcher]
    available_departments: List[str]
    academic_years: List[str]
    is_synthetic: bool = True
