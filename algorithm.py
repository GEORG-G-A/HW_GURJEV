import sqlite3 as sq
import random
import os
import json

# Путь к файлу сохранения данных
user_data_file = "user_data.json"

# Путь к вашей базе данных
network_db_path = r"\\Laptop-q0q1k84b\eda\Project_5oro4ka.db"
products = []

# Код получения продуктов из базы данных
try:
    # Подключение к базе данных
    connection = sq.connect(network_db_path)
    cursor = connection.cursor()

    # Получение данных из таблицы products_fin
    cursor.execute("""
        SELECT "Product Name", "Weight", "Nutrients Protein", "Nutrients Fat", "Nutrients Carbs", 
               "Nutrients Calories", "Score", "Desirability"
        FROM products_fin
        WHERE "Nutrients Protein" > 0 OR "Nutrients Fat" > 0 OR "Nutrients Carbs" > 0
    """)
    rows = cursor.fetchall()

    # Преобразуем результат в список продуктов
    products = []
    for row in rows:
        products.append({
            "Product Name": row[0],
            "Weight": float(row[1]),
            "Nutrients Protein": float(row[2]),
            "Nutrients Fat": float(row[3]),
            "Nutrients Carbs": float(row[4]),
            "Nutrients Calories": float(row[5]),
            "Score": float(row[6]),
            "Desirability": float(row[7]),
            "Category": "Mixed"  # По умолчанию устанавливаем категорию
        })

    connection.close()

except Exception as e:
    print(f"Ошибка при извлечении данных из базы: {e}")


# Функция классификации продуктов
def classify_products(products):
    for product in products:
        if product["Nutrients Protein"] > product["Nutrients Fat"] and product["Nutrients Protein"] > product["Nutrients Carbs"]:
            product["Category"] = "Protein"
        elif product["Nutrients Fat"] > product["Nutrients Protein"] and product["Nutrients Fat"] > product["Nutrients Carbs"]:
            product["Category"] = "Fat"
        elif product["Nutrients Carbs"] > product["Nutrients Protein"] and product["Nutrients Carbs"] > product["Nutrients Fat"]:
            product["Category"] = "Carbs"
        else:
            product["Category"] = "Mixed"


classify_products(products)


# Сортировка продуктов по Desirability, Score и КБЖУ
def sort_products(products):
    return sorted(
        products,
        key=lambda p: (p["Desirability"], p["Score"]),
        reverse=True
    )


products = sort_products(products)

# Загрузка сохранённых данных
def load_user_data():
    if os.path.exists(user_data_file):
        with open(user_data_file, "r") as file:
            return json.load(file)
    return None

# Сохранение данных
def save_user_data(data):
    with open(user_data_file, "w") as file:
        json.dump(data, file)

# Функция получения данных с проверкой
def input_with_validation(prompt, validation, max_attempts=3):
    attempts = 0
    while attempts < max_attempts:
        try:
            value = input(prompt).strip()
            if validation(value):
                return value
            else:
                print("Некорректный ввод. Попробуйте снова.")
        except ValueError:
            print("Некорректный ввод. Попробуйте снова.")
        attempts += 1
    print("Превышено количество попыток ввода. Перезапустите программу.")
    exit()

# Сохранение недельного меню в файл JSON
def save_weekly_menu_to_json(weekly_menu, filename="weekly_menu.json"):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(weekly_menu, file, ensure_ascii=False, indent=4)
    print(f"Weekly menu saved to {filename}.")

# Загрузка данных пользователя
user_data = load_user_data()
if user_data:
    use_saved = input_with_validation(
        "Использовать сохранённые данные? (да/нет): ",
        lambda x: x.lower() in ["да", "нет"]
    ).lower() == "да"
else:
    use_saved = False

if use_saved:
    sex = user_data["sex"]
    age = user_data["age"]
    weight = user_data["weight"]
    height = user_data["height"]
    activity_level = user_data["activity_level"]
