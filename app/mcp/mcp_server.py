from __future__ import annotations

import os
from dotenv import load_dotenv
load_dotenv()

import asyncio
from fastmcp import FastMCP
from typing import List, Optional
import json
import logging

# --- Async SQLAlchemy session ---
from app.db.base import SessionLocal  # async_sessionmaker(AsyncSession)
from app.db.models import Customer

# --- Доменные сервисы без БД ---
from app.services.mcp_services.common_services import *  # noqa
from app.services.mcp_services.personal_services import *  # noqa

# =====================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =====================================================================

async def _get_customer(session, customer_id: int) -> Optional[Customer]:
    return await session.get(Customer, customer_id)


# Создаём FastMCP сервер
server = FastMCP("banking-mcp-server")

# =====================================================================
# БАНКОВСКИЕ ИНСТРУМЕНТЫ (работают через Async SQLAlchemy + наши сервисы)
# Каждый тул принимает lang: str = "ky" и возвращает текст на выбранном языке
# =====================================================================

@server.tool(
    name="get_balance",
    description="Колдонуучунун бардык эсептериндеги жалпы балансты алуу. (lang: ky|ru)"
)
async def get_balance_tool(customer_id: int, lang: str = "ky"):
    async with SessionLocal() as session:
        customer = await _get_customer(session, customer_id)
        if not customer:
            return "Колдонуучу табылган жок." if lang == "ky" else "Пользователь не найден."
        total, msg = await get_balance(session, customer, lang=lang)
        return msg


@server.tool(
    name="get_transactions",
    description="Колдонуучунун акыркы транзакцияларынын тизмесин алуу (limit, default=5). (lang: ky|ru)"
)
async def get_transactions_tool(customer_id: int, limit: int = 5, lang: str = "ky"):
    async with SessionLocal() as session:
        customer = await _get_customer(session, customer_id)
        if not customer:
            return "Колдонуучу табылган жок." if lang == "ky" else "Пользователь не найден."
        txs, err = await get_transactions(session, customer, limit=limit, lang=lang)
        if err:
            return err
        if not txs:
            return "Акыркы транзакциялар табылган жок." if lang == "ky" else "Последние транзакции не найдены."
        title = "Акыркы транзакциялар:\n" if lang == "ky" else "Последние транзакции:\n"
        lines = []
        for t in txs:
            lines.append(f"{t['amount']:.2f} {t.get('currency','KGS')} | {t['from_fullname']} {t['direction']} {t['to_fullname']} | {t['description']} | {t['timestamp']}")
        return title + "\n".join(lines)


@server.tool(
    name="transfer_money",
    description="Башка колдонуучуга аты боюнча акча которуу. (params: to_name, amount, currency='KGS', lang: ky|ru)"
)
async def transfer_money_tool(customer_id: int, to_account_number: str, amount: float = 0, currency: str = "KGS", lang: str = "ky"):
    async with SessionLocal() as session:
        customer = await _get_customer(session, customer_id)
        if not customer:
            return "Колдонуучу табылган жок." if lang == "ky" else "Пользователь не найден."
        ok, msg = await transfer_money(session, customer, to_account_number, amount, currency=currency, lang=lang)
        return msg


@server.tool(
    name="get_last_incoming_transaction",
    description="Акыркы кирген транзакция тууралуу маалымат алуу. (lang: ky|ru)"
)
async def get_last_incoming_transaction_tool(customer_id: int, lang: str = "ky"):
    async with SessionLocal() as session:
        customer = await _get_customer(session, customer_id)
        if not customer:
            return "Колдонуучу табылган жок." if lang == "ky" else "Пользователь не найден."
        _, msg = await get_last_incoming_transaction(session, customer, lang=lang)
        return msg


@server.tool(
    name="get_accounts_info",
    description="Колдонуучунун бардык эсептеринин тизмеси жана балансы. (lang: ky|ru)"
)
async def get_accounts_info_tool(customer_id: int, lang: str = "ky"):
    async with SessionLocal() as session:
        customer = await _get_customer(session, customer_id)
        if not customer:
            return "Колдонуучу табылган жок." if lang == "ky" else "Пользователь не найден."
        accounts, err = await get_accounts_info(session, customer, lang=lang)
        if err:
            return err
        if not accounts:
            return "Сиздин банк эсебиңиз табылган жок." if lang == "ky" else "Ваши банковские счета не найдены."
        title = "Сиздин эсептериңиз:\n" if lang == "ky" else "Ваши счета:\n"
        lines = []
        for acc in accounts:
            lines.append(f"-{acc['account_number']}: {acc['balance']:.2f} {acc.get('currency','KGS')} ({acc['status']})")
        return title + "\n".join(lines)


@server.tool(
    name="get_incoming_sum_for_period",
    description="Көрсөтүлгөн аралыкта кирген которуулар (входящие) жалпы суммасы. (YYYY-MM-DD, YYYY-MM-DD; lang: ky|ru)"
)
async def get_incoming_sum_for_period_tool(customer_id: int, start_date: str, end_date: str, lang: str = "ky"):
    async with SessionLocal() as session:
        customer = await _get_customer(session, customer_id)
        if not customer:
            return "Колдонуучу табылган жок." if lang == "ky" else "Пользователь не найден."
        total, msg = await get_incoming_sum_for_period(session, customer, start_date, end_date, lang=lang)
        return msg


