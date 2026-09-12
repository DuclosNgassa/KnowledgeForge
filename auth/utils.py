import logging
import uuid
from datetime import datetime, timedelta

import jwt
from pwdlib import PasswordHash

from config import Config

password_hash = PasswordHash.recommended()

ACCESS_TOKEN_EXPIRY = 3600


def hash_password(plain_password: str) -> str:
    return password_hash.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(user_data: dict, expiry: timedelta | None = None, refresh: bool = False) -> str:
    payload = {
        "exp": datetime.now() + (expiry if expiry is not None else timedelta(seconds=ACCESS_TOKEN_EXPIRY)),
        "user": user_data,
        "jti": str(uuid.uuid4()),
        "refresh": refresh,
    }

    token = jwt.encode(
        payload,
        key=Config.JWT_SECRET_KEY,
        algorithm=Config.JWT_ALGORITHM,
    )

    return token

def decode_token(token: str) -> dict | None:
    try:
        token_data = jwt.decode(
            jwt=token,
            key=Config.JWT_SECRET_KEY,
            algorithms=[Config.JWT_ALGORITHM],
        )
        return token_data
    except jwt.PyJWTError as e:
        logging.error(e)
        return None
