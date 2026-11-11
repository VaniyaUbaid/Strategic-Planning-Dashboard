from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field("ok", example="ok")


class SystemModulesStatusResponse(BaseModel):
    student: str = Field("ready", example="ready")
    finance: str = Field("not_ready", example="not_ready")
    research: str = Field("not_ready", example="not_ready")
    decision_assistant: str = Field("not_ready", example="not_ready")


class ModuleStatusResponse(BaseModel):
    module: str
    status: str = Field("not_ready", example="not_ready")
