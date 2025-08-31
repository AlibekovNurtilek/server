from fastapi import APIRouter, Depends, Request
from starlette.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, get_current_employee, EMPLOYEE_SESSION_KEY
from app.schemas.auth import  EmplyeeLoginRequest, EmplyeeOut
from app.services.admin_services.auth_service import AuthService

router = APIRouter(prefix="/api/admin", tags=["admin_part"])


@router.post("/login")
async def login(payload: EmplyeeLoginRequest, request: Request, session: AsyncSession = Depends(get_db_session)):
    user = await AuthService(session).validate_login(username=payload.username, password=payload.password)
    request.session[EMPLOYEE_SESSION_KEY] = {"id": user.id, "role": user.role.value}
    return JSONResponse({"message": "Login successful", "user_id": user.id})

@router.post("/logout")
async def logout(request: Request):
    request.session.pop(EMPLOYEE_SESSION_KEY, None)
    return {"message": "Logged out successfully"}

@router.get("/user", response_model=EmplyeeOut)
async def get_me(current=Depends(get_current_employee)):
    return EmplyeeOut.model_validate(current)