@server.tool(
    name="get_outgoing_sum_for_period",
    description="Көрсөтүлгөн аралыкта чыккан которуулар (исходящие) жалпы суммасы. (YYYY-MM-DD, YYYY-MM-DD; lang: ky|ru)"
)
async def get_outgoing_sum_for_period_tool(customer_id: int, start_date: str, end_date: str, lang: str = "ky"):
    async with SessionLocal() as session:
        customer = await _get_customer(session, customer_id)
        if not customer:
            return "Колдонуучу табылган жок." if lang == "ky" else "Пользователь не найден."
        total, msg = await get_outgoing_sum_for_period(session, customer, start_date, end_date, lang=lang)
        return msg


@server.tool(
    name="get_last_3_transfer_recipients",
    description="Акыркы 3 кото руунун алуучуларынын тизмеси. (lang: ky|ru)"
)
async def get_last_3_transfer_recipients_tool(customer_id: int, lang: str = "ky"):
    async with SessionLocal() as session:
        customer = await _get_customer(session, customer_id)
        if not customer:
            return "Колдонуучу табылган жок." if lang == "ky" else "Пользователь не найден."
        recipients, err = await get_last_3_transfer_recipients(session, customer, lang=lang)
        if err:
            return err
        if not recipients:
            return "Акыркы алуучулар табылган жок." if lang == "ky" else "Последние получатели не найдены."
        title = "Акыркы 3 алуучу:\n" if lang == "ky" else "Последние 3 получателя:\n"
        return title + "\n".join(f"- {name}" for name in recipients)


@server.tool(
    name="get_largest_transaction",
    description="Эң чоң транзакция (суммасы боюнча) жана анын багыты. (lang: ky|ru)"
)
async def get_largest_transaction_tool(customer_id: int, lang: str = "ky"):
    async with SessionLocal() as session:
        customer = await _get_customer(session, customer_id)
        if not customer:
            return "Колдонуучу табылган жок." if lang == "ky" else "Пользователь не найден."
        tx, err = await get_largest_transaction(session, customer, lang=lang)
        if err:
            return err
        if not tx:
            return "Транзакциялар табылган жок." if lang == "ky" else "Транзакции не найдены."
        return (
            "Эң чоң транзакция: " if lang == "ky" else "Крупнейшая транзакция: "
        ) + f"{tx['amount']:.2f} {tx.get('currency','KGS')} | {tx['from_fullname']} {tx['direction']} {tx['to_fullname']} | {tx['description']} | {tx['timestamp']}"


# =====================================================================
# КАРТЫ / ДЕПОЗИТЫ / FAQ — эти сервисы не требуют БД, оставляем как есть
# =====================================================================

@server.tool(
    name="list_all_card_names",
    description="DemirBank'тагы бардык карталардын тизмесин кайтарат"
)
async def list_all_card_names_tool(lang: str = "ky"):
    result = list_all_card_names(lang=lang)
    return "".join(f"{'Карта аты' if lang == 'ky' else 'Название карты'}: {card['name']}\n" for card in result)


@server.tool(
    name="get_card_details",
    description="Карта аталышы боюнча бардык негизги маалыматты кайтарат (валюта, мөөнөтү, чыгымдар, лимиттер, сүрөттөмө)."
)
async def get_card_details_tool(card_name: str, lang: str = "ky"):
    result = get_card_details(card_name, lang=lang)
    if "error" in result:
        return result["error"]
    return "\n".join(f"{k}: {v}" for k, v in result.items())


@server.tool(
    name="compare_cards",
    description="Карталарды негизги параметрлер боюнча салыштырат. Аргумент катары карталардын аттарынын тизмеси берилет (2-4 карта)."
)
async def compare_cards_tool(card_names: List[str], lang: str = "ky"):
    cards = compare_cards(card_names, lang=lang)
    if len(cards) < 2:
        return "Карта салыштыруу үчүн эң азы 2 карта керек." if lang == "ky" else "Для сравнения карт нужно минимум 2 карты."

    result_text = f"{'📋 Салыштырылган карталар' if lang == 'ky' else '📋 Сравниваемые карты'}:\n" + "\n".join(f"{i}. {c['name']}" for i, c in enumerate(cards, 1)) + "\n\n"

    all_keys = set(k for c in cards for k in c.keys() if k != "name")
    similarities, differences = [], []
    for key in all_keys:
        vals = []
        for c in cards:
            v = c.get(key, "белгисиз" if lang == "ky" else "неизвестно")
            if isinstance(v, list):
                v = ", ".join(v)
            elif isinstance(v, dict):
                v = json.dumps(v, ensure_ascii=False)
            vals.append(v)
        if len(set(vals)) == 1:
            similarities.append((key, vals[0]))
        else:
            differences.append((key, [f"{c['name']}: {v}" for c, v in zip(cards, vals)]))

    result_text += f"{'✅ Окшоштуктары' if lang == 'ky' else '✅ Общее'}:\n" + ("\n".join(f"• {k}: {v}" for k, v in similarities) or f"{'• Жок' if lang == 'ky' else '• Нет'}") + "\n"
    result_text += f"{'⚖️ Айырмачылыктары' if lang == 'ky' else '⚖️ Различия'}:\n"
    if differences:
        for k, infos in differences:
            result_text += f"• {k}:\n" + "\n".join(f"  - {info}" for info in infos) + "\n"
    else:
        result_text += f"{'• Жок' if lang == 'ky' else '• Нет'}\n"
    return result_text


