from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Request
from jwt.algorithms import RSAAlgorithm

from finance_api_service.auth import JwtRequestContextProvider, JwtVerifier

ISSUER = "https://auth.test.local"
AUDIENCE = "authenticated"
ACTOR = "20000000-0000-0000-0000-000000000001"
TENANT = "10000000-0000-0000-0000-000000000001"


class StaticKeys:
    def __init__(self, key: dict[str, Any] | None) -> None:
        self.key = key

    async def get(self, key_id: str) -> dict[str, Any] | None:
        return self.key if key_id == "test-key" else None


def key_material() -> tuple[Any, dict[str, Any]]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_jwk = RSAAlgorithm.to_jwk(private_key.public_key(), as_dict=True)
    public_jwk["kid"] = "test-key"
    public_jwk["alg"] = "RS256"
    return private_key, public_jwk


def token(private_key: Any, **overrides: Any) -> str:
    now = datetime.now(UTC)
    claims = {
        "sub": ACTOR,
        "iss": ISSUER,
        "aud": AUDIENCE,
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "role": "authenticated",
    }
    claims.update(overrides)
    return jwt.encode(
        claims,
        private_key,
        algorithm="RS256",
        headers={"kid": "test-key"},
    )


def verifier(public_jwk: dict[str, Any]) -> JwtVerifier:
    return JwtVerifier(
        provider=StaticKeys(public_jwk),
        issuer=ISSUER,
        audience=AUDIENCE,
    )


def provider(public_jwk: dict[str, Any]) -> JwtRequestContextProvider:
    return JwtRequestContextProvider(verifier(public_jwk))


@pytest.mark.asyncio
async def test_valid_token_resolves_finance_request_context() -> None:
    private_key, public_jwk = key_material()
    request = Request(
        {
            "type": "http",
            "headers": [
                (b"authorization", f"Bearer {token(private_key)}".encode()),
                (b"x-tenant-id", TENANT.encode()),
                (b"x-correlation-id", b"correlation-1"),
            ],
        }
    )

    context = await provider(public_jwk).resolve(request)

    assert str(context.actor_id) == ACTOR
    assert str(context.tenant_id) == TENANT
    assert context.correlation_id == "correlation-1"
