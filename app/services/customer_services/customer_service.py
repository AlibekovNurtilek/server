# app/services/customer_services/customer_service.py

import logging
from typing import List, Optional, Dict
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.customer_repository import CustomerRepository
from app.db.models import Customer
from app.schemas.customer_schemas import (
    CustomerRead,
    CustomerReadWithRelations,
    AccountRead,
    CardRead,
    TransactionRead,
    LoanRead,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CustomerService:
    """
    Service layer for managing customers in the admin panel.
    Handles business logic for customer operations, using schemas for output.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = CustomerRepository(session)

    async def get_all_customers(self, page: int = 1, page_size: int = 10) -> Dict:
        """
        Retrieve all customers with pagination.

        :param page: Page number (1-based).
        :param page_size: Number of records per page.
        :return: Dictionary with customers and total count.
        :raises HTTPException: If an error occurs.
        """
        try:
            offset = (page - 1) * page_size
            customers, total = await self.repo.get_all_customers(page=page, page_size=page_size)
            return {
                "customers": [CustomerRead.model_validate(c) for c in customers],
                "total": total
            }
        except Exception as e:
            logger.error(f"Failed to retrieve customers: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve customers"
            )

    async def get_customer_by_id(
        self,
        customer_id: int,
        include: Optional[List[str]] = None,
        accounts_page: int = 1,
        accounts_page_size: int = 10,
        cards_page: int = 1,
        cards_page_size: int = 10,
        transactions_page: int = 1,
        transactions_page_size: int = 10,
        loans_page: int = 1,
        loans_page_size: int = 10,
    ) -> Dict:
        """
        Retrieve a customer by ID with optional related data (accounts, cards, transactions, loans).

        :param customer_id: The ID of the customer.
        :param include: List of relations to include (e.g., ["accounts", "cards", "transactions", "loans"]).
        :param accounts_page: Page number for accounts pagination.
        :param accounts_page_size: Number of accounts per page.
        :param cards_page: Page number for cards pagination.
        :param cards_page_size: Number of cards per page.
        :param transactions_page: Page number for transactions pagination.
        :param transactions_page_size: Number of transactions per page.
        :param loans_page: Page number for loans pagination.
        :param loans_page_size: Number of loans per page.
        :return: Dictionary with customer and related data.
        :raises HTTPException: If customer not found or error occurs.
        """
        try:
            customer = await self.repo.get_by_id(customer_id)
            if not customer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Customer not found"
                )

            # Преобразуем клиента в Pydantic-схему
            customer_data = CustomerRead.model_validate(customer)

            # Инициализируем словарь для ответа
            result = {
                "customer": customer_data,
                "accounts": {"items": [], "total": 0},
                "cards": {"items": [], "total": 0},
                "transactions": {"items": [], "total": 0},
                "loans": {"items": [], "total": 0},
            }

            # Обрабатываем отношения, если они указаны
            include = include or []
            if include:
                if "accounts" in include:
                    accounts, accounts_total = await self.repo.get_accounts_by_customer_id(
                        customer_id, page=accounts_page, page_size=accounts_page_size
                    )
                    result["accounts"] = {
                        "items": [AccountRead.model_validate(a) for a in accounts],
                        "total": accounts_total
                    }

                if "cards" in include:
                    cards, cards_total = await self.repo.get_cards_by_customer_id(
                        customer_id, page=cards_page, page_size=cards_page_size
                    )
                    result["cards"] = {
                        "items": [CardRead.model_validate(c) for c in cards],
                        "total": cards_total
                    }

                if "transactions" in include:
                    try:
                        transactions, transactions_total = await self.repo.get_transactions_by_customer_id(
                            customer_id, page=transactions_page, page_size=transactions_page_size
                        )
                        result["transactions"] = {
                            "items": [TransactionRead.model_validate(t) for t in transactions],
                            "total": transactions_total
                        }
                    except Exception as e:
                        logger.error(
                            f"Failed to fetch or validate transactions for customer {customer_id}: {str(e)}",
                            exc_info=True
                        )
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to fetch transactions: {str(e)}"
                        )

                if "loans" in include:
                    loans, loans_total = await self.repo.get_loans_by_customer_id(
                        customer_id, page=loans_page, page_size=loans_page_size
                    )
                    result["loans"] = {
                        "items": [LoanRead.model_validate(l) for l in loans],
                        "total": loans_total
                    }

            return result
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Failed to retrieve customer {customer_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve customer"
            )