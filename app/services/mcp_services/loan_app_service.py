from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Dict, Any, Optional, Tuple, Union
import json
import logging
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from sqlalchemy import select
from .common_services import load_loans_data
from app.db.models import *

@dataclass
class LoanCriteria:
    """Критерии кредита"""
    name: str
    min_amount: Decimal
    max_amount: Decimal
    min_term: int
    max_term: int
    interest_rate: Decimal
    collateral_required: str
    own_contribution_percent: Decimal = Decimal("0")
    effective_rate: str = ""
    commission: str = ""
    processing_time: str = ""
    disbursement: str = ""
    purpose: str = ""
    
    def validate_amount(self, amount: Decimal) -> bool:
        return self.min_amount <= amount <= self.max_amount
    
    def validate_term(self, term: int) -> bool:
        return self.min_term <= term <= self.max_term

def find_loan_criteria(loan_name: str, lang: str = "ky") -> Optional[LoanCriteria]:
    """
    Поиск критериев кредита по названию во всех возможных местах JSON
    """
    loans_data = load_loans_data(lang)
    
    if not loans_data:
        return None
    
    # Поиск во всех разделах
    for loan_category in loans_data:
        # 1. Проверяем основное название категории
        if loan_category.get("name") == loan_name:
            return _create_default_criteria_for_category(loan_category)
        
        # 2. Проверяем подкategории
        subcategories = loan_category.get("subcategories", [])
        for sub in subcategories:
            if sub.get("name") == loan_name:
                return _parse_subcategory_criteria(sub, loan_category)
        
        # 3. Проверяем специальные программы
        special_programs = loan_category.get("special_programs", [])
        for special in special_programs:
            if special.get("name") == loan_name:
                return _parse_special_program_criteria(special, loan_category)
        
        # 4. Проверяем специальные предложения (для ипотеки)
        special_offers = loan_category.get("special_offers", {})
        for region, offers in special_offers.items():
            if isinstance(offers, list):
                for offer in offers:
                    if offer.get("name") == loan_name:
                        return _parse_special_offer_criteria(offer, loan_category)
    
    return None

def _create_default_criteria_for_category(category: Dict[str, Any]) -> LoanCriteria:
    """Создание критериев по умолчанию для категории"""
    name = category.get("name", "")
    
    # Базовые значения по умолчанию
    if "автокредит" in name.lower() or "auto" in name.lower():
        return LoanCriteria(
            name=name,
            min_amount=Decimal("50000"),
            max_amount=Decimal("10000000"),
            min_term=6,
            max_term=60,
            interest_rate=Decimal("22"),
            collateral_required="автоунаа кепилдиги + 1 кепил берүүчү",
            own_contribution_percent=Decimal("30")
        )
    elif "ипотека" in name.lower() or "mortgage" in name.lower():
        return LoanCriteria(
            name=name,
            min_amount=Decimal("500000"),
            max_amount=Decimal("15000000"),
            min_term=60,
            max_term=240,
            interest_rate=Decimal("14"),
            collateral_required="кыймылсыз мүлк кепилдиги",
            own_contribution_percent=Decimal("20")
        )
    else:  # Потребительские кредиты
        return LoanCriteria(
            name=name,
            min_amount=Decimal("15000"),
            max_amount=Decimal("500000"),
            min_term=3,
            max_term=36,
            interest_rate=Decimal("23"),
            collateral_required="кепил берүүчүсүз (300,000 сомго чейин)"
        )

