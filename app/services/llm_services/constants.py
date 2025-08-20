"""Constants for LLM services."""

import re

# Regular expressions for function parsing
FUNC_RE = re.compile(r"^name=(?P<name>[^,]+)(?:\s*,\s*(?P<args>.*))?$", re.DOTALL)
ARG_RE = re.compile(r"\s*(?P<k>\w+)\s*=\s*(?P<v>.+?)\s*(?=,\s*\w+=|$)")
FUNC_CALL_PATTERN = re.compile(r"\[FUNC_CALL:(.*?)\]", re.DOTALL)

# Restricted functions that require authorization
RESTRICTED_FUNCTIONS = [
    "get_balance",
    "get_transactions", 
    "transfer_money",
    "get_last_incoming_transaction",
    "get_accounts_info",
    "get_incoming_sum_for_period",
    "get_outgoing_sum_for_period",
    "get_last_3_transfer_recipients",
    "get_largest_transaction",
]

# Error messages
ERROR_MESSAGES = {
    "ky": "Кечиресиз, бул суроонузга жооп алуу учун системага кириниз (авторизация).",
    "ru": "Извините, для ответа на этот запрос необходимо войти в систему (авторизация).",
}