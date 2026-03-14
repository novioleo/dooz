"""Auth API."""

from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import jwt, JWTError

SECRET_KEY = "dooz-secret"
ALGORITHM = "HS256"

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

_tenant_manager = None


def set_tenant_manager(mgr):
    global _tenant_manager
    _tenant_manager = mgr


class Token(BaseModel):
    access_token: str
    token_type: str


def create_token(client_id: str, tenant_id: str) -> str:
    return jwt.encode(
        {"sub": client_id, "tenant_id": tenant_id, "exp": datetime.utcnow() + timedelta(hours=1)},
        SECRET_KEY, algorithm=ALGORITHM
    )


def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/token", response_model=Token)
async def login(form: OAuth2PasswordRequestForm = Depends()):
    tenant = _tenant_manager.verify_client(form.username, form.password)
    if not tenant:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return Token(
        access_token=create_token(tenant.client_id, tenant.tenant_id),
        token_type="bearer"
    )
