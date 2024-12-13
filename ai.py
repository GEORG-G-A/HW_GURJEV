import uuid
import requests
import json
import csv
import re
import os
import config

SECRET = 'ZjM2YTgzNmEtMjQxYy00NTA2LWExZWEtY2EzMTMxNjE2NWQ4OjdkOGU0NTdlLTgwYzctNDJmMS1iOTY4LTNhM2NmYWE2ZjE2NQ=='


def get_access_token() -> str:
    url = 'https://ngw.devices.sberbank.ru:9443/api/v2/oauth'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': str(uuid.uuid4()),
        'Authorization': f'Basic {SECRET}'
    }
    payload = {'scope': 'GIGACHAT_API_PERS'}
    res = requests.post(url=url, headers=headers, data=payload, verify=False)
    access_token = res.json()['access_token']
    return access_token


def send_prompt(msg: str, access_token: str):
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    payload = json.dumps({
        "model": "GigaChat",
        "messages": [
            {
                "role": "user",
                "content": msg
            }
        ],
    })
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.post(url=url, headers=headers, data=payload, verify=False)

    try:
        response_data = response.json()

        if 'choices' in response_data:
            return response_data['choices'][0]['message']['content']
        else:
            print(f"Ответ не содержит 'choices': {response_data}")
            return "Ошибка: нет данных для оценки"
    except json.JSONDecodeError:
        print("Ошибка при разборе JSON-ответа")
        return "Ошибка: неверный формат ответа"
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        return f"Ошибка: {str(e)}"


def rate_product(product_name, description):
    prompt = (f"Оцени продукт по шкале от 1 до 10 по следующим критериям: полезность, потребность организмом, качество макронутриентов. Продукт: {product_name}, описание: {description}. Верни численные оценки для каждого критерия в формате: полезность: X, потребность организмом: Y, качество состава: Z. Ответа строго три числа!!! НИЧЕГО БОЛЬШЕ!")
    return prompt


def extract_and_calculate_average(rating: str):
    pattern = r"\D*(\d+)\D*"
    numbers = [int(num) for num in re.findall(pattern, rating)]

    if numbers:
        return sum(numbers) / len(numbers)
    else:
        return None


def process_products(input_csv, output_csv):
    access_token = get_access_token()

    # Создаем файл, если его нет
    if not os.path.exists(output_csv):
        with open(output_csv, 'w', newline='', encoding='utf-8') as outfile:
            with open(input_csv, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                # Записываем заголовки без Ingredients
                fieldnames = [field for field in reader.fieldnames if field != 'Ingredients'] + ['Score']
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()

    # Открываем CSV файлы для чтения и записи
    with open(input_csv, newline='', encoding='utf-8') as csvfile, \
         open(output_csv, 'r+', newline='', encoding='utf-8') as outfile:

        reader = csv.DictReader(csvfile)
        # Записываем заголовки без Ingredients
        fieldnames = [field for field in reader.fieldnames if field != 'Ingredients'] + ['Score']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)

        # Читаем существующие записи и уже обработанные PLU с оценками
        processed_plu = {row['PLU']: row['Score'] for row in csv.DictReader(open(output_csv, 'r', encoding='utf-8'))}

        outfile.seek(0, os.SEEK_END)

        # Обрабатываем товары
        for row in reader:
            plu = row['PLU']

            # Если товар уже оценен и оценка меньше 10, пропускаем
            if plu in processed_plu and processed_plu[plu] != 'N/A' and float(processed_plu[plu]) < 10:
                continue

            product_name = row['Product Name']
            # Мы игнорируем Ingredients, записываем только описание для оценки
            ingredients = row.get('Ingredients', 'Не указаны')
            description = (
                f"Вес: {row['Weight']} г, Белки: {row['Nutrients Protein']} г, "
                f"Жиры: {row['Nutrients Fat']} г, Углеводы: {row['Nutrients Carbs']} г, "
                f"Калории: {row['Nutrients Calories']} ккал, Ингредиенты: {ingredients}."
            )

            prompt = rate_product(product_name, description)
            rating = send_prompt(prompt, access_token)

            average_rating = extract_and_calculate_average(rating)

            # Если есть валидная оценка, записываем её, иначе 'N/A'
            if average_rating is not None:
                row['Score'] = round(average_rating, 2)
            else:
                row['Score'] = 'N/A'

            # Выводим строку без Ingredients
            row = {key: value for key, value in row.items() if key != 'Ingredients'}

            writer.writerow(row)
            processed_plu[plu] = row['Score']