else:
    sex = input_with_validation(
        "Ваш пол (м/ж): ",
        lambda x: x.lower() in ["м", "ж"]
    ).lower()
    age = int(input_with_validation("Ваш возраст (в годах): ", lambda x: x.isdigit() and 0 < int(x) <= 120))
    weight = float(input_with_validation("Ваш вес (в килограммах): ", lambda x: x.replace('.', '', 1).isdigit() and 0 < float(x) <= 300))
    height = float(input_with_validation("Ваш рост (в сантиметрах): ", lambda x: x.replace('.', '', 1).isdigit() and 50 <= float(x) <= 250))

    print("\nУкажите уровень активности:")
    print("1 - Минимальная (сидячий образ жизни)")
    print("2 - Низкая (легкие физические нагрузки 1-3 дня в неделю)")
    print("3 - Средняя (умеренные нагрузки 3-5 дней в неделю)")
    print("4 - Высокая (интенсивные нагрузки 6-7 дней в неделю)")
    print("5 - Очень высокая (очень интенсивные или физически тяжёлые нагрузки)")
    activity_level = int(input_with_validation(
        "Выберите уровень активности (1-5): ",
        lambda x: x.isdigit() and 1 <= int(x) <= 5
    ))

    # Сохранение данных
    user_data = {
        "sex": sex,
        "age": age,
        "weight": weight,
        "height": height,
        "activity_level": activity_level
    }
    save_user_data(user_data)

# Проверка пола и расчёт BMR (Базовый уровень метаболизма)
if sex == 'м':
    bmr = 10 * weight + 6.25 * height - 5 * age + 5
elif sex == 'ж':
    bmr = 10 * weight + 6.25 * height - 5 * age - 161
else:
    print("Некорректный ввод пола. Пожалуйста, укажите 'м' или 'ж'.")

# Множитель активности
activity_multipliers = {
    1: 1.2,  # Минимальная
    2: 1.375,  # Низкая
    3: 1.55,  # Средняя
    4: 1.725,  # Высокая
    5: 1.9   # Очень высокая
}

if activity_level not in activity_multipliers:
    print("Некорректный ввод уровня активности. Выберите число от 1 до 5.")

# Рассчёт общей потребности в калориях
total_calories = int(bmr * activity_multipliers[activity_level])

# Вывод результата
print("\nРезультат расчёта:")
print(f"С учётом вашей активности, вам требуется: {total_calories:.2f} калорий/день.")

# Указать целевые КБЖУ на день
daily_calories = total_calories
fat_range = (25, 35)  # Пределы для жиров
protein_percent = 15  # Процент от калорий для белков

daily_fat_calories = daily_calories * random.uniform(*fat_range) / 100
daily_protein_calories = daily_calories * protein_percent / 100
daily_carb_calories = daily_calories - daily_fat_calories - daily_protein_calories

daily_fat_grams = daily_fat_calories / 9
daily_protein_grams = daily_protein_calories / 4
daily_carb_grams = daily_carb_calories / 4

# Подготовка категорий
categories = {
    "Protein": [p for p in products if p["Category"] == "Protein"],
    "Fat": [p for p in products if p["Category"] == "Fat"],
    "Carbs": [p for p in products if p["Category"] == "Carbs"],
    "Mixed": [p for p in products if p["Category"] == "Mixed"]
}

# Указать целевые КБЖУ на неделю
weekly_calories = daily_calories * 7
weekly_fat_calories = daily_fat_calories * 7
weekly_protein_calories = daily_protein_calories * 7
weekly_carb_calories = daily_carb_calories * 7

weekly_fat_grams = weekly_fat_calories / 9
weekly_protein_grams = weekly_protein_calories / 4
weekly_carb_grams = weekly_carb_calories / 4

