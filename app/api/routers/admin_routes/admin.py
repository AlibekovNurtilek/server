from fastapi import APIRouter, Depends, Request, HTTPException, status, Query
from starlette.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.api.deps import get_db_session, get_current_employee, EMPLOYEE_SESSION_KEY
from app.schemas.auth_schemas import EmplyeeLoginRequest, EmplyeeOut
from app.services.admin_services.auth_service import AuthService
from app.services.customer_services.customer_service import CustomerService
from app.schemas.customer_schemas import CustomerRead, CustomerReadWithRelations, PaginatedCustomers
from app.services.admin_services.employee_service import EmployeeService
from app.db.models import EmployeeRole, Employee
from app.schemas.employee_schemas import EmployeeRead, EmployeeCreate, PaginatedEmployees

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


@router.get("/customers", response_model=PaginatedCustomers)
async def get_all_customers(
    page: int = 1,
    page_size: int = 10,
    session: AsyncSession = Depends(get_db_session),
    current_employee: Employee = Depends(get_current_employee),
):
    """
    Retrieve all customers with pagination (page/page_size).
    Only accessible to admin or manager roles.
    """
    if current_employee.role not in [EmployeeRole.admin, EmployeeRole.manager]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to admin or manager roles"
        )
    try:
        service = CustomerService(session)
        result = await service.get_all_customers(page=page, page_size=page_size)
        return {
            "items": result["customers"],
            "page": page,
            "page_size": page_size,
            "total": result["total"]
        }
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
    accounts_page: int = Query(1, ge=1),
    accounts_page_size: int = Query(10, ge=1),
    cards_page: int = Query(1, ge=1),
    cards_page_size: int = Query(10, ge=1),
    transactions_page: int = Query(1, ge=1),
    transactions_page_size: int = Query(10, ge=1),
    loans_page: int = Query(1, ge=1),
    loans_page_size: int = Query(10, ge=1),
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
        result = await service.get_customer_by_id(
            customer_id=customer_id,
            include=include_list,
            accounts_page=accounts_page,
            accounts_page_size=accounts_page_size,
            cards_page=cards_page,
            cards_page_size=cards_page_size,
            transactions_page=transactions_page,
            transactions_page_size=transactions_page_size,
            loans_page=loans_page,
            loans_page_size=loans_page_size,
        )

        # Формируем ответ в маршруте
        customer_data = {
            "id": result["customer"].id,
            "first_name": result["customer"].first_name,
            "last_name": result["customer"].last_name,
            "middle_name": result["customer"].middle_name,
            "birth_date": result["customer"].birth_date,
            "passport_number": result["customer"].passport_number,
            "phone_number": result["customer"].phone_number,
            "email": result["customer"].email,
            "address": result["customer"].address,
            "created_at": result["customer"].created_at,
            "updated_at": result["customer"].updated_at,
            "accounts": {
                "items": result["accounts"]["items"],
                "page": accounts_page,
                "page_size": accounts_page_size,
                "total": result["accounts"]["total"]
            },
            "cards": {
                "items": result["cards"]["items"],
                "page": cards_page,
                "page_size": cards_page_size,
                "total": result["cards"]["total"]
            },
            "transactions": {
                "items": result["transactions"]["items"],
                "page": transactions_page,
                "page_size": transactions_page_size,
                "total": result["transactions"]["total"]
            },
            "loans": {
                "items": result["loans"]["items"],
                "page": loans_page,
                "page_size": loans_page_size,
                "total": result["loans"]["total"]
            }
        }
        return customer_data
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve customer: {str(e)}"
        )


@router.get("/employees", response_model=PaginatedEmployees)
async def get_all_employees(
    page: int = 1,
    page_size: int = 10,
    session: AsyncSession = Depends(get_db_session),
    current_employee: Employee = Depends(get_current_employee),
):
    """
    Получить всех сотрудников с пагинацией.
    Доступно только для ролей admin.
    """
    if current_employee.role not in [EmployeeRole.admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ ограничен"
        )
    if page < 1 or page_size < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page и page_size должны быть положительными числами"
        )
    try:
        service = EmployeeService(session)
        result = await service.get_all_employees(page=page, page_size=page_size)
        return {
            "items": result["employees"],
            "page": page,
            "page_size": page_size,
            "total": result["total"]
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить сотрудников: {str(e)}"
        )


@router.delete("/employees/{employee_id}", status_code=204)
async def delete_employee(
    employee_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_employee: Employee = Depends(get_current_employee),
):
    """
    Удалить сотрудника по его ID.
    Доступно только для ролей admin или manager.
    """
    if current_employee.role not in [EmployeeRole.admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ ограничен"
        )
    try:
        service = EmployeeService(session)
        await service.delete(employee_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось удалить сотрудника: {str(e)}"
        )

@router.post("/employees", response_model=EmployeeRead, status_code=201)
async def create_employee(
    payload: EmployeeCreate,
    session: AsyncSession = Depends(get_db_session),
    current_employee: Employee = Depends(get_current_employee),
):
    """
    Создать нового сотрудника.
    Доступно только для ролей admin или manager.
    """
    if current_employee.role not in [EmployeeRole.admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ ограничен"
        )
    try:
        service = EmployeeService(session)
        return await service.create(employee_data=payload)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось создать сотрудника: {str(e)}"
        )