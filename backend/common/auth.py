import base64
import json
from typing import Optional, Tuple
from fastapi import Header, HTTPException, Query, status


class UserContext:
    DEPT_CODES = {"CSE", "ECE", "EEE", "AIML", "ME", "BBA", "BT", "CHEM", "MATH", "PHY"}

    def __init__(
        self,
        role: Optional[str] = None,
        department_id: Optional[str] = None,
        email: Optional[str] = None,
    ):
        clean_role = str(role).strip().upper() if isinstance(role, str) and role else "ADMINISTRATOR"
        self.role = clean_role
        self.email = str(email).strip().lower() if isinstance(email, str) and email else ""

        # Derive department_id if missing for HOD
        raw_dept = str(department_id).strip().upper() if isinstance(department_id, str) and department_id else ""
        if not raw_dept and self.email:
            for code in self.DEPT_CODES:
                if code.lower() in self.email:
                    raw_dept = code
                    break

        if self.role == "HOD" and not raw_dept:
            raw_dept = "CSE"  # Safe default for HOD if unspecified

        self.department_id = raw_dept if raw_dept != "ALL" and raw_dept != "" else None

    @property
    def is_admin(self) -> bool:
        return self.role in ("ADMINISTRATOR", "ADMIN")

    @property
    def is_hod(self) -> bool:
        return self.role == "HOD"

    def enforce_department(self, requested_dept: Optional[str] = None) -> Optional[str]:
        """
        CRITICAL AUTHORIZATION ENFORCEMENT:
        If user is HOD, ALWAYS return user's assigned department_id.
        DISREGARD any requested_dept passed by frontend for HOD users.
        If user is Administrator, respect requested_dept if provided (and not ALL), else None.
        """
        if self.is_hod:
            if not self.department_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: HOD user is not assigned to a valid department.",
                )
            # MANDATORY SECURITY OVERRIDE FOR HOD
            return self.department_id.upper()

        # Administrator access
        if requested_dept and isinstance(requested_dept, str) and requested_dept.strip().upper() not in ["ALL", "NONE", ""]:
            return requested_dept.strip().upper()
        return None


def parse_jwt_claims(auth_header: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Parse role, department_id, and email from Bearer JWT token payload if present."""
    if not isinstance(auth_header, str) or not auth_header.startswith("Bearer "):
        return None, None, None

    token = auth_header[7:].strip()
    try:
        parts = token.split(".")
        if len(parts) == 3:
            payload_b64 = parts[1]
            payload_b64 += "=" * (-len(payload_b64) % 4)
            payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8"))

            user_meta = payload.get("user_metadata", {})
            role = user_meta.get("role") or payload.get("role")
            dept = user_meta.get("department_id") or user_meta.get("department")
            email = payload.get("email") or user_meta.get("email")
            return role, dept, email
    except Exception:
        pass
    return None, None, None


def get_user_context(
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    x_user_email: Optional[str] = Header(None, alias="X-User-Email"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
) -> UserContext:
    # Safely extract string arguments if FastAPI Query/Header default objects passed
    clean_role_hdr = x_user_role if isinstance(x_user_role, str) else None
    clean_dept_hdr = x_user_department if isinstance(x_user_department, str) else None
    clean_email_hdr = x_user_email if isinstance(x_user_email, str) else None
    clean_auth_hdr = authorization if isinstance(authorization, str) else None
    clean_role_qry = role if isinstance(role, str) else None
    clean_dept_qry = user_department if isinstance(user_department, str) else None

    # 1. Parse JWT token if available
    jwt_role, jwt_dept, jwt_email = parse_jwt_claims(clean_auth_hdr)

    # 2. Determine effective role, department, and email
    eff_role = clean_role_qry or clean_role_hdr or jwt_role or "ADMINISTRATOR"
    eff_dept = clean_dept_qry or clean_dept_hdr or jwt_dept
    eff_email = clean_email_hdr or jwt_email

    return UserContext(role=eff_role, department_id=eff_dept, email=eff_email)
