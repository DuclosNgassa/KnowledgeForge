from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer

from auth.utils import decode_token


def is_token_valid(token_data) -> bool:
    return True if token_data is not None else False


class TokenBearer(HTTPBearer):

    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> dict | None:
        creds = await super().__call__(request)
        if creds is None:
            raise HTTPException(
                403,
                detail="Please provide an access token",
            )
        token = creds.credentials
        token_data = decode_token(token)

        if not is_token_valid(token_data):
            raise HTTPException(
                401,
                detail="Invalid or expired token",
            )

        self.verify_token_data(token_data)

        return token_data

    def verify_token_data(self, token_data: dict) -> None:
        raise NotImplementedError("Please implement this method in subclass")


class AccessTokenBearer(TokenBearer):
    def verify_token_data(self, token_data: dict) -> None:
        if token_data and token_data['refresh']:
            raise HTTPException(
                403,
                detail="Please provide an access token",
            )


class RefreshTokenBearer(TokenBearer):
    def verify_token_data(self, token_data: dict) -> None:
        if token_data and not token_data['refresh']:
            raise HTTPException(
                403,
                detail="Please provide an refresh token",
            )
