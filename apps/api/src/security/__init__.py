import os

from fastapi import Depends, HTTPException
from fastapi.security.api_key import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

API_SECRET_KEY = os.getenv("API_SECRET_KEY")


def verify_api_key(api_key: str = Depends(api_key_header)):
    if not API_SECRET_KEY:
        raise HTTPException(status_code=500, detail="API key is not set")

    if api_key != API_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Could not validate API key")

    return api_key