def generate_weekly_menu(categories, weekly_fat, weekly_protein, weekly_carbs):
    tolerance = 0.25  # Допустимое отклонение в 5%
    max_attempts = 10000  # Максимальное количество попыток для поиска меню

    target_fat_min = weekly_fat * (1 - tolerance)
    target_fat_max = weekly_fat * (1 + tolerance)

    target_protein_min = weekly_protein * (1 - tolerance)
    target_protein_max = weekly_protein * (1 + tolerance)

    target_carb_min = weekly_carbs * (1 - tolerance)
    target_carb_max = weekly_carbs * (1 + tolerance)

    for attempt in range(max_attempts):
        weekly_products = []
        remaining_fat = weekly_fat
        remaining_protein = weekly_protein
        remaining_carbs = weekly_carbs

        while (
            remaining_fat > 0 or remaining_protein > 0 or remaining_carbs > 0
        ):
            category = random.choice(["Fat", "Protein", "Carbs"])

            if category == "Fat" and remaining_fat > 0:
                product = random.choice(categories["Fat"])
            elif category == "Protein" and remaining_protein > 0:
                product = random.choice(categories["Protein"])
            elif category == "Carbs" and remaining_carbs > 0:
                product = random.choice(categories["Carbs"])
            else:
                continue  # Если категория не подходит, пропускаем

            portion_factor = product["Weight"] / 100

            # Корректировка шансов в зависимости от рейтинга Desirability
            desirability = product["Desirability"]
            if desirability > 7:
                weight = 1.5  # Увеличиваем вероятность выбора продуктов с высокими оценками
            elif desirability < 4:
                weight = 0.5  # Уменьшаем вероятность для продуктов с низкими оценками
            else:
                weight = 1  # Нормальный вес для продуктов с рейтингом от 4 до 7


            if random.random()< weight:
                weekly_products.append({
                   "Product Name": product["Product Name"],
                   "Portion (g/ml)": product["Weight"],
                   "Calories": product["Nutrients Calories"] * portion_factor,
                   "Protein": product["Nutrients Protein"] * portion_factor,
                   "Fat": product["Nutrients Fat"] * portion_factor,
                   "Carbs": product["Nutrients Carbs"] * portion_factor,
                   "Score": product["Score"],  # Добавление "Score"
                   "Desirability": product["Desirability"]  # Включение Desirability
            })

            remaining_fat -= product["Nutrients Fat"] * portion_factor
            remaining_protein -= product["Nutrients Protein"] * portion_factor
            remaining_carbs -= product["Nutrients Carbs"] * portion_factor

        # Проверяем итоговые значения
        total_fat = sum(item["Fat"] for item in weekly_products)
        total_protein = sum(item["Protein"] for item in weekly_products)
        total_carbs = sum(item["Carbs"] for item in weekly_products)

        if (
            target_fat_min <= total_fat <= target_fat_max and
            target_protein_min <= total_protein <= target_protein_max and
            target_carb_min <= total_carbs <= target_carb_max
        ):
            print(f"Weekly menu generated successfully in {attempt + 1} attempts!")
            print("Weekly Menu:")
            for item in weekly_products:
                print(f"- {item['Product Name']}: {item['Portion (g/ml)']:.2f}g/ml, "
                      f"Protein: {item['Protein']:.2f}g, Fat: {item['Fat']:.2f}g, Carbs: {item['Carbs']:.2f}g, "
                      f"Desirability: {item['Desirability']:.2f}")
            print()
            return weekly_products

   #print("Failed to generate a menu within the allowed attempts.")
   #return None

# Сохранение целевых значений КБЖУ
def save_daily_weekly_targets_to_json(daily_calories, daily_protein, daily_fat, daily_carbs,
                                      weekly_calories, weekly_protein, weekly_fat, weekly_carbs,
                                      filename="kbju_targets.json"):
    targets = {
        "Daily": {
            "Calories": daily_calories,
            "Protein (g)": daily_protein,
            "Fat (g)": daily_fat,
            "Carbs (g)": daily_carbs
        },
        "Weekly": {
            "Calories": weekly_calories,
            "Protein (g)": weekly_protein,
            "Fat (g)": weekly_fat,
            "Carbs (g)": weekly_carbs
        }
    }
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(targets, file, ensure_ascii=False, indent=4)
    print(f"КБЖУ цели сохранены в файл {filename}.")

# Сохранение данных о целевых значениях КБЖУ
save_daily_weekly_targets_to_json(
    daily_calories=daily_calories,
    daily_protein=daily_protein_grams,
    daily_fat=daily_fat_grams,
    daily_carbs=daily_carb_grams,
    weekly_calories=weekly_calories,
    weekly_protein=weekly_protein_grams,
    weekly_fat=weekly_fat_grams,
    weekly_carbs=weekly_carb_grams
)

# Генерация меню
weekly_menu = generate_weekly_menu(
    categories,
    weekly_fat=weekly_fat_grams,
    weekly_protein=weekly_protein_grams,
    weekly_carbs=weekly_carb_grams
)

if weekly_menu:
    # Расчет суммарных КБЖУ
    total_calories = sum(item["Calories"] for item in weekly_menu)
    total_protein = sum(item["Protein"] for item in weekly_menu)
    total_fat = sum(item["Fat"] for item in weekly_menu)
    total_carbs = sum(item["Carbs"] for item in weekly_menu)
    total_score = sum(item["Score"] for item in weekly_menu)  # Суммирование Score

    # Вывод суммарного количества КБЖУ
    print("Total Nutrients for the Week:")
    print(f"Calories: {total_calories:.2f} kcal")
    print(f"Protein: {total_protein:.2f} g")
    print(f"Fat: {total_fat:.2f} g")
    print(f"Carbs: {total_carbs:.2f} g")
    print(f"Total Score: {total_score:.2f}")

    # Если меню создано, сохраняем его
    save_weekly_menu_to_json(weekly_menu)

