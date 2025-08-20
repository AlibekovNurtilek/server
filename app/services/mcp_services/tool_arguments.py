tools_params = {
    "get_balance": ["customer_id", "lang"],
    "get_transactions": ["customer_id", "limit", "lang"],
    "transfer_money": ["customer_id", "to_account_number", "amount", "currency", "lang"],
    "get_last_incoming_transaction": ["customer_id", "lang"],
    "get_accounts_info": ["customer_id", "lang"],
    "get_incoming_sum_for_period": ["customer_id", "start_date", "end_date", "lang"],
    "get_outgoing_sum_for_period": ["customer_id", "start_date", "end_date", "lang"],
    "get_last_3_transfer_recipients": ["customer_id", "lang"],
    "get_largest_transaction": ["customer_id", "lang"],
    "list_all_card_names": ["lang"],
    "get_card_details": ["card_name", "lang"],
    "compare_cards": ["card_names", "lang"],
    "get_card_limits": ["card_name", "lang"],
    "get_card_benefits": ["card_name", "lang"],
    "get_cards_by_type": ["card_type", "lang"],
    "get_cards_by_payment_system": ["system", "lang"],
    "get_cards_by_fee_range": ["min_fee", "max_fee", "lang"],
    "get_cards_by_currency": ["currency", "lang"],
    "get_card_instructions": ["card_name", "lang"],
    "get_card_conditions": ["card_name", "lang"],
    "get_cards_with_features": ["features", "lang"],
    "get_card_recommendations": ["criteria", "lang"],
    "get_bank_info": ["lang"],
    "get_bank_mission": ["lang"],
    "get_bank_values": ["lang"],
    "get_ownership_info": ["lang"],
    "get_branch_network": ["lang"],
    "get_contact_info": ["lang"],
    "get_complete_about_us": ["lang"],
    "get_about_us_section": ["section", "lang"],
    "list_all_deposit_names": ["lang"],
    "get_deposit_details": ["deposit_name", "lang"],
    "compare_deposits": ["deposit_names", "lang"],
    "get_deposits_by_currency": ["currency", "lang"],
    "get_deposits_by_term_range": ["min_term", "max_term", "lang"],
    "get_deposits_by_min_amount": ["max_amount", "lang"],
    "get_deposits_by_rate_range": ["min_rate", "max_rate", "lang"],
    "get_deposits_with_replenishment": ["lang"],
    "get_deposits_with_capitalization": ["lang"],
    "get_deposits_by_withdrawal_type": ["withdrawal_type", "lang"],
    "get_deposit_recommendations": ["criteria", "lang"],
    "get_government_securities": ["lang"],
    "get_child_deposits": ["lang"],
    "get_online_deposits": ["lang"],
    "get_faq_by_category": ["category", "lang"]
}


def filter_tool_args(name: str, kwargs: dict) -> list:
    """
    Фильтрует входящие аргументы по списку допустимых для тула.
    Возвращает список значений в порядке, указанном в tools_params.
    """
    valid_params = tools_params.get(name, [])
    filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_params}
    # Пост-обработка: преобразование строк с запятыми в списки
    for key, value in filtered_kwargs.items():
        if isinstance(value, str) and ',' in value:
            # Разделяем строку по запятым и убираем пробелы
            filtered_kwargs[key] = [item.strip() for item in value.split(',')]
    
    return filtered_kwargs