@server.tool(
    name="get_card_limits",
    description="Карта аталышы боюнча лимиттерди кайтарат (ATM, POS, контактсыз ж.б.)."
)
async def get_card_limits_tool(card_name: str, lang: str = "ky"):
    result = get_card_limits(card_name, lang=lang)
    if "error" in result:
        return result["error"]
    return json.dumps(result, ensure_ascii=False, indent=2)


@server.tool(
    name="get_card_benefits",
    description="Карта аталышы боюнча артыкчылыктарды жана өзгөчөлүктөрдү кайтарат."
)
async def get_card_benefits_tool(card_name: str, lang: str = "ky"):
    result = get_card_benefits(card_name, lang=lang)
    return json.dumps(result, ensure_ascii=False, indent=2)


@server.tool(
    name="get_cards_by_type",
    description="Карталарды түрү боюнча фильтрлейт (дебеттик/кредиттик)."
)
async def get_cards_by_type_tool(card_type: str, lang: str = "ky"):
    result = get_cards_by_type(card_type, lang=lang)
    return f"{'📋 ' + card_type.title() + ' карталары' if lang == 'ky' else '📋 Карты ' + card_type.title()}:\n\n" + "\n".join(f"• {c['name']}" for c in result)


@server.tool(
    name="get_cards_by_payment_system",
    description="Карталарды төлөм системасы боюнча фильтрлейт (Visa/Mastercard)."
)
async def get_cards_by_payment_system_tool(system: str, lang: str = "ky"):
    result = get_cards_by_payment_system(system, lang=lang)
    return f"{'📋 ' + system.title() + ' карталары' if lang == 'ky' else '📋 Карты ' + system.title()}:\n\n" + "\n".join(f"• {c['name']}" for c in result)


@server.tool(
    name="get_cards_by_fee_range",
    description="Карталарды жылдык акы диапазону боюнча фильтрлейт."
)
async def get_cards_by_fee_range_tool(min_fee: str = None, max_fee: str = None, lang: str = "ky"):
    result = get_cards_by_fee_range(min_fee, max_fee, lang=lang)
    lines = [f"{'📋 Карталар' if lang == 'ky' else '📋 Карты'}:\n"]
    for c in result:
        lines.append(f"• {c['name']}: {c.get('annual_fee', 'белгисиз' if lang == 'ky' else 'неизвестно')}")
    return "\n".join(lines)


@server.tool(
    name="get_cards_by_currency",
    description="Карталарды валюта боюнча фильтрлейт (KGS, USD, EUR)."
)
async def get_cards_by_currency_tool(currency: str, lang: str = "ky"):
    result = get_cards_by_currency(currency, lang=lang)
    return f"{'📋 ' + currency.upper() + ' валютасын колдогон карталар' if lang == 'ky' else '📋 Карты, поддерживающие валюту ' + currency.upper()}:\n\n" + "\n".join(f"• {c['name']}" for c in result)


@server.tool(
    name="get_card_instructions",
    description="Картанын колдонуу көрсөтмөлөрүн кайтарат (Card Plus, Virtual Card үчүн)."
)
async def get_card_instructions_tool(card_name: str, lang: str = "ky"):
    result = get_card_instructions(card_name, lang=lang)
    if "error" in result:
        return result["error"]
    lines = [f"{'📖 ' + card_name + ' картасынын көрсөтмөлөрү' if lang == 'ky' else '📖 Инструкции для карты ' + card_name}:\n"]
    for k, v in result.items():
        if isinstance(v, dict):
            lines.append(f"{'🔹 ' + k.title() if lang == 'ky' else '🔹 ' + k.title()}:")
            for sk, sv in v.items():
                lines.append(f"  • {sk}: {sv}")
        elif isinstance(v, list):
            lines.append(f"{'🔹 ' + k.title() if lang == 'ky' else '🔹 ' + k.title()}:")
            for item in v:
                lines.append(f"  • {item}")
        else:
            lines.append(f"{'🔹 ' + k.title() if lang == 'ky' else '🔹 ' + k.title()}: {v}")
    return "\n".join(lines)


@server.tool(
    name="get_card_conditions",
    description="Картанын шарттарын жана талаптарын кайтарат (Elkart үчүн)."
)
async def get_card_conditions_tool(card_name: str, lang: str = "ky"):
    result = get_card_conditions(card_name, lang=lang)
    if "error" in result:
        return result["error"]
    lines = [f"{'📋 ' + card_name + ' картасынын шарттары' if lang == 'ky' else '📋 Условия карты ' + card_name}:\n"]
    for k, v in result.items():
        if isinstance(v, dict):
            lines.append(f"{'🔹 ' + k.title() if lang == 'ky' else '🔹 ' + k.title()}:")
            for sk, sv in v.items():
                lines.append(f"  • {sk}: {sv}")
        else:
            lines.append(f"{'🔹 ' + k.title() if lang == 'ky' else '🔹 ' + k.title()}: {v}")
    return "\n".join(lines)


