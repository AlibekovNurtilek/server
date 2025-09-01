# app/services/customer_services/customer_service.py

import logging
from typing import List, Optional, Dict, Tuple
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.customer_repository import CustomerRepository
from app.db.models import Customer
from app.schemas.customer_schemas import CustomerRead, AccountRead, CardRead, TransactionRead, LoanRead


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

    async def get_customer_by_id(self, customer_id: int) -> CustomerRead:
        """
        Retrieve a customer by ID.

        :param customer_id: The ID of the customer.
        :return: CustomerRead schema with customer data.
        :raises HTTPException: If customer not found or error occurs.
        """
        try:
            customer = await self.repo.get_by_id(customer_id)
            if not customer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Customer not found"
                )
            return CustomerRead.model_validate(customer)
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Failed to retrieve customer {customer_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve customer"
            )

    async def get_accounts_by_customer_id(
        self, customer_id: int, page: int = 1, page_size: int = 10
    ) -> Tuple[List[AccountRead], int]:
        """
        Retrieve paginated accounts for a customer by ID.

        :param customer_id: The ID of the customer.
        :param page: Page number for pagination.
        :param page_size: Number of accounts per page.
        :return: Tuple of list of AccountRead schemas and total count.
        """
        try:
            accounts, total = await self.repo.get_accounts_by_customer_id(
                customer_id=customer_id, page=page, page_size=page_size
            )
            return [AccountRead.model_validate(a) for a in accounts], total
        except Exception as e:
            logger.error(f"Failed to retrieve accounts for customer {customer_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve accounts: {str(e)}"
            )

    async def get_cards_by_customer_id(
        self, customer_id: int, page: int = 1, page_size: int = 10
    ) -> Tuple[List[CardRead], int]:
        """
        Retrieve paginated cards for a customer by ID.

        :param customer_id: The ID of the customer.
        :param page: Page number for pagination.
        :param page_size: Number of cards per page.
        :return: Tuple of list of CardRead schemas and total count.
        """
        try:
            cards, total = await self.repo.get_cards_by_customer_id(
                customer_id=customer_id, page=page, page_size=page_size
            )
            return [CardRead.model_validate(c) for c in cards], total
        except Exception as e:
            logger.error(f"Failed to retrieve cards for customer {customer_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve cards: {str(e)}"
            )

    async def get_transactions_by_customer_id(
        self, customer_id: int, page: int = 1, page_size: int = 10
    ) -> Tuple[List[TransactionRead], int]:
        """
        Retrieve paginated transactions for a customer by ID.

        :param customer_id: The ID of the customer.
        :param page: Page number for pagination.
        :param page_size: Number of transactions per page.
        :return: Tuple of list of TransactionRead schemas and total count.
        """
        try:
            transactions, total = await self.repo.get_transactions_by_customer_id(
                customer_id=customer_id, page=page, page_size=page_size
            )
            return [TransactionRead.model_validate(t) for t in transactions], total
        except Exception as e:
            logger.error(f"Failed to retrieve transactions for customer {customer_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve transactions: {str(e)}"
            )

    async def get_loans_by_customer_id(
        self, customer_id: int, page: int = 1, page_size: int = 10
    ) -> Tuple[List[LoanRead], int]:
        """
        Retrieve paginated loans for a customer by ID.

        :param customer_id: The ID of the customer.
        :param page: Page number for pagination.
        :param page_size: Number of loans per page.
        :return: Tuple of list of LoanRead schemas and total count.
        """
        try:
            loans, total = await self.repo.get_loans_by_customer_id(
                customer_id=customer_id, page=page, page_size=page_size
            )
            return [LoanRead.model_validate(l) for l in loans], total
        except Exception as e:
            logger.error(f"Failed to retrieve loans for customer {customer_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve loans: {str(e)}"
            )