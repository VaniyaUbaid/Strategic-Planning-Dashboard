import argparse
import logging
import re
import sys

from supabase import create_client

from backend.common.supabase_client import (
    get_supabase_config,
    get_supabase_service_role_key,
)

DEPARTMENTS = {"CSE", "ECE", "EEE", "AIML", "ME", "BBA", "BT", "CHEM", "MATH", "PHY"}
logger = logging.getLogger("role_assignment")


def _sanitize_error_message(message: object, secret_key: str) -> str:
    sanitized = str(message or "No error message provided.")
    if secret_key:
        sanitized = sanitized.replace(secret_key, "[REDACTED]")
    sanitized = re.sub(
        r"(?i)\bBearer\s+\S+",
        "Bearer [REDACTED]",
        sanitized,
    )
    sanitized = re.sub(
        r"\bsb_(?:secret|publishable)_[A-Za-z0-9_-]+\b",
        "[REDACTED_API_KEY]",
        sanitized,
    )
    sanitized = re.sub(
        r"\b[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b",
        "[REDACTED_TOKEN]",
        sanitized,
    )
    sanitized = re.sub(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        "[REDACTED_EMAIL]",
        sanitized,
        flags=re.IGNORECASE,
    )
    return " ".join(sanitized.split())[:500]


def _report_api_error(operation: str, error: Exception, secret_key: str) -> None:
    status_code = getattr(error, "status", None) or getattr(error, "status_code", None)
    error_code = getattr(error, "code", None)
    message = _sanitize_error_message(
        getattr(error, "message", None) or str(error),
        secret_key,
    )
    logger.error(
        "Supabase Auth Admin request failed (operation=%s, status=%s, code=%s, message=%s)",
        operation,
        status_code if status_code is not None else "unknown",
        error_code if error_code is not None else "unknown",
        message,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Assign a trusted app_metadata role using a backend-only Supabase service key."
    )
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--expected-email", required=True)
    parser.add_argument("--role", required=True, choices=("ADMINISTRATOR", "HOD"))
    parser.add_argument("--department", choices=sorted(DEPARTMENTS))
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verify Auth Admin access and account identity without changing app_metadata.",
    )
    args = parser.parse_args()

    if args.role == "HOD" and not args.department:
        parser.error("--department is required for HOD assignments.")
    if args.role == "ADMINISTRATOR" and args.department:
        parser.error("--department is not valid for Administrator assignments.")

    supabase_url, _ = get_supabase_config()
    service_key = get_supabase_service_role_key()
    if not supabase_url or not service_key:
        print(
            "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in the trusted backend environment "
            "or configure them in the supported backend environment files.",
            file=sys.stderr,
        )
        return 2

    try:
        admin = create_client(supabase_url, service_key).auth.admin
        current_user = admin.get_user_by_id(args.user_id).user
    except Exception as exc:
        _report_api_error("get_user_by_id", exc, service_key)
        print("Role assignment stopped; the account was not modified.", file=sys.stderr)
        return 1

    if (current_user.email or "").casefold() != args.expected_email.casefold():
        print("User ID and expected email do not identify the same account.", file=sys.stderr)
        return 2

    if args.verify_only:
        print("Supabase Auth Admin lookup succeeded and the account identity matched.")
        print("Read-only verification complete; app_metadata was not changed.")
        return 0

    app_metadata = dict(current_user.app_metadata or {})
    app_metadata["role"] = args.role
    if args.role == "HOD":
        app_metadata["department_id"] = args.department
    else:
        app_metadata.pop("department_id", None)

    try:
        admin.update_user_by_id(args.user_id, {"app_metadata": app_metadata})
    except Exception as exc:
        _report_api_error("update_user_by_id", exc, service_key)
        print("Role assignment failed; Supabase did not confirm the update.", file=sys.stderr)
        return 1

    print(f"Assigned {args.role} to the verified account {args.expected_email}.")
    print("The user must sign out and sign in again to receive updated app_metadata claims.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
