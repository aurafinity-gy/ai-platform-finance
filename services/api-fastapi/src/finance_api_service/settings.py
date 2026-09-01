from collections.abc import Mapping
from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    database_url: str
    auth_jwks_url: str
    auth_issuer: str
    auth_audience: str = "authenticated"

    @classmethod
    def from_environment(
        cls, environment: Mapping[str, str] | None = None
    ) -> "RuntimeSettings":
        values = environment or os.environ
        database_url = values.get("FINANCE_DATABASE_URL", "").strip()
        database_url_file = values.get("FINANCE_DATABASE_URL_FILE", "").strip()
        if not database_url and database_url_file:
            database_url = Path(database_url_file).read_text(encoding="utf-8").strip()
        required = {
            "FINANCE_DATABASE_URL": database_url,
            "FINANCE_AUTH_JWKS_URL": values.get("FINANCE_AUTH_JWKS_URL", "").strip(),
            "FINANCE_AUTH_ISSUER": values.get("FINANCE_AUTH_ISSUER", "").strip(),
        }
        missing = sorted(key for key, value in required.items() if not value)
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        return cls(
            database_url=required["FINANCE_DATABASE_URL"],
            auth_jwks_url=required["FINANCE_AUTH_JWKS_URL"],
            auth_issuer=required["FINANCE_AUTH_ISSUER"],
            auth_audience=values.get("FINANCE_AUTH_AUDIENCE", "authenticated").strip()
            or "authenticated",
        )