def _parse_subcategory_criteria(sub: Dict[str, Any], category: Dict[str, Any]) -> LoanCriteria:
    """Парсинг критериев из подкатегории"""
    name = sub.get("name", "")
    
    # Парсинг суммы
    amount_str = sub.get("amount", "")
    min_amount, max_amount = _parse_amount_range(amount_str)
    
    # Парсинг срока
    term_str = sub.get("term", "")
    min_term, max_term = _parse_term_range(term_str)
    
    # Парсинг процентной ставки
    rate = _parse_rate(sub.get("rate") or sub.get("rates", {}))
    
    # Определение залога
    collateral = _determine_collateral(sub, min_amount)
    
    # Собственный взнос
    own_funds = sub.get("own_funds")
    own_contribution = Decimal("0")
    if own_funds:
        if isinstance(own_funds, str) and "%" in own_funds:
            own_contribution = Decimal(own_funds.replace("%", "")) / 100
        elif isinstance(own_funds, dict):
            # Для автокредитов
            if "new_car" in own_funds:
                own_contribution = Decimal(str(own_funds["new_car"]).replace("%", "")) / 100
    
    return LoanCriteria(
        name=name,
        min_amount=min_amount,
        max_amount=max_amount,
        min_term=min_term,
        max_term=max_term,
        interest_rate=rate,
        collateral_required=collateral,
        own_contribution_percent=own_contribution,
        effective_rate=sub.get("effective_rate", ""),
        commission=sub.get("commission", ""),
        processing_time=sub.get("processing", ""),
        disbursement=sub.get("disbursement", ""),
        purpose=sub.get("purpose", "")
    )

def _parse_special_program_criteria(special: Dict[str, Any], category: Dict[str, Any]) -> LoanCriteria:
    """Парсинг критериев из специальной программы"""
    name = special.get("name", "")
    
    # Парсинг суммы
    amount_str = special.get("amount", "")
    min_amount, max_amount = _parse_amount_range(amount_str)
    
    # Парсинг срока
    term_str = special.get("term", "")
    min_term, max_term = _parse_term_range(term_str)
    
    # Парсинг процентной ставки для специальных программ
    rates = special.get("rates", {})
    rate = Decimal("25")  # По умолчанию
    
    if isinstance(rates, dict):
        if "payroll" in rates:
            payroll_rates = rates["payroll"]
            if isinstance(payroll_rates, list) and payroll_rates:
                rate = Decimal(str(payroll_rates[0].get("rate", "25")).replace("%", ""))
    
    # Определение залога для специальных программ
    collateral_info = special.get("collateral", {})
    collateral = "кепил берүүчү керек"
    
    if isinstance(collateral_info, dict):
        if "payroll" in collateral_info:
            collateral = "кепил берүүчү талап кылынат"
    elif isinstance(collateral_info, list) and collateral_info:
        first_collateral = collateral_info[0]
        collateral = f"{first_collateral.get('payroll', 'кепил берүүчү керек')}"
    
    return LoanCriteria(
        name=name,
        min_amount=min_amount,
        max_amount=max_amount,
        min_term=min_term,
        max_term=max_term,
        interest_rate=rate,
        collateral_required=collateral,
        purpose=special.get("purpose", ""),
        effective_rate=special.get("effective_rate", "")
    )

def _parse_special_offer_criteria(offer: Dict[str, Any], category: Dict[str, Any]) -> LoanCriteria:
    """Парсинг критериев из специального предложения"""
    name = offer.get("name", "")
    term_str = offer.get("term", "8 жылга чейин")
    rate_str = offer.get("rate", "14%")
    
    # Парсинг срока
    max_years = 8
    if "жылга чейин" in term_str:
        try:
            max_years = int(term_str.split()[0])
        except:
            max_years = 8
    
    # Парсинг ставки
    rate = Decimal("14")
    if "%" in rate_str:
        try:
            rate = Decimal(rate_str.replace("%дан", "").replace("%", ""))
        except:
            rate = Decimal("14")
    
    return LoanCriteria(
        name=name,
        min_amount=Decimal("500000"),  # Базовые значения для ипотеки
        max_amount=Decimal("15000000"),
        min_term=60,
        max_term=max_years * 12,
        interest_rate=rate,
        collateral_required="кыймылсыз мүлк кепилдиги",
        own_contribution_percent=Decimal("20"),
        purpose="турак жай сатып алуу"
    )

