import csv
import random

# Чтение данных из CSV файла
file_path = "products_with_scores.csv"  # Укажите путь к вашему CSV-файлу
products = []

with open(file_path, "r", encoding="utf-8") as csv_file:
    reader = csv.DictReader(csv_file)
    for row in reader:
        if (
            float(row["Nutrients Protein"]) > 0 or
            float(row["Nutrients Fat"]) > 0 or
            float(row["Nutrients Carbs"]) > 0
        ):
            products.append({
                "Product Name": row["Product Name"],
                "Weight": float(row["Weight"]),
                "Nutrients Protein": float(row["Nutrients Protein"]),
                "Nutrients Fat": float(row["Nutrients Fat"]),
                "Nutrients Carbs": float(row["Nutrients Carbs"]),
                "Nutrients Calories": float(row["Nutrients Calories"]),
                "Score": float(row["Score"]),  # Добавление столбца "Score"
                "Category": "Mixed"  # Присвоить категорию по умолчанию
            })

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

# Количество требуемых калорий на основе антропометрических данных
print("Калькулятор калорий\nВведите свои данные для расчёта суточной калорийности.")

# Ввод данных пользователя
sex = input("Ваш пол (м/ж): ").strip().lower()
age = int(input("Ваш возраст (в годах): "))
weight = float(input("Ваш вес (в килограммах): "))
height = float(input("Ваш рост (в сантиметрах): "))

print("\nУкажите уровень активности:")
print("1 - Минимальная (сидячий образ жизни)")
print("2 - Низкая (легкие физические нагрузки 1-3 дня в неделю)")
print("3 - Средняя (умеренные нагрузки 3-5 дней в неделю)")
print("4 - Высокая (интенсивные нагрузки 6-7 дней в неделю)")
print("5 - Очень высокая (очень интенсивные или физически тяжёлые нагрузки)")

activity_level = int(input("Выберите уровень активности (1-5): "))

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

        # Случайное перемешивание продуктов в каждой категории
        for category in categories:
            random.shuffle(categories[category])

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

            weekly_products.append({
                "Product Name": product["Product Name"],
                "Portion (g/ml)": product["Weight"],
                "Calories": product["Nutrients Calories"] * portion_factor,
                "Protein": product["Nutrients Protein"] * portion_factor,
                "Fat": product["Nutrients Fat"] * portion_factor,
                "Carbs": product["Nutrients Carbs"] * portion_factor,
                "Score": product["Score"]  # Добавление "Score"
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
                      f"Protein: {item['Protein']:.2f}g, Fat: {item['Fat']:.2f}g, Carbs: {item['Carbs']:.2f}g,")
            print()
            return weekly_products

   #print("Failed to generate a menu within the allowed attempts.")
   #return None

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
