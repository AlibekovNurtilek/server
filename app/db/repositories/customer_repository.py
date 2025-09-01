from typing import List, Optional, Tuple
from sqlalchemy import select, or_, union_all, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

    async def get_accounts_by_customer_id(self, customer_id: int, page: int = 1, page_size: int = 10) -> Tuple[List[Account], int]:
        """
        Retrieve accounts for a specific customer with pagination.
        
        :param customer_id: The ID of the customer.
        :param page: Page number for pagination.
        :param page_size: Number of records per page.
        :return: Tuple of (list of Account objects, total count).
        """
        offset = (page - 1) * page_size
        # Query for accounts
        stmt = select(Account).where(Account.customer_id == customer_id).order_by(Account.id).offset(offset).limit(page_size)
        result = await self.session.execute(stmt)
        accounts = result.scalars().all()
        
        # Query for total count
        count_stmt = select(func.count()).select_from(Account).where(Account.customer_id == customer_id)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()
        
        return accounts, total

    async def get_cards_by_customer_id(self, customer_id: int, page: int = 1, page_size: int = 10) -> Tuple[List[Card], int]:
        """
        Retrieve cards for a specific customer (via their accounts) with pagination.
        
        :param customer_id: The ID of the customer.
        :param page: Page number for pagination.
        :param page_size: Number of records per page.
        :return: Tuple of (list of Card objects, total count).
        """
        offset = (page - 1) * page_size
        # Query for cards
        stmt = (
            select(Card)
            .join(Account, Card.account_id == Account.id)
            .where(Account.customer_id == customer_id)
            .order_by(Card.id)
            .offset(offset)
            .limit(page_size)
        )
        result = await self.session.execute(stmt)
        cards = result.scalars().all()
        
        # Query for total count
        count_stmt = select(func.count()).select_from(Card).join(Account, Card.account_id == Account.id).where(Account.customer_id == customer_id)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()
        
        return cards, total

    async def get_transactions_by_customer_id(self, customer_id: int, page: int = 1, page_size: int = 10) -> Tuple[List[Transaction], int]:
        """
        Retrieve transactions for a specific customer (incoming and outgoing via their accounts) with pagination.
        
        :param customer_id: The ID of the customer.
        :param page: Page number for pagination.
        :param page_size: Number of records per page.
        :return: Tuple of (list of Transaction objects, total count).
        """
        offset = (page - 1) * page_size
        
        # Основной запрос с DISTINCT чтобы избежать дубликатов
        stmt = (
            select(Transaction)
            .distinct()
            .join(
                Account, 
                or_(
                    Transaction.from_account_id == Account.id,
                    Transaction.to_account_id == Account.id
                )
            )
            .where(Account.customer_id == customer_id)
            .order_by(Transaction.created_at.desc(), Transaction.id.desc())
            .offset(offset)
            .limit(page_size)
        )
        
        result = await self.session.execute(stmt)
        transactions = result.scalars().all()
        
        # Запрос для подсчета общего количества (тоже с DISTINCT)
        count_stmt = (
            select(func.count(func.distinct(Transaction.id)))
            .select_from(Transaction)
            .join(
                Account, 
                or_(
                    Transaction.from_account_id == Account.id,
                    Transaction.to_account_id == Account.id
                )
            )
            .where(Account.customer_id == customer_id)
        )
        
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one() or 0
        
        return transactions, total

    async def get_loans_by_customer_id(self, customer_id: int, page: int = 1, page_size: int = 10) -> Tuple[List[Loan], int]:
        """
        Retrieve loans for a specific customer with pagination.
        
        :param customer_id: The ID of the customer.
        :param page: Page number for pagination.
        :param page_size: Number of records per page.
        :return: Tuple of (list of Loan objects, total count).
        """
        offset = (page - 1) * page_size
        # Query for loans
        stmt = select(Loan).where(Loan.customer_id == customer_id).order_by(Loan.id).offset(offset).limit(page_size)
        result = await self.session.execute(stmt)
        loans = result.scalars().all()
        
        # Query for total count
        count_stmt = select(func.count()).select_from(Loan).where(Loan.customer_id == customer_id)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()
        
        return loans, total