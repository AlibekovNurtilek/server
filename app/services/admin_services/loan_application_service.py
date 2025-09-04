import logging
from typing import Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.app_repository import LoanApplicationRepository
from app.db.repositories.customer_repository import CustomerRepository
from app.schemas.customer_schemas import CustomerRead
from app.schemas.application_schemas import LoanApplicationRead, LoanApplicationUpdateStatus
from app.services.mcp_services.common_services import load_loans_data


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LoanApplicationService:
    """
    Service layer for managing loan applications.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = LoanApplicationRepository(session)
        self.customer_repo = CustomerRepository(session)

    async def get_all(self, page: int = 1, page_size: int = 10) -> Dict:
        """
        Retrieve all loan applications with customer and loan info.
        """
        try:
            applications, total = await self.repo.get_all(page=page, page_size=page_size)

            # Загружаем справочник кредитов один раз
            loan_products = load_loans_data()

            enriched_apps = []
            for app in applications:
                # 1) заявка
                app_data = LoanApplicationRead.model_validate(app)

                # 2) пользователь
                customer = await self.customer_repo.get_by_id(app.customer_id)
                customer_data = CustomerRead.model_validate(customer) if customer else None

                # 3) кредит (поиск по loan_name заявки)
                loan_info = self._find_loan_info(loan_products, app.loan_type)

                enriched_apps.append({
                    "application": app_data,
                    "customer": customer_data,
                    "loan_info": loan_info
                })

            return {
                "loan_applications": enriched_apps,
                "total": total
            }

        except Exception as e:
            logger.error(f"Failed to retrieve loan applications: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve loan applications"
            )

    def _find_loan_info(self, loan_products: Any, loan_name: str) -> Dict[str, Any]:
        """
        Ищем кредит по имени (в type, name, subcategories, special_offers/programs).
        Возвращаем целиком объект, если найден.
        """
        if not loan_name or not loan_products:
            return {}

        for product in loan_products:
            # 1) Проверяем главный кредит
            if product.get("name") == loan_name or product.get("type") == loan_name:
                # Создаем копию продукта без подкатегорий, спецпрограмм и спецпредложений
                result = {
                    key: value
                    for key, value in product.items()
                    if key not in ("subcategories", "special_programs", "special_offers")
                }
                return result

            # 2) Проверяем подкатегории
            for sub in product.get("subcategories", []):
                if sub.get("name") == loan_name:
                    return sub

            # 3) Проверяем спец программы
            for sp in product.get("special_programs", []):
                if sp.get("name") == loan_name:
                    return sp

            # 4) Проверяем спец предложения (могут быть вложенные dict/списки)
            special_offers = product.get("special_offers", {})
            if isinstance(special_offers, dict):
                for region, offers in special_offers.items():
                    if isinstance(offers, list):
                        for offer in offers:
                            if offer.get("name") == loan_name:
                                return offer

        return {}

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