@server.tool(
    name="get_cards_with_features",
    description="Белгилүү өзгөчөлүктөргө ээ карталарды табат."
)
async def get_cards_with_features_tool(features: List[str], lang: str = "ky"):
    result = get_cards_with_features(features, lang=lang)
    lines = [f"{'📋 ' + '\', \''.join(features) + ' өзгөчөлүктөрү бар карталар' if lang == 'ky' else '📋 Карты с функциями ' + '\', \''.join(features)}:\n"]
    for c in result:
        lines.append(f"• {c['name']}")
    return "\n".join(lines)


@server.tool(
    name="get_card_recommendations",
    description="Критерийлерге ылайык карта сунуштарын кайтарат."
)
async def get_card_recommendations_tool(criteria: dict, lang: str = "ky"):
    result = get_card_recommendations(criteria, lang=lang)
    lines = [f"{'🎯 Карта сунуштары' if lang == 'ky' else '🎯 Рекомендации карт'}:\n"]
    for i, c in enumerate(result, 1):
        score = c.get("recommendation_score", 0)
        fee = c.get("annual_fee", "белгисиз" if lang == "ky" else "неизвестно")
        lines.append(f"{i}. {c['name']} ({'упай' if lang == 'ky' else 'баллы'}: {score})")
        lines.append(f"   {'Жылдык акы' if lang == 'ky' else 'Годовая плата'}: {fee}")
        if "descr" in c:
            descr = c["descr"]
            if len(descr) > 100:
                descr = descr[:100] + "..."
            lines.append(f"   {'Сүрөттөмө' if lang == 'ky' else 'Описание'}: {descr}")
        lines.append("")
    return "\n".join(lines)


@server.tool(
    name="get_bank_info",
    description="Банк тууралуу негизги маалыматты кайтарат (аты, негизделген жылы, лицензия)."
)
async def get_bank_info_tool(lang: str = "ky"):
    result = get_bank_info(lang=lang)
    return (
        f"{'🏦 ' + result['bank_name'] if lang == 'ky' else '🏦 ' + result['bank_name']}\n\n"
        f"{'📅 Негизделген' if lang == 'ky' else '📅 Основан'}: {result['founded']}\n"
        f"{'📜 Лицензия' if lang == 'ky' else '📜 Лицензия'}: {result['license']}\n"
        f"{'📝 Сүрөттөмө' if lang == 'ky' else '📝 Описание'}: {result['descr']}\n"
    )


@server.tool(
    name="get_bank_mission",
    description="Банктын миссиясын жана тарыхын кайтарат."
)
async def get_bank_mission_tool(lang: str = "ky"):
    return f"{'🎯 Банктын миссиясы' if lang == 'ky' else '🎯 Миссия банка'}:\n\n" + get_bank_mission(lang=lang)


@server.tool(
    name="get_bank_values",
    description="Банктын баалуулуктарын жана принциптерин кайтарат."
)
async def get_bank_values_tool(lang: str = "ky"):
    values = get_bank_values(lang=lang)
    return f"{'💎 Банктын баалуулуктары' if lang == 'ky' else '💎 Ценности банка'}:\n\n" + "\n".join(f"{i}. {v}" for i, v in enumerate(values, 1))


@server.tool(
    name="get_ownership_info",
    description="Банктын ээлик маалыматтарын кайтарат."
)
async def get_ownership_info_tool(lang: str = "ky"):
    o = get_ownership_info(lang=lang)
    return (
        f"{'👥 Ээлик маалыматтары' if lang == 'ky' else '👥 Информация о владельцах'}:\n\n"
        f"{'🔹 Негизги акционер' if lang == 'ky' else '🔹 Основной акционер'}: {o.get('main_shareholder', 'белгисиз' if lang == 'ky' else 'неизвестно')}\n"
        f"{'🔹 Өлкө' if lang == 'ky' else '🔹 Страна'}: {o.get('country', 'белгисиз' if lang == 'ky' else 'неизвестно')}\n"
        f"{'🔹 Ээлик пайы' if lang == 'ky' else '🔹 Доля владения'}: {o.get('ownership_percentage', 'белгисиз' if lang == 'ky' else 'неизвестно')}\n"
    )


@server.tool(
    name="get_branch_network",
    description="Банктын филиалдар тармагын кайтарат."
)
async def get_branch_network_tool(lang: str = "ky"):
    b = get_branch_network(lang=lang)
    lines = [f"{'🏢 Филиалдар тармагы' if lang == 'ky' else '🏢 Сеть филиалов'}:\n"]
    lines.append(f"{'🏛️ Башкы кеңсе' if lang == 'ky' else '🏛️ Головной офис'}: {b.get('head_office', 'белгисиз' if lang == 'ky' else 'неизвестно')}\n")
    regions = b.get('regions', [])
    if regions:
        lines.append(f"{'📍 Аймактык филиалдар' if lang == 'ky' else '📍 Региональные филиалы'}:")
        lines.extend(f"{i}. {r}" for i, r in enumerate(regions, 1))
    return "\n".join(lines)


