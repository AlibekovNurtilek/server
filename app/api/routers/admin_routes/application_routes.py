from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any, Generic, TypeVar
from pydantic import BaseModel
from pydantic.generics import GenericModel

from app.api.deps import get_db_session, get_current_employee
from app.db.models import EmployeeRole, Employee
from app.services.admin_services.loan_application_service import LoanApplicationService
from app.services.admin_services.card_application_service import CardApplicationService
from app.schemas.application_schemas import (
    LoanApplicationRead,
    LoanApplicationUpdateStatus,
    CardApplicationRead,
    CardApplicationUpdateStatus,
)
from app.schemas.customer_schemas import CustomerRead


# ---------- Generic Pagination ----------
T = TypeVar("T")


class PaginatedItems(GenericModel, Generic[T]):
    items: List[T]
    page: int
    page_size: int
    total: int


# ---------- Loan Applications ----------
class EnrichedLoanApplication(BaseModel):
    application: LoanApplicationRead
    customer: Optional[CustomerRead]
    loan_info: Dict[str, Any]


router = APIRouter(prefix="/api/admin/applications", tags=["applications"])


@router.get("/loans", response_model=PaginatedItems[EnrichedLoanApplication])
async def get_loan_applications(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    session: AsyncSession = Depends(get_db_session),
    current_employee: Employee = Depends(get_current_employee),
):
    """
    Retrieve all loan applications with pagination.
    Only accessible to admin or manager roles.
    """
    if current_employee.role not in [EmployeeRole.admin, EmployeeRole.manager]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to admin or manager roles",
        )

    service = LoanApplicationService(session)
    result = await service.get_all(page=page, page_size=page_size)

    return {
        "items": result["loan_applications"],  # список EnrichedLoanApplication
        "page": page,
        "page_size": page_size,
        "total": result["total"],
    }


@router.patch("/loans/{application_id}", response_model=LoanApplicationRead)
async def update_loan_application_status(
    application_id: int,
    payload: LoanApplicationUpdateStatus,
    session: AsyncSession = Depends(get_db_session),
    current_employee: Employee = Depends(get_current_employee),
):
    """
    Update the status of a loan application by ID.
    Only accessible to admin or manager roles.
    """
    if current_employee.role not in [EmployeeRole.admin, EmployeeRole.manager]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to admin or manager roles",
        )

    service = LoanApplicationService(session)
    return await service.update_status(application_id, payload)


# ---------- Card Applications ----------
@router.get("/cards", response_model=PaginatedItems[CardApplicationRead])
async def get_card_applications(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    session: AsyncSession = Depends(get_db_session),
    current_employee: Employee = Depends(get_current_employee),
):
    """
    Retrieve all card applications with pagination.
    Only accessible to admin or manager roles.
    """
    if current_employee.role not in [EmployeeRole.admin, EmployeeRole.manager]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to admin or manager roles",
        )

    service = CardApplicationService(session)
    result = await service.get_all(page=page, page_size=page_size)
    return {
        "items": result["card_applications"],
        "page": page,
        "page_size": page_size,
        "total": result["total"],
    }


@router.patch("/cards/{application_id}", response_model=CardApplicationRead)
async def update_card_application_status(
    application_id: int,
    payload: CardApplicationUpdateStatus,
    session: AsyncSession = Depends(get_db_session),
    current_employee: Employee = Depends(get_current_employee),
):
    """
    Update the status of a card application by ID.
    Only accessible to admin or manager roles.
    """
    if current_employee.role not in [EmployeeRole.admin, EmployeeRole.manager]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to admin or manager roles",
        )

    service = CardApplicationService(session)
    return await service.update_status(application_id, payload)
