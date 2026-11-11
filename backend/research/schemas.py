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
