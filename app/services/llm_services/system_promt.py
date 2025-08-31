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
    return template.format(local_dt_str=local_dt_str, docs=docs)

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