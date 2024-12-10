import uuid
import requests
import json
import csv
import re
import os
from datetime import datetime

CLIENT_ID = '56e50044-520d-4630-b002-5311870c278a'
SECRET = 'NTZlNTAwNDQtNTIwZC00NjMwLWIwMDItNTMxMTg3MGMyNzhhOjVkNzM3OTk3LWEyMTAtNGM4My04ZDgzLWM5MWFhODdkMjI1MA=='


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
        answer = response.json()['choices'][0]['message']['content']
    except KeyError as e:
        print(e)
    return answer


def rate_product(product_name, description):
    prompt = f"Оцени продукт по шкале от 1 до 10 по следующим критериям: полезность, частота потребления обычным человеком, натуральность. Продукт: {product_name}, описание: {description}. Верни численные оценки для каждого критерия в формате: полезность: X, частота потребления: Y, натуральность: Z. Ответа строго три числа!!! НИЧЕГО БОЛЬШЕ!"
    return prompt


def extract_and_calculate_average(rating: str):
    # Паттерн для поиска чисел
    pattern = r"\D*(\d+)\D*"  # Ищем все числа в строке, окруженные нецифровыми символами

    # Находим все числа в строке
    numbers = [int(num) for num in re.findall(pattern, rating)]

    if numbers:
        # Рассчитываем среднее
        return sum(numbers) / len(numbers)
    else:
        return None


def generate_output_filename(output_csv):
    # Проверяем, существует ли файл с таким именем
    if not os.path.exists(output_csv):
        return output_csv

    # Если файл существует, добавляем метку времени к имени файла
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    name, ext = os.path.splitext(output_csv)
    new_filename = f"{name}_{timestamp}{ext}"

    return new_filename


def process_products(input_csv, output_csv):
    # Получаем токен для работы с API
    access_token = get_access_token()

    # Генерируем имя файла, чтобы не перезаписывать существующий
    output_csv = generate_output_filename(output_csv)

    # Открываем CSV с товарами для чтения и для записи результата
    with open(input_csv, newline='', encoding='utf-8') as csvfile, \
            open(output_csv, 'w', newline='', encoding='utf-8') as outfile:

        reader = csv.DictReader(csvfile)
        fieldnames = reader.fieldnames + ['Score']  # Добавляем колонку для оценок
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)

        # Записываем заголовки в новый файл
        writer.writeheader()

        # Сохраняем уже обработанные PLU и их оценки
        processed_plu = set()

        # Обрабатываем каждый товар
        for row in reader:
            plu = row['PLU']  # Используем PLU для проверки

            # Если PLU уже обработан, пропускаем этот товар
            if plu in processed_plu:
                print(f"Продукт с PLU {plu} уже был обработан. Пропускаем.")
                writer.writerow(row)  # Записываем строку без изменений
                continue

            product_name = row['Product Name']
            description = f"Вес: {row['Weight']} г, Белки: {row['Nutrients Protein']} г, Жиры: {row['Nutrients Fat']} г, Углеводы: {row['Nutrients Carbs']} г, Калории: {row['Nutrients Calories']} ккал."

            # Получаем оценку товара
            prompt = rate_product(product_name, description)
            rating = send_prompt(prompt, access_token)

            # Извлекаем и рассчитываем среднее значение оценки
            average_rating = extract_and_calculate_average(rating)

            # Если средняя оценка валидна, добавляем её в строку
            if average_rating is not None:
                row['Score'] = round(average_rating, 2)
            else:
                row['Score'] = 'N/A'  # В случае ошибки в ответе

            # Записываем строку с результатами в новый CSV файл
            writer.writerow(row)

            # Добавляем PLU в список обработанных
            processed_plu.add(plu)

            print(f"Продукт: {product_name}")
            print(f"Оценка: {row['Score']}\n")


# Пример вызова функции с файлом товаров
process_products('products.csv', 'products_with_scores.csv')
