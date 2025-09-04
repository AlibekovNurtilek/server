import json
import os
from pathlib import Path
from datetime import datetime
from app.services.llm_services.mcp_tools import generate_function_docs
from typing import Optional
from app.db.models import Customer

KNOWLEDGE_BASE_DIR = Path(os.getenv("KNOWLEDGE_BASE_DIR", "knowledge"))

# helper: нормализуем код языка
def _norm_lang(language: str) -> str:
    return "ru" if (language or "").strip().lower() == "ru" else "ky"

# helper: загружаем шаблон промпта из JSON файла
def _load_prompt_template(prompt_name: str, language: str) -> str:
    lang = _norm_lang(language)
    file_path = KNOWLEDGE_BASE_DIR / lang / "system_prompts.json"
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
            return prompts.get(prompt_name, {}).get("template", "")
    except FileNotFoundError:
        return ""

def get_system_prompt(language: str) -> str:
    """
    Возвращает системный промпт для AiBank MCP-ассистента.
    :param language: 'ky' (кыргызский, по умолчанию) или 'ru' (русский).
    """
    global s_ky
    global s_ru
    s = s_ky if language == "ky" else s_ru
    docs = generate_function_docs(language)

    # Локальная дата/время (Бишкек)
    try:
        from zoneinfo import ZoneInfo  # Python 3.9+
        now = datetime.now(ZoneInfo("Asia/Bishkek"))
        local_dt_str = now.strftime("%Y-%m-%d %H:%M %Z")
    except Exception:
        # На всякий случай, если zoneinfo недоступен
        now = datetime.now()
        local_dt_str = now.strftime("%Y-%m-%d %H:%M")

    template = _load_prompt_template("system_prompt", language)
    return (template.format(local_dt_str=local_dt_str, docs=docs)) + s

def get_faq_system_prompt(lang: str, user: Optional[Customer], tool_response: str) -> str:
    """Generate system prompt for FAQ responses."""
    user_name = user.first_name if user else ("Колдонуучу" if lang == "ky" else "Пользователь")
    template = _load_prompt_template("faq_system_prompt", lang)
    return template.format(user_name=user_name, lang=lang, tool_response=tool_response)

def get_tool_response_system_prompt(lang: str, user: Optional[Customer], tool_response: str) -> str:
    """Generate system prompt for tool response processing."""
    user_name = user.first_name if user else ("Колдонуучу" if lang == "ky" else "Пользователь")
    template = _load_prompt_template("tool_response_system_prompt", lang)
    return template.format(user_name=user_name, lang=lang, tool_response=tool_response)



s_ky = 'Жеткиликтүү карталар тизмеси: Visa Classic Debit, Visa Gold Debit, Visa Platinum Debit, Mastercard Standard Debit, Mastercard Gold Debit, Mastercard Platinum Debit, Card Plus, Virtual Card, Visa Classic Credit, Visa Gold Credit, Visa Platinum Credit, Mastercard Standard Credit, Mastercard Gold Credit, Mastercard Platinum Credit, Elkart, Visa Campus Card, Жеткиликтүү депозиттер тизмеси: Demand Deposit, Classic Term Deposit, Replenishable Deposit, Standard Term Deposit, Online Deposit, Child Deposit, Government Treasury Bills, NBKR Notes, Жеткиликтүү насыялар тизмеси: Ар кандай максаттарга кредиттер, Онлайн кредит, Стандарттык керектөөчү кредит, Ыңгайлуу жашоо (KyrSEFF), АУЦАда билим алуу, Автокредиттер, Стандарттык автокредит, Автосалондор менен өнөктөштүк программасы алкагындагы кредиттер, Ипотека, Эркиндик турак жай комплекси, Prime Park турак жай комплекси, Орто-Сай клубдук үйү, Резиденс турак жай комплекси, Bellagio Resort, Talisman Village'
s_ru = 'Список доступных карт: Visa Classic Debit, Visa Gold Debit, Visa Platinum Debit, Mastercard Standard Debit, Mastercard Gold Debit, Mastercard Platinum Debit, Card Plus, Virtual Card, Visa Classic Credit, Visa Gold Credit, Visa Platinum Credit, Mastercard Standard Credit, Mastercard Gold Credit, Mastercard Platinum Credit, Elkart, Visa Campus Card, Список доступных депозитов: Депозит до востребования, Классический срочный депозит, Пополняемый депозит, Стандартный срочный депозит, Онлайн депозит, Детский депозит, Государственные казначейские векселя, Ноты НБКР, Список доступных кредитов: Кредиты на различные цели, Онлайн кредит, Стандартный потребительский кредит, Удобная жизнь (KyrSEFF), Образование в АУЦА, Автокредиты, Стандартный автокредит, Кредиты в рамках программы партнерства с автосалонами, Ипотека, Жилой комплекс Эркиндик, Жилой комплекс Prime Park, Клубный дом Орто-Сай, Жилой комплекс Резиденс, Bellagio Resort, Talisman Village'