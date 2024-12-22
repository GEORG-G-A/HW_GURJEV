import csv
import logging
import traceback
import threading


class CsvHandler:
    _lock = threading.Lock()  # Блокировка для обеспечения потокобезопасности

    @staticmethod
    def _open_file(filename, mode='r', encoding='utf-8'):
        """Helper method to open a CSV file with error handling and return file object."""
        try:
            return open(filename, mode, newline='', encoding=encoding)
        except IOError as e:
            logging.error(f"Failed to open {filename}: {e}")
            logging.debug(traceback.format_exc())
            return None

    @staticmethod
    def write_category_to_csv(categories, filename):
        """Writes category data to CSV with subcategories."""
        fieldnames = ['Category ID', 'Category', 'Subcategory ID', 'Subcategory']
        with CsvHandler._lock:  # Потокобезопасный доступ
            try:
                with CsvHandler._open_file(filename, 'w') as file:
                    if not file:
                        return

                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    writer.writeheader()
                    for category in categories:
                        for subcategory in category.get('subcategories', []):
                            writer.writerow({
                                'Category ID': category['id'],
                                'Category': category['name'],
                                'Subcategory ID': subcategory['id'],
                                'Subcategory': subcategory['name']
                            })
            except Exception as e:
                logging.error(f"Failed to write categories to CSV: {e}")
                logging.debug(traceback.format_exc())

    @staticmethod
    def read_categories_from_csv(filename):
        """Reads categories and their subcategories from a CSV file."""
        categories = []
        with CsvHandler._lock:  # Потокобезопасный доступ
            try:
                with CsvHandler._open_file(filename, 'r') as file:
                    if not file:
                        return categories

                    reader = csv.DictReader(file)
                    for row in reader:
                        category_id = row['Category ID']
                        subcategory_id = row['Subcategory ID']
                        category_name = row['Category']
                        subcategory_name = row['Subcategory']
                        subcategory_desirability = row['Desirability']

                        # Use a dictionary to quickly check if the category already exists
                        category = next(
                            (cat for cat in categories if cat['id'] == category_id),
                            None
                        )
                        if not category:
                            category = {'id': category_id, 'name': category_name, 'subcategories': []}
                            categories.append(category)

                        category['subcategories'].append(
                            {'id': subcategory_id, 'name': subcategory_name, 'desirability': subcategory_desirability}
                        )

            except Exception as e:
                logging.error(f"Failed to read categories from CSV: {e}")
                logging.debug(traceback.format_exc())

        return categories

    @staticmethod
    def write_dynamic_product_to_csv(product, filename):
        """Appends a product to the CSV file with dynamic headers."""
        with CsvHandler._lock:  # Потокобезопасный доступ
            try:
                with CsvHandler._open_file(filename, 'a') as file:
                    if not file:
                        return

                    fieldnames = list(product.keys())
                    writer = csv.DictWriter(file, fieldnames=fieldnames)

                    # Write the header only if the file is empty
                    if file.tell() == 0:
                        writer.writeheader()

                    writer.writerow(product)

            except Exception as e:
                logging.error(f"Failed to write product to CSV: {e}")
                logging.debug(traceback.format_exc())
