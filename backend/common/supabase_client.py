import os
import logging
import re
from pathlib import Path
from typing import Optional

from supabase import create_client, Client
from supabase.lib.client_options import SyncClientOptions

logger = logging.getLogger(__name__)

_supabase_client: Optional[Client] = None
_supabase_client_config: Optional[tuple[str, str]] = None

_TOKEN_PATTERN = re.compile(r"\b[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")
_API_KEY_PATTERN = re.compile(r"\bsb_(?:secret|publishable)_[A-Za-z0-9_-]+\b")
_BEARER_PATTERN = re.compile(r"(?i)\bBearer\s+\S+")


def _sanitize_supabase_error(message: object, key: Optional[str] = None) -> str:
    sanitized = str(message or "No error message provided.")
    if key:
        sanitized = sanitized.replace(key, "[REDACTED]")
    sanitized = _BEARER_PATTERN.sub("Bearer [REDACTED]", sanitized)
    sanitized = _TOKEN_PATTERN.sub("[REDACTED_TOKEN]", sanitized)
    sanitized = _API_KEY_PATTERN.sub("[REDACTED_API_KEY]", sanitized)
    return " ".join(sanitized.split())[:400]


class SupabaseConfigurationError(RuntimeError):
    """Raised when the backend cannot initialize a configured Supabase client."""


def get_supabase_config() -> tuple[Optional[str], Optional[str]]:
    url = os.getenv("SUPABASE_URL")
    key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
    )

    project_root = Path(__file__).resolve().parents[2]
    env_paths = (project_root / "backend" / ".env", project_root / ".env")
    file_values = {}
    for env_path in env_paths:
        if not env_path.is_file() or (url and key):
            continue
        try:
            with env_path.open("r", encoding="utf-8") as env_file:
                for line in env_file:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue

                    name, value = line.split("=", 1)
                    name = name.strip()
                    value = value.strip().strip("'\"")
                    if not value:
                        continue

                    if name in (
                        "SUPABASE_URL",
                        "SUPABASE_SERVICE_ROLE_KEY",
                        "SUPABASE_KEY",
                        "SUPABASE_ANON_KEY",
                    ):
                        file_values.setdefault(name, value)
        except OSError as exc:
            logger.warning(
                "Could not read Supabase environment file (file=%s, error_type=%s)",
                env_path.name,
                type(exc).__name__,
            )

    url = url or file_values.get("SUPABASE_URL")
    key = (
        key
        or file_values.get("SUPABASE_SERVICE_ROLE_KEY")
        or file_values.get("SUPABASE_KEY")
        or file_values.get("SUPABASE_ANON_KEY")
    )
    return url, key


def get_supabase_service_role_key() -> Optional[str]:
    """Return the backend-only service key without falling back to public keys."""
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if service_key:
        return service_key

    env_path = Path(__file__).resolve().parents[2] / "backend" / ".env"
    if not env_path.is_file():
        return None

    try:
        with env_path.open("r", encoding="utf-8") as env_file:
            for line in env_file:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name, value = line.split("=", 1)
                if name.strip() == "SUPABASE_SERVICE_ROLE_KEY":
                    return value.strip().strip("'\"") or None
    except OSError as exc:
        logger.warning(
            "Could not read backend Supabase service key configuration (error_type=%s)",
            type(exc).__name__,
        )
    return None


def get_supabase_client() -> Client:
    global _supabase_client, _supabase_client_config
    url, key = get_supabase_config()
    if not url or not key:
        logger.error(
            "Supabase client configuration is incomplete (url_configured=%s, key_configured=%s)",
            bool(url),
            bool(key),
        )
        raise SupabaseConfigurationError(
            "Supabase backend configuration is incomplete. Set SUPABASE_URL and a server-side "
            "SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY in the backend environment or backend/.env."
        )

    config = (url, key)
    if _supabase_client is not None and _supabase_client_config == config:
        return _supabase_client

    try:
        _supabase_client = create_client(url, key)
        _supabase_client_config = config
    except Exception as exc:
        logger.error(
            "Supabase client initialization failed (error_type=%s, message=%s)",
            type(exc).__name__,
            _sanitize_supabase_error(getattr(exc, "message", None) or str(exc), key),
        )
        raise SupabaseConfigurationError(
            "Supabase client initialization failed. Check the backend Supabase URL, server-side key, "
            "and installed SDK configuration."
        ) from None
    return _supabase_client


def get_supabase_client_for_access_token(access_token: Optional[str]) -> Client:
    """Create a request-scoped client so Supabase RLS evaluates the signed-in user."""
    if not isinstance(access_token, str) or not access_token.strip():
        return get_supabase_client()

    url, key = get_supabase_config()
    if not url or not key:
        logger.error(
            "Supabase request client configuration is incomplete (url_configured=%s, key_configured=%s)",
            bool(url),
            bool(key),
        )
        raise SupabaseConfigurationError(
            "Supabase backend configuration is incomplete. Set SUPABASE_URL and a server-side "
            "SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY in the backend environment or backend/.env."
        )

    try:
        return create_client(
            url,
            key,
            options=SyncClientOptions(
                headers={"Authorization": f"Bearer {access_token.strip()}"}
            ),
        )
    except Exception as exc:
        logger.error(
            "Supabase request client initialization failed (error_type=%s, message=%s)",
            type(exc).__name__,
            _sanitize_supabase_error(getattr(exc, "message", None) or str(exc), key),
        )
        raise SupabaseConfigurationError(
            "Supabase request client initialization failed. Check the installed synchronous "
            "Supabase SDK configuration and backend credentials."
        ) from None
