import csv
import json
import os
import re
import uuid
from typing import Dict
import requests
from prefect import task, flow

SECRET = 'MzRmMGUyMjctNjJkYS00ZjgzLWEwNDAtMGRkZGQ3MjY3ZDI2OjZhMGZkNWIyLWIxN2MtNGQ2Yi05NWE5LWQ2ZDQwM2IyM2Q1Yg=='


@task
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


@task
def send_prompt(msg: str, access_token: str) -> str:
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


@task
def rate_product(product_name: str, description: str) -> str:
    prompt = (
        f"Оцени продукт по шкале от 1 до 10 по следующим критериям: полезность, потребность организмом, качество макронутриентов. Продукт: {product_name}, описание: {description}. Верни численные оценки для каждого критерия в формате: полезность: X, потребность организмом: Y, качество состава: Z. Ответа строго три числа!!! НИЧЕГО БОЛЬШЕ!")
    return prompt


@task
def extract_and_calculate_average(rating: str) -> float:
    pattern = r"\D*(\d+)\D*"
    numbers = [int(num) for num in re.findall(pattern, rating)]

    if numbers:
        return sum(numbers) / len(numbers)
    else:
        return None


@task
def process_product(product_name: str, description: str, access_token: str) -> str:
    prompt = rate_product(product_name, description)
    rating = send_prompt(prompt, access_token)
    average_rating = extract_and_calculate_average(rating)

    if average_rating is not None:
        return round(average_rating, 2)
    else:
        return 'N/A'


@task
def process_and_write_product_to_csv(row: Dict, product_name: str, description: str, access_token: str, output_csv: str) -> None:
    plu = row['PLU']
    processed_rating = process_product(plu, product_name, row.get('Ingredients', 'Не указаны'), description, access_token)

    row['Score'] = processed_rating
    row = {key: value for key, value in row.items() if key != 'Ingredients'}

    with open(output_csv, 'a', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=row.keys())
        writer.writerow(row)


@flow
def process_products_flow(input_csv: str, output_csv: str):
    access_token = get_access_token()

    # Ensure output CSV exists and write headers if not
    if not os.path.exists(output_csv):
        with open(output_csv, 'w', newline='', encoding='utf-8') as outfile:
            with open(input_csv, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                fieldnames = [field for field in reader.fieldnames if field != 'Ingredients'] + ['Score']
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()

    # Process products
    with open(input_csv, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        processed_plu = {row['PLU']: row['Score'] for row in csv.DictReader(open(output_csv, 'r', encoding='utf-8'))}

        futures = []
        for row in reader:
            plu = row['PLU']

            # Skip if already processed
            if plu in processed_plu and processed_plu[plu] != 'N/A' and float(processed_plu[plu]) < 10:
                continue

            product_name = row['Product Name']
            ingredients = row.get('Ingredients', 'Не указаны')
            description = (
                f"Вес: {row['Weight']} г, Белки: {row['Nutrients Protein']} г, "
                f"Жиры: {row['Nutrients Fat']} г, Углеводы: {row['Nutrients Carbs']} г, "
                f"Калории: {row['Nutrients Calories']} ккал, Ингредиенты: {ingredients}."
            )

            future = process_and_write_product_to_csv(row, product_name, description, access_token, output_csv)
            futures.append(future)

        # Wait for all futures to complete
        for future in futures:
            future.wait()
