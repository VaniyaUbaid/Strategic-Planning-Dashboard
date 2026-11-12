import base64
import json
import logging
import time
from typing import Optional

import httpx
from fastapi import Header, HTTPException, status
from supabase_auth.errors import AuthApiError

from backend.common.supabase_client import (
    SupabaseConfigurationError,
    get_supabase_client,
    get_supabase_config,
)

logger = logging.getLogger(__name__)


class UserContext:
    def __init__(
        self,
        user_id: str,
        role: str,
        department_id: Optional[str] = None,
        email: Optional[str] = None,
        access_token: Optional[str] = None,
    ):
        self.user_id = user_id
        self.role = role
        self.department_id = department_id.upper() if department_id else None
        self.email = email
        self.access_token = access_token

    @property
    def is_admin(self) -> bool:
        return self.role == "ADMINISTRATOR"

    @property
    def is_hod(self) -> bool:
        return self.role == "HOD"

    def require_admin(self) -> None:
        if not self.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator access is required.",
            )

    def require_hod(self) -> None:
        if not self.is_hod:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="HOD access is required.",
            )

    def enforce_department(self, requested_dept: Optional[str] = None) -> Optional[str]:
        if self.is_hod:
            if not self.department_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Your account is not assigned to a department.",
                )
            return self.department_id

        if requested_dept and requested_dept.strip().upper() not in {"ALL", "NONE"}:
            return requested_dept.strip().upper()
        return None


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="A valid Supabase access token is required.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _verified_jwt_claims(token: str, user_id: str) -> dict:
    parts = token.split(".")
    if len(parts) != 3:
        raise _unauthorized()
    try:
        payload_segment = parts[1] + "=" * (-len(parts[1]) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload_segment).decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        raise _unauthorized() from None
    if not isinstance(claims, dict):
        raise _unauthorized()

    url, _ = get_supabase_config()
    expected_issuer = f"{url.rstrip('/')}/auth/v1" if url else None
    audience = claims.get("aud")
    audiences = audience if isinstance(audience, list) else [audience]
    expires_at = claims.get("exp")
    not_before = claims.get("nbf")
    now = time.time()
    if (
        not expected_issuer
        or claims.get("iss") != expected_issuer
        or claims.get("sub") != user_id
        or "authenticated" not in audiences
        or not isinstance(expires_at, (int, float))
        or expires_at <= now
        or (not_before is not None and (not isinstance(not_before, (int, float)) or not_before > now))
    ):
        raise _unauthorized()
    return claims


def get_user_context(
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> UserContext:
    """Verify a Supabase access token and authorize only trusted app_metadata roles."""
    if not isinstance(authorization, str):
        raise _unauthorized()

    scheme, separator, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not separator or not token.strip():
        raise _unauthorized()

    try:
        response = get_supabase_client().auth.get_user(token.strip())
    except AuthApiError:
        raise _unauthorized() from None
    except httpx.RequestError as exc:
        logger.error("Supabase token verification unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is temporarily unavailable.",
        ) from None
    except SupabaseConfigurationError:
        logger.error("Supabase token verification is not configured.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is not configured.",
        ) from None
    except Exception as exc:
        logger.error("Supabase token verification failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service could not verify the access token.",
        ) from None

    user = getattr(response, "user", None)
    if user is None:
        raise _unauthorized()

    claims = _verified_jwt_claims(token.strip(), getattr(user, "id", ""))
    app_metadata = claims.get("app_metadata") or {}
    if not isinstance(app_metadata, dict):
        app_metadata = {}

    role_value = app_metadata.get("role")
    role = role_value.strip().upper() if isinstance(role_value, str) else ""
    if role not in {"ADMINISTRATOR", "HOD"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account does not have an authorized application role.",
        )

    department_value = app_metadata.get("department_id")
    department = (
        department_value.strip().upper()
        if isinstance(department_value, str) and department_value.strip()
        else None
    )
    if role == "HOD" and not department:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your HOD account is not assigned to a department.",
        )
    if role == "ADMINISTRATOR":
        department = None

    user_id = getattr(user, "id", None)
    if not isinstance(user_id, str) or not user_id:
        raise _unauthorized()

    return UserContext(
        user_id=user_id,
        role=role,
        department_id=department,
        email=getattr(user, "email", None),
        access_token=token.strip(),
    )