def _parse_amount_range(amount_str: str) -> Tuple[Decimal, Decimal]:
    """Парсинг диапазона сумм"""
    if not amount_str:
        return Decimal("15000"), Decimal("500000")
    
    # Удаляем валюту и лишние символы
    clean_str = amount_str.lower().replace("сом", "").replace("$", "").replace(",", "").strip()
    
    if " - " in clean_str:
        parts = clean_str.split(" - ")
        try:
            min_amount = Decimal(parts[0].strip())
            max_part = parts[1].strip()
            if "го чейин" in max_part:
                max_amount = Decimal(max_part.replace("го чейин", "").strip())
            else:
                max_amount = Decimal(max_part)
            return min_amount, max_amount
        except:
            pass
    elif "го чейин" in clean_str:
        try:
            max_amount = Decimal(clean_str.replace("го чейин", "").strip())
            return Decimal("15000"), max_amount
        except:
            pass
    elif "дон" in clean_str or "дан" in clean_str:
        try:
            min_amount = Decimal(clean_str.replace("дон", "").replace("дан", "").strip())
            return min_amount, Decimal("10000000")
        except:
            pass
    
    # По умолчанию
    return Decimal("15000"), Decimal("500000")

def _parse_term_range(term_str: str) -> Tuple[int, int]:
    """Парсинг диапазона сроков"""
    if not term_str:
        return 6, 36
    
    # Очищаем строку
    clean_str = term_str.lower().strip()
    
    # Обрабатываем различные форматы сроков
    if " - " in clean_str:
        parts = clean_str.split(" - ")
        try:
            min_part = parts[0].strip()
            max_part = parts[1].strip()
            
            # Парсим минимальный срок
            min_term = _extract_number_from_term(min_part)
            
            # Парсим максимальный срок
            max_term = _extract_number_from_term(max_part)
            
            # Конвертируем годы в месяцы
            if "жыл" in max_part:
                max_term *= 12
            if "жыл" in min_part:
                min_term *= 12
                
            return min_term, max_term
        except:
            pass
    elif "-" in clean_str and not "дан" in clean_str:
        parts = clean_str.split("-")
        try:
            min_term = _extract_number_from_term(parts[0].strip())
            max_term = _extract_number_from_term(parts[1].strip())
            
            # Конвертируем годы в месяцы если нужно
            if "жыл" in parts[1]:
                max_term *= 12
            if "жыл" in parts[0]:
                min_term *= 12
                
            return min_term, max_term
        except:
            pass
    elif "дан баштап" in clean_str:
        try:
            min_term = _extract_number_from_term(clean_str.replace("дан баштап", "").strip())
            if "жыл" in clean_str:
                min_term *= 12
                return min_term, 240  # максимум 20 лет
            return min_term, 60
        except:
            pass
    elif "го чейин" in clean_str or "га чейин" in clean_str:
        try:
            max_term = _extract_number_from_term(clean_str.replace("го чейин", "").replace("га чейин", "").strip())
            if "жыл" in clean_str:
                max_term *= 12
                return 60, max_term  # минимум 5 лет для долгосрочных кредитов
            return 3, max_term
        except:
            pass
    elif "жыл" in clean_str:
        try:
            # Формат типа "5-20 жыл" или "8 жыл"
            numbers = []
            words = clean_str.split()
            for word in words:
                if word.replace("-", "").isdigit():
                    if "-" in word:
                        parts = word.split("-")
                        numbers.extend([int(p) for p in parts])
                    else:
                        numbers.append(int(word))
            
            if len(numbers) >= 2:
                return numbers[0] * 12, numbers[1] * 12
            elif len(numbers) == 1:
                return 60, numbers[0] * 12
        except:
            pass
    
    # По умолчанию
    return 6, 36

