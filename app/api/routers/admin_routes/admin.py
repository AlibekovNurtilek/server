from fastapi import APIRouter, Depends, Request, HTTPException, status
from starlette.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.api.deps import get_db_session, get_current_employee, EMPLOYEE_SESSION_KEY
from app.schemas.auth_schemas import EmplyeeLoginRequest, EmplyeeOut
from app.services.admin_services.auth_service import AuthService
from app.services.customer_services.customer_service import CustomerService
from app.schemas.customer_schemas import CustomerRead, CustomerReadWithRelations
from app.db.models import EmployeeRole, Employee

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


@router.get("/customers", response_model=List[CustomerRead])
async def get_all_customers(
    limit: int = 10,
    offset: int = 0,
    session: AsyncSession = Depends(get_db_session),
    current_employee: Employee = Depends(get_current_employee),
):
    """
    Retrieve all customers with pagination.
    Only accessible to admin or manager roles.
    """
    if current_employee.role not in [EmployeeRole.admin, EmployeeRole.manager]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to admin or manager roles"
        )
    try:
        service = CustomerService(session)
        return await service.get_all_customers(limit=limit, offset=offset)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve customers: {str(e)}"
        )


@router.get("/customers/{customer_id}", response_model=CustomerReadWithRelations)
async def get_customer_by_id(
    customer_id: int,
    include: Optional[str] = None,  # e.g., "accounts,cards,transactions,loans"
    relations_limit: int = 10,
    relations_offset: int = 0,
    session: AsyncSession = Depends(get_db_session),
    current_employee: Employee = Depends(get_current_employee),
):
    """
    Retrieve a customer by ID with optional related data (accounts, cards, transactions, loans).
    Only accessible to admin or manager roles.
    """
    if current_employee.role not in [EmployeeRole.admin, EmployeeRole.manager]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to admin or manager roles"
        )
    try:
        service = CustomerService(session)
        include_list = include.split(",") if include else []
        return await service.get_customer_by_id(
            customer_id=customer_id,
            include=include_list,
            relations_limit=relations_limit,
            relations_offset=relations_offset,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve customer: {str(e)}"
        )