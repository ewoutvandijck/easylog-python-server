from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.settings import settings

bearer_scheme = HTTPBearer(auto_error=False)


def verify_api_key(token: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> str:
    if not settings.API_SECRET_KEY:
        raise HTTPException(status_code=500, detail="API key is not set")

    if token is None or token.credentials != settings.API_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Could not validate API key")

    return token.credentials
