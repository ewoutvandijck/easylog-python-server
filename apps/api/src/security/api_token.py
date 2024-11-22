from fastapi import Depends, HTTPException
from fastapi.security.api_key import APIKeyHeader

from src.settings import settings

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)


def verify_api_key(api_key: str = Depends(api_key_header)):
    if not settings.API_SECRET_KEY:
        raise HTTPException(status_code=500, detail="API key is not set")

    if api_key != settings.API_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Could not validate API key")

    return api_key
