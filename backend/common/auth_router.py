from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.common.auth import UserContext, get_user_context

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class AuthenticatedUserResponse(BaseModel):
    user_id: str
    email: Optional[str] = None
    role: str
    department_id: Optional[str] = None


@router.get("/me", response_model=AuthenticatedUserResponse)
def get_authenticated_user(
    user: UserContext = Depends(get_user_context),
) -> AuthenticatedUserResponse:
    return AuthenticatedUserResponse(
        user_id=user.user_id,
        email=user.email,
        role=user.role,
        department_id=user.department_id,
    )
