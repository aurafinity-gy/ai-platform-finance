from collections.abc import Mapping
from typing import Any, Protocol
from uuid import UUID, uuid4

import httpx
import jwt
from finance_api import AuthenticationRequiredError, TenantScopeRequiredError
from finance_application import RequestContext
from fastapi import Request
from jwt import PyJWK


class AuthenticationFailedError(AuthenticationRequiredError):
    """Raised when a bearer token cannot be independently authenticated."""


class JwkProvider(Protocol):
    async def get(self, key_id: str) -> Mapping[str, Any] | None: ...


class HttpJwkProvider:
    def __init__(self, url: str) -> None:
        self._url = url
        self._keys: dict[str, Mapping[str, Any]] = {}

    async def get(self, key_id: str) -> Mapping[str, Any] | None:
        if key_id not in self._keys:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(self._url)
                response.raise_for_status()
            payload = response.json()
            self._keys = {
                str(item["kid"]): item
                for item in payload.get("keys", ())
                if isinstance(item, dict) and "kid" in item
            }
        return self._keys.get(key_id)


class JwtVerifier:
    def __init__(
        self,
        *,
        provider: JwkProvider,
        issuer: str,
        audience: str,
    ) -> None:
        self._provider = provider
        self._issuer = issuer
        self._audience = audience

    async def verify(self, token: str) -> Mapping[str, Any]:
        try:
            header = jwt.get_unverified_header(token)
            if header.get("alg") not in {"RS256", "ES256"}:
                raise AuthenticationFailedError("token_algorithm_rejected")
            key_id = header.get("kid")
            if not isinstance(key_id, str):
                raise AuthenticationFailedError("token_key_missing")
            jwk_data = await self._provider.get(key_id)
            if jwk_data is None:
                raise AuthenticationFailedError("token_key_unknown")
            key = PyJWK.from_dict(dict(jwk_data)).key
            claims: Mapping[str, Any] = jwt.decode(
                token,
                key,
                algorithms=[header["alg"]],
                audience=self._audience,
                issuer=self._issuer,
                options={"require": ["sub", "exp", "iat", "iss", "aud"]},
            )
            if claims.get("role") != "authenticated":
                raise AuthenticationFailedError("token_role_rejected")
            return claims
        except AuthenticationFailedError:
            raise
        except (jwt.PyJWTError, ValueError, TypeError) as error:
            raise AuthenticationFailedError("token_invalid") from error


class JwtRequestContextProvider:
    def __init__(self, verifier: JwtVerifier) -> None:
        self._verifier = verifier

    async def resolve(self, request: Request) -> RequestContext:
        authorization = request.headers.get("authorization", "")
        if not authorization.startswith("Bearer "):
            raise AuthenticationRequiredError("bearer_token_required")
        tenant = request.headers.get("x-tenant-id")
        if tenant is None:
            raise TenantScopeRequiredError("tenant_scope_required")
        correlation_id = request.headers.get("x-correlation-id", "").strip()
        try:
            claims = await self._verifier.verify(authorization[7:])
            return RequestContext(
                actor_id=UUID(str(claims["sub"])),
                tenant_id=UUID(tenant),
                correlation_id=correlation_id[:128] or str(uuid4()),
            )
        except (KeyError, ValueError) as error:
            raise AuthenticationFailedError("token_or_tenant_invalid") from error