async def create_loan_application_improved(
    session: AsyncSession,
    customer_id: int,
    loan_name: str,
    amount: Union[Decimal, int, str, None] = None,
    term: Optional[int] = None,
    *,
    lang: str = "ky"
) -> Tuple[bool, str]:
    """
    Улучшенная функция создания заявки на кредит с валидацией из JSON
    """
    # Находим критерии кредита
    criteria = find_loan_criteria(loan_name, lang)
    if not criteria:
        return False, _t(lang, "loan_not_found", loan_name=loan_name)

    # Установка значений по умолчанию для amount и term, если они не указаны
    amount_decimal = criteria.min_amount
    term_value = criteria.min_term

    # Если сумма указана, конвертируем и валидируем
    if amount is not None:
        try:
            amount_decimal = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except (InvalidOperation, ValueError):
            return False, _t(lang, "wrong_amount")
        
        # Валидация суммы
        if not criteria.validate_amount(amount_decimal):
            return False, _t(lang, "amount_validation_error", 
                            loan_name=loan_name,
                            min_amount=f"{criteria.min_amount:,.0f}",
                            max_amount=f"{criteria.max_amount:,.0f}")

    # Если срок указан, валидируем
    if term is not None:
        term_value = term
        # Валидация срока
        if not criteria.validate_term(term_value):
            return False, _t(lang, "term_validation_error",
                            loan_name=loan_name,
                            min_term=str(criteria.min_term),
                            max_term=str(criteria.max_term))

    # Проверяем существование клиента
    customer = await session.get(Customer, customer_id)
    if not customer:
        return False, _t(lang, "user_not_found")

    # Расчет собственного взноса
    own_contribution = amount_decimal * (criteria.own_contribution_percent / 100) if criteria.own_contribution_percent > 0 else Decimal("0")

    # Определение залога на основе суммы и критериев
    collateral = criteria.collateral_required
    
    # Дополнительная логика для определения залога на основе суммы
    if "кепилсиз" in criteria.collateral_required or "документсиз" in criteria.collateral_required:
        collateral = _t(lang, "no_collateral")
    elif amount_decimal <= 300000 and "кепил берүүчүсүз" in criteria.collateral_required:
        collateral = _t(lang, "no_guarantor")
    elif amount_decimal > 500000:
        if "автоунаа" in criteria.collateral_required.lower():
            collateral = _t(lang, "car_collateral_guarantor")
        elif "мүлк" in criteria.collateral_required.lower():
            collateral = _t(lang, "property_collateral_guarantor")
        else:
            collateral = _t(lang, "property_collateral_guarantor")
    else:
        collateral = _t(lang, "one_guarantor")

    # Создаем заявку
    try:
        application = LoanApplication(
            customer_id=customer_id,
            loan_type=loan_name,  # Используем название как тип
            amount=amount_decimal,
            term_months=term_value,
            interest_rate=criteria.interest_rate,
            own_contribution=own_contribution,
            collateral=collateral,
            status=LoanApplicationStatus.pending
        )
        
        session.add(application)
        await session.flush()
        
        # Генерируем ID заявки
        application_id = f"#{application.id:04d}"
        
        return True, _t(lang, "application_success",
                       loan_name=loan_name,
                       application_id=application_id,
                       amount=f"{amount_decimal:,.0f}",
                       term=str(term_value),
                       interest_rate=str(criteria.interest_rate),
                       own_contribution=f"{own_contribution:,.0f}",
                       collateral=collateral)
                    
    except Exception as e:
        logging.error(f"Error creating loan application: {e}")
        return False, _t(lang, "application_error")

