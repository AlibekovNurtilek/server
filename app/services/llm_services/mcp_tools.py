import json
import os
from pathlib import Path
KNOWLEDGE_BASE_DIR = Path(os.getenv("KNOWLEDGE_BASE_DIR", "knowledge"))


# helper: нормализуем код языка
def _norm_lang(language: str) -> str:
    return "ru" if (language or "").strip().lower() == "ru" else "ky"

# helper: загружаем схемы из JSON файлов
def _load_schemas(language: str):
    lang = _norm_lang(language)
    file_path = KNOWLEDGE_BASE_DIR / lang / "schemas.json"
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    
# helper: выбираем схемы по языку
def _get_schemas(language: str):
    return _load_schemas(language)

def generate_function_docs(language: str = "ky") -> str:
    """
    Возвращает человекочитаемый список функций и параметров на выбранном языке.
    language: 'ky' (по умолчанию) или 'ru'
    """
    schemas = _get_schemas(language)
    lang = _norm_lang(language)

    docs = []
    for fname, schema in schemas.items():
        doc_parts = [f"\t{fname}"]
        description = schema.get("description")
        params = schema.get("parameters", {}).get("properties", {})
        
        if description:
            doc_parts.append(f" — {description}")
        if params:
            param_list = ", ".join(params.keys())
            label_params = "Параметрлер" if lang == "ky" else "Параметры"
            doc_parts.append(f". {label_params}: {param_list}")
            
        docs.append("".join(doc_parts))
    return "\n".join(docs)

def get_allowed_params(func_name: str, language: str = "ky") -> set:
    """
    Возвращает множество допустимых имён параметров для функции на выбранном языке.
    """
    schemas = _get_schemas(language)
    schema = schemas.get(func_name, {})
    return set(schema.get("parameters", {}).get("properties", {}).keys())

def cast_param_value(param_name: str, value, func_name: str, language: str = "ky"):
    """
    Кастует значение параметра к типу, определённому в схеме выбранного языка.
    Если тип не указан или каст не удался — возвращает исходное значение.
    """
    schemas = _get_schemas(language)
    schema = schemas.get(func_name, {})
    param_schema = schema.get("parameters", {}).get("properties", {}).get(param_name, {})
    param_type = param_schema.get("type")

    if param_type == "number":
        try:
            return float(value)
        except Exception:
            return value
    if param_type == "integer":
        try:
            return int(value)
        except Exception:
            return value
    if param_type == "string":
        return str(value)
    if param_type == "array":
        # Небольшая помощь: строку с запятыми превращаем в список
        if isinstance(value, str):
            return [v.strip() for v in value.split(",")]
        return list(value) if not isinstance(value, list) else value
    if param_type == "boolean":
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "y", "да", "ооба"}
        return bool(value)

    return value

