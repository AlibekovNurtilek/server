import logging
from typing import Dict
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.app_repository import LoanApplicationRepository
from app.schemas.application_schemas import LoanApplicationRead, LoanApplicationUpdateStatus


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LoanApplicationService:
    """
    Service layer for managing loan applications.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = LoanApplicationRepository(session)

    async def get_all(self, page: int = 1, page_size: int = 10) -> Dict:
        """
        Retrieve all loan applications with pagination.
        """
        try:
            applications, total = await self.repo.get_all(page=page, page_size=page_size)
            return {
                "loan_applications": [LoanApplicationRead.model_validate(app) for app in applications],
                "total": total
            }
        except Exception as e:
            logger.error(f"Failed to retrieve loan applications: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve loan applications"
            )

    async def update_status(self, application_id: int, data: LoanApplicationUpdateStatus) -> LoanApplicationRead:
        """
        Update the status of a loan application.
        """
        try:
            updated = await self.repo.update_status(application_id, data.status)
            if not updated:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Loan application not found"
                )
            await self.session.commit()
            return LoanApplicationRead.model_validate(updated)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to update loan application {application_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update loan application"
            )
