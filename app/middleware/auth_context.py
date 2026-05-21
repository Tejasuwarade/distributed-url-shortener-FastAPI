from __future__ import annotations

import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.security import TokenType, decode_token


class AuthContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request.state.token_payload = None
        request.state.token_error = None

        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization.removeprefix("Bearer ").strip()
            try:
                request.state.token_payload = decode_token(token, expected_type=TokenType.ACCESS)
            except jwt.InvalidTokenError as exc:
                request.state.token_error = str(exc)

        return await call_next(request)