@server.tool(
    name="get_contact_info",
    description="Банктын байланыш маалыматтарын кайтарат."
)
async def get_contact_info_tool(lang: str = "ky"):
    c = get_contact_info(lang=lang)
    return (
        f"{'📞 Байланыш маалыматтары' if lang == 'ky' else '📞 Контактная информация'}:\n\n"
        f"{'📱 Телефон' if lang == 'ky' else '📱 Телефон'}: {c.get('phone', 'белгисиз' if lang == 'ky' else 'неизвестно')}\n"
        f"{'📧 Электрондук почта' if lang == 'ky' else '📧 Электронная почта'}: {c.get('email', 'белгисиз' if lang == 'ky' else 'неизвестно')}\n"
        f"{'📍 Дарек' if lang == 'ky' else '📍 Адрес'}: {c.get('address', 'белгисиз' if lang == 'ky' else 'неизвестно')}\n"
    )


@server.tool(
    name="get_complete_about_us",
    description="Банк тууралуу толук маалыматты кайтарат."
)
async def get_complete_about_us_tool(lang: str = "ky"):
    data = get_complete_about_us(lang=lang)
    lines = [f"{'🏦 ' + data.get('bank_name', 'DemirBank') if lang == 'ky' else '🏦 ' + data.get('bank_name', 'DemirBank')}\n"]
    lines.append(f"\n{'🎯 Миссия' if lang == 'ky' else '🎯 Миссия'}:\n" + data.get('mission', '') + "\n")
    values = data.get('values', [])
    if values:
        lines.append(f"{'💎 Баалуулуктар' if lang == 'ky' else '💎 Ценности'}:")
        lines.extend(f"{i}. {v}" for i, v in enumerate(values, 1))
        lines.append("")
    ownership = data.get('ownership', {})
    if ownership:
        lines.append(f"{'👥 Ээлик' if lang == 'ky' else '👥 Владение'}:")
        lines.append(f"• {'Негизги акционер' if lang == 'ky' else 'Основной акционер'}: {ownership.get('main_shareholder', '')}")
        lines.append(f"• {'Өлкө' if lang == 'ky' else 'Страна'}: {ownership.get('country', '')}")
        lines.append(f"• {'Ээлик пайы' if lang == 'ky' else 'Доля владения'}: {ownership.get('ownership_percentage', '')}")
        lines.append("")
    branches = data.get('branches', {})
    if branches:
        lines.append(f"{'🏢 Филиалдар' if lang == 'ky' else '🏢 Филиалы'}:")
        lines.append(f"• {'Башкы кеңсе' if lang == 'ky' else 'Головной офис'}: {branches.get('head_office', '')}")
        regs = branches.get('regions', [])
        if regs:
            lines.append(f"{'• Аймактык филиалдар' if lang == 'ky' else '• Региональные филиалы'}:")
            lines.extend(f"  - {r}" for r in regs)
        lines.append("")
    contact = data.get('contact', {})
    if contact:
        lines.append(f"{'📞 Байланыш' if lang == 'ky' else '📞 Контакты'}:")
        lines.append(f"• {'Телефон' if lang == 'ky' else 'Телефон'}: {contact.get('phone', '')}")
        lines.append(f"• {'Электрондук почта' if lang == 'ky' else 'Электронная почта'}: {contact.get('email', '')}")
        lines.append(f"• {'Дарек' if lang == 'ky' else 'Адрес'}: {contact.get('address', '')}")
    return "\n".join(lines)


@server.tool(
    name="get_about_us_section",
    description="Банк тууралуу маалыматтын белгилүү бөлүмүн кайтарат."
)
async def get_about_us_section_tool(section: str, lang: str = "ky"):
    data = get_about_us_section(section, lang=lang)
    if isinstance(data, str) and "not found" in data:
        return data
    lines = [f"{'📋 ' + section.title() if lang == 'ky' else '📋 ' + section.title()}:\n"]
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, list):
                lines.append(f"{'🔹 ' + k.replace('_', ' ').title() if lang == 'ky' else '🔹 ' + k.replace('_', ' ').title()}:")
                lines.extend(f"  • {item}" for item in v)
            else:
                lines.append(f"{'🔹 ' + k.replace('_', ' ').title() if lang == 'ky' else '🔹 ' + k.replace('_', ' ').title()}: {v}")
    elif isinstance(data, list):
        lines.extend(f"{i}. {item}" for i, item in enumerate(data, 1))
    else:
        lines.append(str(data))
    return "\n".join(lines)


# =========================
# Депозиты
# =========================

@server.tool(
    name="list_all_deposit_names",
    description="DemirBank'тагы бардык депозиттердин тизмесин кайтарат"
)
async def list_all_deposit_names_tool(lang: str = "ky"):
    deposits = list_all_deposit_names(lang=lang)
    return f"{'💰 Бардык депозиттер' if lang == 'ky' else '💰 Все депозиты'}:\n\n" + "\n".join(f"{i}. {d['name']}" for i, d in enumerate(deposits, 1))