# Расширенная функция перевода с поддержкой параметров
def _t(lang: str, key: str, **kwargs) -> str:
    """Функция перевода с поддержкой параметров"""
    translations = {
        "ky": {
            "wrong_amount": "Туура эмес сумма",
            "user_not_found": "Колдонуучу табылган жок",
            "loan_not_found": "'{loan_name}' кредити системада табылган жок",
            "amount_validation_error": "'{loan_name}' кредити үчүн сумма {min_amount} сомдон {max_amount} сомго чейин болушу керек",
            "term_validation_error": "'{loan_name}' кредити үчүн мөөнөт {min_term} айдан {max_term} айга чейин болушу керек",
            "no_collateral": "кепилсиз",
            "no_guarantor": "кепил берүүчүсүз",
            "car_collateral_guarantor": "автоунаа кепилдиги + 1 кепил берүүчү",
            "property_collateral_guarantor": "кыймылсыз мүлк кепилдиги + 1 кепил берүүчү",
            "one_guarantor": "1 кепил берүүчү",
            "application_success": "'{loan_name}' кредитине арыз ийгиликтүү түзүлдү!\nАрыздын ID: {application_id}\nСумма: {amount} сом\nМөөнөт: {term} ай\nПайыздык ылдамдык: {interest_rate}%\nӨз салымы: {own_contribution} сом\nКепилдик: {collateral}",
            "application_error": "Арыз түзүүдө ката кетти. Кийинчерээк аракет кылыңыз",
        },
        "ru": {
            "wrong_amount": "Неверная сумма",
            "user_not_found": "Пользователь не найден",
            "loan_not_found": "Кредит '{loan_name}' не найден в системе",
            "amount_validation_error": "Для кредита '{loan_name}' сумма должна быть от {min_amount} до {max_amount} сом",
            "term_validation_error": "Для кредита '{loan_name}' срок должен быть от {min_term} до {max_term} месяцев",
            "no_collateral": "без залога",
            "no_guarantor": "без поручителя",
            "car_collateral_guarantor": "залог автомобиля + 1 поручитель",
            "property_collateral_guarantor": "залог недвижимости + 1 поручитель",
            "one_guarantor": "1 поручитель",
            "application_success": "Ваша заявка на кредит '{loan_name}' успешно оформлена!\nID заявки: {application_id}\nСумма: {amount} сом\nСрок: {term} месяцев\nПроцентная ставка: {interest_rate}%\nСобственный взнос: {own_contribution} сом\nЗалог: {collateral}",
            "application_error": "Ошибка при создании заявки. Попробуйте позже",
        }
    }
    
    lang_dict = translations.get(lang, translations["ky"])
    template = lang_dict.get(key, key)
    
    # Подставляем параметры
    try:
        return template.format(**kwargs)
    except KeyError:
        return template

def _parse_rate(rate_data) -> Decimal:
    """Парсинг процентной ставки"""
    if isinstance(rate_data, str):
        return Decimal(rate_data.replace("%", ""))
    elif isinstance(rate_data, dict):
        # Берем первую доступную ставку
        if "payroll" in rate_data:
            payroll = rate_data["payroll"]
            if isinstance(payroll, list) and payroll:
                return Decimal(str(payroll[0].get("rate", "25")).replace("%", ""))
            elif isinstance(payroll, str):
                return Decimal(payroll.replace("%", ""))
        elif "non_payroll" in rate_data:
            return Decimal(str(rate_data["non_payroll"]).replace("%", ""))
        elif "KGS" in rate_data:
            return Decimal(str(rate_data["KGS"]).replace("%", ""))
    
    return Decimal("25")  # По умолчанию

def _determine_collateral(sub: Dict[str, Any], amount: Decimal) -> str:
    """Определение требований к залогу"""
    collateral_data = sub.get("collateral")
    
    if isinstance(collateral_data, str):
        return collateral_data
    elif isinstance(collateral_data, list):
        # Найти подходящий диапазон
        for tier in collateral_data:
            amount_range = tier.get("amount", "")
            if _amount_in_range(amount, amount_range):
                return tier.get("payroll", tier.get("requirement", "кепил берүүчү керек"))
    
    # Определение по сумме
    if amount <= 100000:
        return "кепилсиз"
    elif amount <= 300000:
        return "кепил берүүчүсүз"
    elif amount <= 500000:
        return "1 кепил берүүчү"
    else:
        return "мүлк кепилдиги + 1 кепил берүүчү"

