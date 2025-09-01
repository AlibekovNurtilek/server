from typing import List, Optional, Tuple
from sqlalchemy import select, or_, union_all, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import text

from app.db.models import Customer, Account, Card, Transaction, Loan

class CustomerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, customer_id: int) -> Optional[Customer]:
        res = await self.session.execute(select(Customer).where(Customer.id == customer_id))
        return res.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[Customer]:
        res = await self.session.execute(select(Customer).where(Customer.email == email))
        return res.scalar_one_or_none()

    async def add(self, customer: Customer) -> Customer:
        self.session.add(customer)
        await self.session.flush()  # чтобы получить id без отдельного запроса
        return customer

    async def get_all_customers(self, page: int = 1, page_size: int = 10) -> Tuple[List[Customer], int]:
        """
        Retrieve all customers with pagination.

        :param page: Page number (1-based).
        :param page_size: Number of records per page.
        :return: Tuple of (list of Customer objects, total count).
        """
        offset = (page - 1) * page_size
        # Query for customers
        stmt = select(Customer).order_by(Customer.id).offset(offset).limit(page_size)
        result = await self.session.execute(stmt)
        customers = result.scalars().all()
        
        # Query for total count
        count_stmt = select(func.count()).select_from(Customer)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()
        
        return customers, total

    async def get_accounts_by_customer_id(self, customer_id: int, limit: int = 10, offset: int = 0) -> List[Account]:
        """
        Retrieve accounts for a specific customer with pagination.
        
        :param customer_id: The ID of the customer.
        :param limit: Number of records to return.
        :param offset: Number of records to skip.
        :return: List of Account objects.
        """
        stmt = select(Account).where(Account.customer_id == customer_id).order_by(Account.id).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_cards_by_customer_id(self, customer_id: int, limit: int = 10, offset: int = 0) -> List[Card]:
        """
        Retrieve cards for a specific customer (via their accounts) with pagination.
        
        :param customer_id: The ID of the customer.
        :param limit: Number of records to return.
        :param offset: Number of records to skip.
        :return: List of Card objects.
        """
        stmt = (
            select(Card)
            .join(Account, Card.account_id == Account.id)
            .where(Account.customer_id == customer_id)
            .order_by(Card.id)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_transactions_by_customer_id(self, customer_id: int, limit: int = 10, offset: int = 0) -> List[Transaction]:
        """
        Retrieve transactions for a specific customer (incoming and outgoing via their accounts) with pagination.
        
        :param customer_id: The ID of the customer.
        :param limit: Number of records to return.
        :param offset: Number of records to skip.
        :return: List of Transaction objects.
        """
        # Subquery for outgoing transactions
        outgoing_stmt = (
            select(Transaction)
            .join(Account, Transaction.from_account_id == Account.id)
            .where(Account.customer_id == customer_id)
            .subquery()
        )
        
        # Subquery for incoming transactions
        incoming_stmt = (
            select(Transaction)
            .join(Account, Transaction.to_account_id == Account.id)
            .where(Account.customer_id == customer_id)
            .subquery()
        )
        
        # Combine subqueries with UNION ALL and order by transactions.id
        union_stmt = (
            select(Transaction)
            .from_statement(
                text(
                    "SELECT * FROM ("
                    "SELECT transactions.* FROM transactions "
                    "JOIN accounts ON transactions.from_account_id = accounts.id "
                    "WHERE accounts.customer_id = :customer_id "
                    "UNION ALL "
                    "SELECT transactions.* FROM transactions "
                    "JOIN accounts ON transactions.to_account_id = accounts.id "
                    "WHERE accounts.customer_id = :customer_id"
                    ") AS combined_transactions "
                    "ORDER BY id ASC LIMIT :limit OFFSET :offset"
                )
            )
            .params(customer_id=customer_id, limit=limit, offset=offset)
        )
        
        result = await self.session.execute(union_stmt)
        return result.scalars().all()

    async def get_loans_by_customer_id(self, customer_id: int, limit: int = 10, offset: int = 0) -> List[Loan]:
        """
        Retrieve loans for a specific customer with pagination.
        
        :param customer_id: The ID of the customer.
        :param limit: Number of records to return.
        :param offset: Number of records to skip.
        :return: List of Loan objects.
        """
        stmt = select(Loan).where(Loan.customer_id == customer_id).order_by(Loan.id).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()