@server.tool(
    name="get_deposit_details",
    description="Депозит аталышы боюнча бардык негизги маалыматты кайтарат (валюта, мөөнөт, пайыздык ставка, минималдык сумма, сүрөттөмө)."
)
async def get_deposit_details_tool(deposit_name: str, lang: str = "ky"):
    d = get_deposit_details(deposit_name, lang=lang)
    if "error" in d:
        return d["error"]
    return (
        f"{'💰 ' + d['name'] if lang == 'ky' else '💰 ' + d['name']}\n\n"
        f"{'💱 Валюта' if lang == 'ky' else '💱 Валюта'}: {', '.join(d.get('currency', []))}\n"
        f"{'💵 Минималдык сумма' if lang == 'ky' else '💵 Минимальная сумма'}: {d.get('min_amount', 'белгисиз' if lang == 'ky' else 'неизвестно')}\n"
        f"{'⏰ Мөөнөт' if lang == 'ky' else '⏰ Срок'}: {d.get('term', 'белгисиз' if lang == 'ky' else 'неизвестно')}\n"
        f"{'📈 Пайыздык ставка' if lang == 'ky' else '📈 Процентная ставка'}: {d.get('rate', 'белгисиз' if lang == 'ky' else 'неизвестно')}\n"
        f"{'💸 Чыгаруу' if lang == 'ky' else '💸 Вывод'}: {d.get('withdrawal', 'белгисиз' if lang == 'ky' else 'неизвестно')}\n"
        f"{'➕ Толуктоо' if lang == 'ky' else '➕ Пополнение'}: {d.get('replenishment', 'белгисиз' if lang == 'ky' else 'неизвестно')}\n"
        f"{'📊 Капитализация' if lang == 'ky' else '📊 Капитализация'}: {d.get('capitalization', 'белгисиз' if lang == 'ky' else 'неизвестно')}\n"
        f"{'📝 Сүрөттөмө' if lang == 'ky' else '📝 Описание'}: {d.get('descr', 'белгисиз' if lang == 'ky' else 'неизвестно')}\n"
    )


@server.tool(
    name="compare_deposits",
    description="Депозиттерди негизги параметрлер боюнча салыштырат. Аргумент катары депозиттердин аттарынын тизмеси берилет (2-4 депозит)."
)
async def compare_deposits_tool(deposit_names: List[str], lang: str = "ky"):
    deposits = compare_deposits(deposit_names, lang=lang)
    if len(deposits) < 2:
        return "Депозит салыштыруу үчүн эң азы 2 депозит керек." if lang == "ky" else "Для сравнения депозитов нужно минимум 2 депозита."
    result_text = f"{'📋 Салыштырылган депозиттер' if lang == 'ky' else '📋 Сравниваемые депозиты'}:\n" + "\n".join(
        f"{i}. {d['name']}" for i, d in enumerate(deposits, 1)
    ) + "\n\n"
    all_keys = set(k for d in deposits for k in d.keys() if k != "name")
    for key in all_keys:
        vals = []
        for d in deposits:
            v = d.get(key, "белгисиз" if lang == "ky" else "неизвестно")
            if isinstance(v, list):
                v = ", ".join(v)
            elif isinstance(v, dict):
                v = json.dumps(v, ensure_ascii=False)
            vals.append(v)
        if len(set(vals)) == 1:
            result_text += f"{'✅ Бардыгы бирдей' if lang == 'ky' else '✅ Все одинаково'}: {vals[0]}\n\n"
        else:
            for i, (d, v) in enumerate(zip(deposits, vals), 1):
                result_text += f"  {i}. {d['name']}: {v}\n"
            result_text += "\n"
    return result_text


@server.tool(
    name="get_deposits_by_currency",
    description="Депозиттерди валюта боюнча фильтрлейт (KGS, USD, EUR, RUB)."
)
async def get_deposits_by_currency_tool(currency: str, lang: str = "ky"):
    deposits = get_deposits_by_currency(currency, lang=lang)
    lines = [f"{'💰 ' + currency.upper() + ' валютасындагы депозиттер' if lang == 'ky' else '💰 Депозиты в валюте ' + currency.upper()}:\n"]
    for i, d in enumerate(deposits, 1):
        lines.append(f"{i}. {d['name']}")
        lines.append(f"   {'Пайыздык ставка' if lang == 'ky' else 'Процентная ставка'}: {d.get('rate', 'белгисиз' if lang == 'ky' else 'неизвестно')}")
        lines.append(f"   {'Минималдык сумма' if lang == 'ky' else 'Минимальная сумма'}: {d.get('min_amount', 'белгисиз' if lang == 'ky' else 'неизвестно')}")
        lines.append(f"   {'Мөөнөт' if lang == 'ky' else 'Срок'}: {d.get('term', 'белгисиз' if lang == 'ky' else 'неизвестно')}\n")
    return "\n".join(lines)


@server.tool(
    name="get_deposits_by_term_range",
    description="Депозиттерди мөөнөт диапазону боюнча фильтрлейт."
)
async def get_deposits_by_term_range_tool(min_term: str = None, max_term: str = None, lang: str = "ky"):
    deposits = get_deposits_by_term_range(min_term, max_term, lang=lang)
    lines = [f"{'� VEGAS⏰ Мөөнөт боюнча депозиттер' if lang == 'ky' else '⏰ Депозиты по сроку'}:\n"]
    for i, d in enumerate(deposits, 1):
        lines.append(f"{i}. {d['name']}")
        lines.append(f"   {'Мөөнөт' if lang == 'ky' else 'Срок'}: {d.get('term', 'белгисиз' if lang == 'ky' else 'неизвестно')}")
        lines.append(f"   {'Пайыздык ставка' if lang == 'ky' else 'Процентная ставка'}: {d.get('rate', 'белгисиз' if lang == 'ky' else 'неизвестно')}\n")
    return "\n".join(lines)


