from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Dict, Any, Optional
import enum
import logging
import json
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.db.models import *
from .common_services import load_cards_data

async def apply_for_card(
    session: AsyncSession,
    customer_id: int,
    card_name: str,
    lang: str = "ky",
) -> tuple[bool, str]:
    if lang not in ["ky", "ru"]:
        lang = "ky"  # Default to Kyrgyz if language is invalid

    # Translation dictionary
    translations = {
        "ky": {
            "card_not_found": "Карта табылган жок",
            "invalid_card_type": "Карта түрү туура эмес",
            "no_suitable_account": "Ылайыктуу эсеп табылган жок",
            "application_submitted": "Заявка жөнөтүлдү",
            "card_name": "Картанын аты",
            "description": "Сүрөттөмө",
            "currency": "Валюта",
            "validity": "Жарактуулук мөөнөтү",
            "issuance_fee": "Чыгаруу акысы",
            "annual_fee": "Жылдык тейлөө акысы",
            "limits": "Чектөөлөр",
            "customer_not_found": "Кардар табылган жок"
        },
        "ru": {
            "card_not_found": "Карта не найдена",
            "invalid_card_type": "Неверный тип карты",
            "no_suitable_account": "Подходящий счёт не найден",
            "application_submitted": "Заявка отправлена",
            "card_name": "Название карты",
            "description": "Описание",
            "currency": "Валюта",
            "validity": "Срок действия",
            "issuance_fee": "Плата за выпуск",
            "annual_fee": "Годовая плата за обслуживание",
            "limits": "Лимиты",
            "customer_not_found": "Клиент не найден"
        }
    }

    # Find customer
    customer_stmt = select(Customer).where(Customer.id == customer_id)
    customer = await session.scalar(customer_stmt)
    if not customer:
        return False, translations[lang]["customer_not_found"]

    # Load cards knowledge base
    cards = load_cards_data(lang)
    # Search for card by name
    card_data = None
    card_key = None
    for key, data in cards.items():
        if data.get("name") == card_name:
            card_data = data
            card_key = key
            break

    if not card_data:
        return False, translations[lang]["card_not_found"]

    # Determine card_type based on key
    if "_Debit" in card_key or card_key in ["Card_Plus", "virtual", "elkart", "Visa_Campus_Card"]:
        card_type = CardType.debit
    elif "_Credit" in card_key:
        card_type = CardType.credit
    else:
        return False, translations[lang]["invalid_card_type"]

    # Find a suitable active current account in KGS
    stmt = (
        select(Account)
        .where(
            Account.customer_id == customer_id,
            Account.status == AccountStatus.active,
            Account.account_type == AccountType.current,
            Account.currency == "KGS",
        )
        .limit(1)
    )
    account = await session.scalar(stmt)
    if not account:
        return False, translations[lang]["no_suitable_account"]

    # Create the application within a transaction
    application = CardApplication(
        customer_id=customer_id,
        account_id=account.id,
        card_type=card_type,
        card_name=card_name,
        status=CardApplicationStatus.pending,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(application)
    await session.flush()  # To get the ID

    # Prepare user message with card details
    details = []
    details.append(f"{translations[lang]['card_name']}: {card_name}")
    if "descr" in card_data:
        details.append(f"{translations[lang]['description']}: {card_data['descr']}")
    if "currency" in card_data:
        details.append(f"{translations[lang]['currency']}: {', '.join(card_data['currency'])}")
    if "validity" in card_data:
        details.append(f"{translations[lang]['validity']}: {card_data['validity']}")
    if "issuance" in card_data:
        details.append(f"{translations[lang]['issuance_fee']}: {card_data['issuance']}")
    if "annual_fee" in card_data:
        details.append(f"{translations[lang]['annual_fee']}: {card_data['annual_fee']}")
    if "limits" in card_data:
        limits_str = "\n".join([f"{k}: {v}" for k, v in card_data["limits"].items() if isinstance(v, str)])
        details.append(f"{translations[lang]['limits']}:\n{limits_str}")

    message = f"{translations[lang]['application_submitted']} #{application.id:04d}\n\n" + "\n".join(details)

    return True, message



async def check_application_status(
    session: AsyncSession,
    customer_id: int,
    application_id: int,
    lang: str = "ky",
) -> tuple[bool, str]:
    """
    Проверяет состояние заявки на карту.

    Args:
        session: Асинхронная сессия SQLAlchemy
        customer_id: ID клиента
        application_id: ID заявки
        lang: Язык ответа ("ky" или "ru")

    Returns:
        Tuple[bool, str]: (успех, сообщение)
    """
    if lang not in ["ky", "ru"]:
        lang = "ky"  # Default to Kyrgyz if language is invalid

    # Translation dictionary
    translations = {
        "ky": {
            "application_not_found": "Арызыңыз табылган жок",
            "access_denied": "Арызыңыз табылган жок",
            "status": "Статус",
            "card_name": "Картанын аты",
            "created_at": "Түзүлгөн датасы",
            "application_info": "Заявка маалыматы",
            "status_pending": "Күтүүдө",
            "status_approved": "Жактырылды",
            "status_rejected": "Четке кагылды",
            "status_processing": "Иштетилүүдө",
        },
        "ru": {
            "application_not_found": "Заявка не найдена",
            "access_denied": "Заявка не найдена",
            "status": "Статус",
            "card_name": "Название карты",
            "created_at": "Дата создания",
            "application_info": "Информация о заявке",
            "status_pending": "В ожидании",
            "status_approved": "Одобрена",
            "status_rejected": "Отклонена",
            "status_processing": "В обработке",
        }
    }

    # Find the application
    stmt = select(CardApplication).where(
        CardApplication.id == application_id
    )
    application = await session.scalar(stmt)

    if not application:
        return False, translations[lang]["application_not_found"]

    # Check if the application belongs to the customer
    if application.customer_id != customer_id:
        return False, translations[lang]["access_denied"]

    # Map status to translated text
    status_map = {
        CardApplicationStatus.pending: translations[lang]["status_pending"],
        CardApplicationStatus.approved: translations[lang]["status_approved"],
        CardApplicationStatus.rejected: translations[lang]["status_rejected"],
        CardApplicationStatus.processing: translations[lang]["status_processing"],
    }

    # Prepare response message
    details = [
        f"{translations[lang]['application_info']} #{application.id:04d}",
        f"{translations[lang]['card_name']}: {application.card_name}",
        f"{translations[lang]['status']}: {status_map[application.status]}",
        f"{translations[lang]['created_at']}: {application.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
    ]

    message = "\n".join(details)
    return True, message