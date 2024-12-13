import ast
import csv
import logging
import re
import traceback

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_mass(product):
    uom = product.get('uom')
    step = float(product.get('step', 1))
    clarification = product.get('property_clarification', '').lower()

    mass_in_grams = -1

    # Если UOM - килограммы
    if uom == "кг":
        try:
            mass_in_grams = step * 1000
        except ValueError:
            print(f"Не удалось обработать массу для продукта: {product['name']}")

    # Если UOM - штуки
    elif uom == "шт":
        # Попробуем извлечь массу из property_clarification
        gram_match = re.search(r"(\d+)\s*г", clarification)
        kilogram_match = re.search(r"(\d+)\s*кг", clarification)
        ml_match = re.search(r"(\d+)\s*мл", clarification)
        l_match = re.search(r"(\d+)\s*л", clarification)

        if gram_match:
            mass_in_grams = float(gram_match.group(1))
        elif ml_match:
            # Предполагаем плотность воды, 1 мл = 1 г
            mass_in_grams = float(ml_match.group(1))
        elif l_match:
            # Предполагаем плотность воды, 1 мл = 1 г
            mass_in_grams = float(l_match.group(1)) * 1000
        elif kilogram_match:
            # Предполагаем плотность воды, 1 мл = 1 г
            mass_in_grams = float(kilogram_match.group(1)) * 1000

        mass_in_grams *= step

    return mass_in_grams


def save_filtered_products(input_file, output_file):
    fieldnames = [
        'Product Name', 'PLU', 'UOM', 'Step', 'Property Clarification', 'Weight',
        'Nutrients Protein', 'Nutrients Fat', 'Nutrients Carbs', 'Nutrients Calories'
    ]

    try:
        with open(input_file, mode='r', encoding='utf-8') as infile, \
             open(output_file, mode='w', newline='', encoding='utf-8') as outfile:

            reader = csv.DictReader(infile)
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)

            writer.writeheader()  # Записываем заголовок в файл

            for row in reader:
                try:
                    # Парсим nutrients из строки JSON
                    nutrients = ast.literal_eval(row.get('nutrients', '[]'))

                    # Пропускаем продукт, если nutrients пустой
                    if not nutrients:
                        continue

                    # Формируем строку для записи
                    filtered_row = {
                        'Product Name': row.get('name', 'Unknown Name'),
                        'PLU': row.get('plu'),
                        'UOM': row.get('uom'),
                        'Step': row.get('step'),
                        'Property Clarification': row.get('property_clarification', ''),
                        'Weight': calculate_mass(row),
                        'Nutrients Protein': next((item['value'] for item in nutrients if item['text'] == 'белки'), ''),
                        'Nutrients Fat': next((item['value'] for item in nutrients if item['text'] == 'жиры'), ''),
                        'Nutrients Carbs': next((item['value'] for item in nutrients if item['text'] == 'углеводы'), ''),
                        'Nutrients Calories': next((item['value'] for item in nutrients if item['text'] == 'ккал'), '')
                    }

                    writer.writerow(filtered_row)

                except Exception as product_error:
                    logging.error(f"Failed to process product {row.get('name', 'Unknown Name')}. Error: {product_error}")
                    logging.debug(traceback.format_exc())

    except Exception as e:
        logging.error(f"Failed to process file. Error: {e}")
        logging.debug(traceback.format_exc())