@server.tool(
    name="get_deposits_by_min_amount",
    description="Депозиттерди минималдык сумма боюнча фильтрлейт."
)
async def get_deposits_by_min_amount_tool(max_amount: str, lang: str = "ky"):
    deposits = get_deposits_by_min_amount(max_amount, lang=lang)
    lines = [f"{'💵 ' + max_amount + ' чейинки минималдык суммадагы депозиттер' if lang == 'ky' else '💵 Депозиты с минимальной суммой до ' + max_amount}:\n"]
    for i, d in enumerate(deposits, 1):
        lines.append(f"{i}. {d['name']}")
        lines.append(f"   {'Минималдык сумма' if lang == 'ky' else 'Минимальная сумма'}: {d.get('min_amount', 'белгисиз' if lang == 'ky' else 'неизвестно')}")
        lines.append(f"   {'Пайыздык ставка' if lang == 'ky' else 'Процентная ставка'}: {d.get('rate', 'белгисиз' if lang == 'ky' else 'неизвестно')}\n")
    return "\n".join(lines)


@server.tool(
    name="get_deposits_by_rate_range",
    description="Депозиттерди пайыздык ставка диапазону боюнча фильтрлейт."
)
async def get_deposits_by_rate_range_tool(min_rate: str = None, max_rate: str = None, lang: str = "ky"):
    deposits = get_deposits_by_rate_range(min_rate, max_rate, lang=lang)
    lines = [f"{'📈 Пайыздык ставка боюнча депозиттер' if lang == 'ky' else '📈 Депозиты по процентной ставке'}:\n"]
    for i, d in enumerate(deposits, 1):
        lines.append(f"{i}. {d['name']}")
        lines.append(f"   {'Пайыздык ставка' if lang == 'ky' else 'Процентная ставка'}: {d.get('rate', 'белгисиз' if lang == 'ky' else 'неизвестно')}")
        lines.append(f"   {'Мөөнөт' if lang == 'ky' else 'Срок'}: {d.get('term', 'белгисиз' if lang == 'ky' else 'неизвестно')}\n")
    return "\n".join(lines)


@server.tool(
    name="get_deposits_with_replenishment",
    description="Толуктоого мүмкүндүк берген депозиттерди кайтарат."
)
async def get_deposits_with_replenishment_tool(lang: str = "ky"):
    deposits = get_deposits_with_replenishment(lang=lang)
    lines = [f"{'➕ Толуктоого мүмкүндүк берген депозиттер' if lang == 'ky' else '➕ Депозиты с возможностью пополнения'}:\n"]
    for i, d in enumerate(deposits, 1):
        lines.append(f"{i}. {d['name']}")
        lines.append(f"   {'Пайыздык ставка' if lang == 'ky' else 'Процентная ставка'}: {d.get('rate', 'белгисиз' if lang == 'ky' else 'неизвестно')}")
        lines.append(f"   {'Мөөнөт' if lang == 'ky' else 'Срок'}: {d.get('term', 'белгисиз' if lang == 'ky' else 'неизвестно')}\n")
    return "\n".join(lines)


@server.tool(
    name="get_deposits_with_capitalization",
    description="Капитализация мүмкүндүгүн берген депозиттерди кайтарат."
)
async def get_deposits_with_capitalization_tool(lang: str = "ky"):
    deposits = get_deposits_with_capitalization(lang=lang)
    lines = [f"{'📊 Капитализация мүмкүндүгүн берген депозиттер' if lang == 'ky' else '📊 Депозиты с капитализацией'}:\n"]
    for i, d in enumerate(deposits, 1):
        lines.append(f"{i}. {d['name']}")
        lines.append(f"   {'Пайыздык ставка' if lang == 'ky' else 'Процентная ставка'}: {d.get('rate', 'белгисиз' if lang == 'ky' else 'неизвестно')}")
        lines.append(f"   {'Мөөнөт' if lang == 'ky' else 'Срок'}: {d.get('term', 'белгисиз' if lang == 'ky' else 'неизвестно')}\n")
    return "\n".join(lines)


@server.tool(
    name="get_deposits_by_withdrawal_type",
    description="Депозиттерди чыгаруу түрү боюнча фильтрлейт."
)
async def get_deposits_by_withdrawal_type_tool(withdrawal_type: str, lang: str = "ky"):
    deposits = get_deposits_by_withdrawal_type(withdrawal_type, lang=lang)
    lines = [f"{'💸 ' + withdrawal_type + ' чыгаруу түрүндөгү депозиттер' if lang == 'ky' else '💸 Депозиты с типом вывода ' + withdrawal_type}:\n"]
    for i, d in enumerate(deposits, 1):
        lines.append(f"{i}. {d['name']}")
        lines.append(f"   {'Чыгаруу' if lang == 'ky' else 'Вывод'}: {d.get('withdrawal', 'белгисиз' if lang == 'ky' else 'неизвестно')}")
        lines.append(f"   {'Пайыздык ставка' if lang == 'ky' else 'Процентная ставка'}: {d.get('rate', 'белгисиз' if lang == 'ky' else 'неизвестно')}\n")
    return "\n".join(lines)


