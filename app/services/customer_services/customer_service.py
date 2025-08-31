# app/services/customer_services/customer_service.py

import logging
from typing import List, Optional
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

    async def get_all_customers(
        self, limit: int = 10, offset: int = 0
    ) -> List[CustomerRead]:
        """
        Retrieve all customers with pagination.

        :param limit: Number of records to return.
        :param offset: Number of records to skip.
        :return: List of customers as schemas.
        :raises HTTPException: If an error occurs.
        """
        try:
            customers = await self.repo.get_all_customers(limit=limit, offset=offset)
            return [CustomerRead.model_validate(c) for c in customers]
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
        relations_limit: int = 10,
        relations_offset: int = 0,
    ) -> CustomerReadWithRelations:
        """
        Retrieve a customer by ID with optional related data (accounts, cards, transactions, loans).

        :param customer_id: The ID of the customer.
        :param include: List of relations to include (e.g., ["accounts", "cards", "transactions", "loans"]).
        :param relations_limit: Number of related records to return per relation.
        :param relations_offset: Number of related records to skip per relation.
        :return: Customer with related data as a schema.
        :raises HTTPException: If customer not found or error occurs.
        """
        try:
            customer = await self.repo.get_by_id(customer_id)
            if not customer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Customer not found"
                )

            # Prepare response data
            customer_data = {
                "id": customer.id,
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "middle_name": customer.middle_name,
                "birth_date": customer.birth_date,
                "passport_number": customer.passport_number,
                "phone_number": customer.phone_number,
                "email": customer.email,
                "address": customer.address,
                "created_at": customer.created_at,
                "updated_at": customer.updated_at,
                # Exclude password_hash for security
            }

            # Handle relations if specified
            include = include or []
            if include:
                if "accounts" in include:
                    accounts = await self.repo.get_accounts_by_customer_id(
                        customer_id, limit=relations_limit, offset=relations_offset
                    )
                    customer_data["accounts"] = [
                        AccountRead.model_validate(a) for a in accounts
                    ]
                else:
                    customer_data["accounts"] = []

                if "cards" in include:
                    cards = await self.repo.get_cards_by_customer_id(
                        customer_id, limit=relations_limit, offset=relations_offset
                    )
                    customer_data["cards"] = [CardRead.model_validate(c) for c in cards]
                else:
                    customer_data["cards"] = []

                if "transactions" in include:
                    try:
                        transactions = await self.repo.get_transactions_by_customer_id(
                            customer_id, limit=relations_limit, offset=relations_offset
                        )
                        customer_data["transactions"] = [
                            TransactionRead.model_validate(t) for t in transactions
                        ]
                    except Exception as e:
                        logger.error(
                            f"Failed to fetch or validate transactions for customer {customer_id}: {str(e)}",
                            exc_info=True
                        )
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to fetch transactions: {str(e)}"
                        )
                    customer_data["transactions"] = [
                        TransactionRead.model_validate(t) for t in transactions
                    ]
                else:
                    customer_data["transactions"] = []

                if "loans" in include:
                    loans = await self.repo.get_loans_by_customer_id(
                        customer_id, limit=relations_limit, offset=relations_offset
                    )
                    customer_data["loans"] = [LoanRead.model_validate(l) for l in loans]
                else:
                    customer_data["loans"] = []

            return CustomerReadWithRelations.model_validate(customer_data)
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Failed to retrieve customer {customer_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve customer"
            )