import os
import logging
from pathlib import Path
from typing import Optional

from supabase import create_client, Client

logger = logging.getLogger(__name__)

_supabase_client: Optional[Client] = None


class SupabaseConfigurationError(RuntimeError):
    """Raised when the backend cannot initialize a configured Supabase client."""


def get_supabase_config() -> tuple[Optional[str], Optional[str]]:
    url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
    key = (
        os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
        or os.getenv("VITE_SUPABASE_PUBLISHABLE_KEY")
    )

    project_root = Path(__file__).resolve().parents[2]
    env_paths = (
        project_root / "backend" / ".env",
        project_root / ".env",
        project_root / "frontend" / ".env",
    )
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

                    if not url and name in ("SUPABASE_URL", "VITE_SUPABASE_URL"):
                        url = value
                    if not key and name in (
                        "SUPABASE_KEY",
                        "SUPABASE_SERVICE_ROLE_KEY",
                        "SUPABASE_ANON_KEY",
                        "VITE_SUPABASE_PUBLISHABLE_KEY",
                    ):
                        key = value
        except OSError as exc:
            logger.warning(
                "Could not read Supabase environment file (file=%s, error_type=%s)",
                env_path.name,
                type(exc).__name__,
            )

    return url, key


def get_supabase_client() -> Client:
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    url, key = get_supabase_config()
    if not url or not key:
        raise SupabaseConfigurationError(
            "Supabase configuration is incomplete. Set SUPABASE_URL and SUPABASE_KEY "
            "in the backend environment or backend/.env. If RLS permits public reads, "
            "the existing publishable key can be used as a fallback."
        )

    try:
        _supabase_client = create_client(url, key)
    except Exception as exc:
        logger.error(
            "Supabase client initialization failed (error_type=%s)",
            type(exc).__name__,
        )
        raise SupabaseConfigurationError(
            "Supabase client initialization failed. Check the backend project URL and API key configuration."
        ) from None
    return _supabase_client