@server.tool(
    name="get_deposit_recommendations",
    description="Критерийлерге ылайык депозит сунуштарын кайтарат."
)
async def get_deposit_recommendations_tool(criteria: dict, lang: str = "ky"):
    deposits = get_deposit_recommendations(criteria, lang=lang)
    lines = [f"{'🎯 Депозит сунуштары' if lang == 'ky' else '🎯 Рекомендации депозитов'}:\n"]
    for i, d in enumerate(deposits, 1):
        lines.append(f"{i}. {d['name']}")
        lines.append(f"   {'Пайыздык ставка' if lang == 'ky' else 'Процентная ставка'}: {d.get('rate', 'белгисиз' if lang == 'ky' else 'неизвестно')}")
        lines.append(f"   {'Мөөнөт' if lang == 'ky' else 'Срок'}: {d.get('term', 'белгисиз' if lang == 'ky' else 'неизвестно')}")
        lines.append(f"   {'Минималдык сумма' if lang == 'ky' else 'Минимальная сумма'}: {d.get('min_amount', 'белгисиз' if lang == 'ky' else 'неизвестно')}")
        if 'recommendation_score' in d:
            lines.append(f"   {'Сунуштук балл' if lang == 'ky' else 'Рекомендационный балл'}: {d['recommendation_score']}")
        lines.append("")
    return "\n".join(lines)


@server.tool(
    name="get_government_securities",
    description="Мамлекеттик баалуу кагаздарды кайтарат (Treasury Bills, NBKR Notes)."
)
async def get_government_securities_tool(lang: str = "ky"):
    securities = get_government_securities(lang=lang)
    lines = [f"{'🏛️ Мамлекеттик баалуу кагаздар' if lang == 'ky' else '🏛️ Государственные ценные бумаги'}:\n"]
    for i, s in enumerate(securities, 1):
        lines.append(f"{i}. {s['name']}")
        lines.append(f"   {'Мөөнөт' if lang == 'ky' else 'Срок'}: {s.get('term', 'белгисиз' if lang == 'ky' else 'неизвестно')}")
        lines.append(f"   {'Номиналдык сумма' if lang == 'ky' else 'Номинальная сумма'}: {s.get('nominal_amount', 'белгисиз' if lang == 'ky' else 'неизвестно')}")
        lines.append(f"   {'Түрү' if lang == 'ky' else 'Тип'}: {s.get('type', 'белгисиз' if lang == 'ky' else 'неизвестно')}")
        lines.append(f"   {'Чыгаруучу' if lang == 'ky' else 'Эмитент'}: {s.get('issuer', 'белгисиз' if lang == 'ky' else 'неизвестно')}\n")
    return "\n".join(lines)


@server.tool(
    name="get_child_deposits",
    description="Балдар үчүн атайын депозиттерди кайтарат."
)
async def get_child_deposits_tool(lang: str = "ky"):
    deposits = get_child_deposits(lang=lang)
    lines = [f"{'👶 Балдар үчүн депозиттер' if lang == 'ky' else '👶 Депозиты для детей'}:\n"]
    for i, d in enumerate(deposits, 1):
        lines.append(f"{i}. {d['name']}")
        lines.append(f"   {'Пайыздык ставка' if lang == 'ky' else 'Процентная ставка'}: {d.get('rate', 'белгисиз' if lang == 'ky' else 'неизвестно')}")
        lines.append(f"   {'Мөөнөт' if lang == 'ky' else 'Срок'}: {d.get('term', 'белгисиз' if lang == 'ky' else 'неизвестно')}")
        lines.append(f"   {'Минималдык сумма' if lang == 'ky' else 'Минимальная сумма'}: {d.get('min_amount', 'белгисиз' if lang == 'ky' else 'неизвестно')}\n")
    return "\n".join(lines)


@server.tool(
    name="get_online_deposits",
    description="Онлайн ачылуучу депозиттерди кайтарат."
)
async def get_online_deposits_tool(lang: str = "ky"):
    deposits = get_online_deposits(lang=lang)
    lines = [f"{'🌐 Онлайн депозиттер' if lang == 'ky' else '🌐 Онлайн депозиты'}:\n"]
    for i, d in enumerate(deposits, 1):
        lines.append(f"{i}. {d['name']}")
        lines.append(f"   {'Пайыздык ставка' if lang == 'ky' else 'Процентная ставка'}: {d.get('rate', 'белгисиз' if lang == 'ky' else 'неизвестно')}")
        lines.append(f"   {'Мөөнөт' if lang == 'ky' else 'Срок'}: {d.get('term', 'белгисиз' if lang == 'ky' else 'неизвестно')}")
        lines.append(f"   {'Минималдык сумма' if lang == 'ky' else 'Минимальная сумма'}: {d.get('min_amount', 'белгисиз' if lang == 'ky' else 'неизвестно')}\n")
    return "\n".join(lines)


@server.tool(
    name="get_faq_by_category",
    description="Жалпы суроолорго FAQ маалыматтарын колдонуу менен жооп берет. LLM тек гана FAQ маалыматтарын колдонуу керек, жаңы маалымат ойлоп чыгарбоо керек."
)
async def get_faq_by_category_tool(category: str, question: str = None, lang: str = "ky"):
    result = get_faq_by_category(category, lang=lang)
    return " ".join(f"{'Суроо' if lang == 'ky' else 'Вопрос'}: {item['question']} {'Жооп' if lang == 'ky' else 'Ответ'}: {item['answer']} \n" for item in result)


if __name__ == "__main__":
    server.run()