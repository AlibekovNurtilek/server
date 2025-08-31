import json

# Чтение исходного JSON-файла
with open('ru/useful-info.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# Категории для обработки
categories = [
    "cards",
    "loans",
    "internet_banking",
    "deposits",
    "other",
    "taxes_fines"
]

# Добавление итеративного id для каждой пары question-answer в каждой категории
for category in categories:
    if category in data['useful-info']:
        for index, item in enumerate(data['useful-info'][category], start=1):
            # Добавление id, начиная с 1 для каждой категории
            item['id'] = index

# Сохранение обновленного JSON-файла
with open('ru/useful-info.json', 'w', encoding='utf-8') as file:
    json.dump(data, file, ensure_ascii=False, indent=2)

print("Итеративные ID успешно добавлены в JSON-файл. Новый файл сохранен как 'knowledge_base_updated.json'.")