def _amount_in_range(amount: Decimal, range_str: str) -> bool:
    """Проверка, входит ли сумма в диапазон"""
    if not range_str:
        return True
    
    # Парсинг диапазонов типа "300,001-500,000 сом"
    if "-" in range_str and "сом" in range_str:
        try:
            parts = range_str.replace("сом", "").replace(",", "").strip().split("-")
            min_val = Decimal(parts[0].strip())
            max_val = Decimal(parts[1].strip())
            return min_val <= amount <= max_val
        except:
            return True
    
    # Парсинг типа "300,000 сомго чейин"
    if "го чейин" in range_str:
        try:
            max_val = Decimal(range_str.replace("сом", "").replace("го чейин", "").replace(",", "").strip())
            return amount <= max_val
        except:
            return True
    
    # Парсинг типа "300,001 сомдон"
    if "дон" in range_str or "дан" in range_str:
        try:
            min_val = Decimal(range_str.replace("сом", "").replace("дон", "").replace("дан", "").replace(",", "").strip())
            return amount >= min_val
        except:
            return True
    
    return True

def _extract_number_from_term(term_str: str) -> int:
    """Извлечение числа из строки срока"""
    import re
    numbers = re.findall(r'\d+', term_str)
    if numbers:
        return int(numbers[0])
    return 6




async def check_loan_application_status(
    session: AsyncSession,
    customer_id: int,
    application_id: int,
    lang: str = "ky",
) -> tuple[bool, str]:
    """
    Проверяет состояние заявки на кредит и возвращает всю информацию о ней.

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
            "loan_type": "Кредит түрү",
            "amount": "Сумма",
            "term_months": "Мөөнөтү (айлар)",
            "interest_rate": "Пайыздык чен",
            "own_contribution": "Өз салымы",
            "collateral": "Күрөө",
            "created_at": "Түзүлгөн датасы",
            "application_info": "Кредиттик заявка маалыматы",
            "status_pending": "Күтүүдө",
            "status_approved": "Жактырылды",
            "status_rejected": "Четке кагылды",
            "status_processing": "Иштетилүүдө",
            "none": "Жок",
        },
        "ru": {
            "application_not_found": "Заявка не найдена",
            "access_denied": "Заявка не найдена",
            "status": "Статус",
            "loan_type": "Тип кредита",
            "amount": "Сумма",
            "term_months": "Срок (месяцы)",
            "interest_rate": "Процентная ставка",
            "own_contribution": "Собственный взнос",
            "collateral": "Залог",
            "created_at": "Дата создания",
            "application_info": "Информация о кредитной заявке",
            "status_pending": "В ожидании",
            "status_approved": "Одобрена",
            "status_rejected": "Отклонена",
            "status_processing": "В обработке",
            "none": "Отсутствует",
        }
    }

    # Find the application
    stmt = select(LoanApplication).where(
        LoanApplication.id == application_id
    )
    application = await session.scalar(stmt)

    if not application:
        return False, translations[lang]["application_not_found"]

    # Check if the application belongs to the customer
    if application.customer_id != customer_id:
        return False, translations[lang]["access_denied"]

    # Map status to translated text
    status_map = {
        LoanApplicationStatus.pending: translations[lang]["status_pending"],
        LoanApplicationStatus.approved: translations[lang]["status_approved"],
        LoanApplicationStatus.rejected: translations[lang]["status_rejected"],
        LoanApplicationStatus.processing: translations[lang]["status_processing"],
    }

    # Prepare response message with all info
    details = [
        f"{translations[lang]['application_info']} #{application.id:04d}",
        f"{translations[lang]['loan_type']}: {application.loan_type}",
        f"{translations[lang]['amount']}: {application.amount}",
        f"{translations[lang]['term_months']}: {application.term_months}",
        f"{translations[lang]['interest_rate']}: {application.interest_rate}%",
        f"{translations[lang]['own_contribution']}: {application.own_contribution if application.own_contribution is not None else translations[lang]['none']}",
        f"{translations[lang]['collateral']}: {application.collateral if application.collateral else translations[lang]['none']}",
        f"{translations[lang]['status']}: {status_map[application.status]}",
        f"{translations[lang]['created_at']}: {application.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
    ]

    message = "\n".join(details)
    return True, message