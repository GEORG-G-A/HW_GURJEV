import http.client
import json
import time
import csv
import traceback
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class HttpRequest:
    def __init__(self, conn, headers, retries=3, delay=2, max_redirects=5):
        self.conn = conn
        self.headers = headers
        self.retries = retries
        self.delay = delay
        self.max_redirects = max_redirects
        self.cookies = {}

    def make_request(self, url):
        redirects = 0
        while redirects < self.max_redirects:
            for attempt in range(self.retries):
                try:
                    if self.cookies:
                        self.headers['Cookie'] = '; '.join([f"{key}={value}" for key, value in self.cookies.items()])

                    logging.info(f"Requesting URL: {url}")
                    self.conn.request("GET", url, '', self.headers)
                    res = self.conn.getresponse()
                    data = res.read()
                    status_code = res.status
                    reason = res.reason

                    if 200 <= status_code < 300:
                        return json.loads(data.decode("utf-8"))

                    if status_code == 504:
                        logging.warning(f"Gateway Timeout (504) on {url}. Retrying...")
                        time.sleep(self.delay)
                        self.delay *= 2
                        return

                    if status_code in (301, 302, 303, 307, 308):
                        location = res.getheader("Location")
                        if not location:
                            logging.error(f"Redirect response received, but no Location header provided for URL: {url}")
                            return None

                        self._handle_redirect(res)
                        url = location
                        redirects += 1
                        break

                    logging.error(f"HTTP Error {status_code} ({reason}) on {url}")
                    logging.debug(f"Response body: {data.decode('utf-8', errors='replace')}")

                except json.JSONDecodeError as json_err:
                    self._handle_error(f"JSON decoding error on {url} attempt {attempt + 1}: {json_err}")
                except Exception as e:
                    self._handle_error(f"Error fetching {url} on attempt {attempt + 1}: {e}")

                if attempt < self.retries - 1:
                    time.sleep(self.delay)
                    self.delay *= 2
                else:
                    self._handle_error(f"All {self.retries} attempts failed for URL: {url}")
                    return None

        logging.error(f"Too many redirects for URL: {url}")
        return None

    def _handle_redirect(self, res):
        set_cookie_header = res.getheader('set-cookie')
        if set_cookie_header:
            for cookie in set_cookie_header.split(';'):
                key_value = cookie.split('=')
                if len(key_value) == 2:
                    self.cookies[key_value[0].strip()] = key_value[1].strip()

    def _handle_error(self, message):
        logging.error(message)
        logging.debug(traceback.format_exc())


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

class CsvHandler:
    @staticmethod
    def write_category_to_csv(categories, filename='categories.csv'):
        fieldnames = ['Category ID', 'Category', 'Subcategory ID', 'Subcategory', 'Downloaded']
        try:
            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                for category in categories:
                    for subcategory in category.get('subcategories', []):
                        downloaded = 'True' if subcategory.get('downloaded', False) else 'False'
                        writer.writerow({
                            'Category ID': category['id'],
                            'Category': category['name'],
                            'Subcategory ID': subcategory['id'],
                            'Subcategory': subcategory['name'],
                            'Downloaded': downloaded
                        })
        except Exception as e:
            logging.error(f"Failed to write categories to CSV: {e}")
            logging.debug(traceback.format_exc())

    @staticmethod
    def write_row_to_csv(row, filename='products.csv'):
        fieldnames = ['Product Name', 'PLU', 'Nutrients']
        try:
            if product_exists_in_csv(row['PLU'], filename):
                logging.info(f"Product with PLU: {row['PLU']} already exists in CSV. Skipping...")
                return

            with open(filename, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                if file.tell() == 0:
                    writer.writeheader()
                writer.writerow(row)
                logging.info(f"Saved product: {row['Product Name']} (PLU: {row['PLU']}) to CSV.")
        except Exception as e:
            logging.error(f"Failed to write row to CSV: {e}")
            logging.debug(traceback.format_exc())

    @staticmethod
    def read_categories_from_csv(filename='categories.csv'):
        categories = []
        try:
            with open(filename, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    category_id = row['Category ID']
                    subcategory_id = row['Subcategory ID']
                    category_name = row['Category']
                    subcategory_name = row['Subcategory']

                    category = next((cat for cat in categories if cat['id'] == category_id), None)
                    if not category:
                        category = {'id': category_id, 'name': category_name, 'subcategories': []}
                        categories.append(category)

                    category['subcategories'].append({'id': subcategory_id, 'name': subcategory_name})

        except Exception as e:
            logging.error(f"Failed to read categories from CSV: {e}")
            logging.debug(traceback.format_exc())

        return categories

    @staticmethod
    def write_product_to_csv(product, filename='products.csv'):
        fieldnames = [
            'Product Name', 'PLU', 'UOM', 'Step', 'Property Clarification', 'Weight',
            'Nutrients Protein', 'Nutrients Fat', 'Nutrients Carbs', 'Nutrients Calories'
        ]

        try:
            if not product.get('nutrients'):
                logging.warning(f"Skipping product {product.get('name', 'Unknown Name')} due to missing nutrients.")
                return  # Пропустить продукт
            # Prepare the product data for writing
            row = {
                'Product Name': product.get('name', 'Unknown Name'),
                'PLU': product.get('plu'),
                'UOM': product.get('uom'),
                'Step': product.get('step'),
                'Property Clarification': product.get('property_clarification', ''),
                'Weight': calculate_mass(product),
                'Nutrients Protein': next((item['value'] for item in product['nutrients'] if item['text'] == 'белки'),''),
                'Nutrients Fat': next((item['value'] for item in product['nutrients'] if item['text'] == 'жиры'), ''),
                'Nutrients Carbs': next((item['value'] for item in product['nutrients'] if item['text'] == 'углеводы'),
                                        ''),
                'Nutrients Calories': next((item['value'] for item in product['nutrients'] if item['text'] == 'ккал'),
                                           '')
            }

            # Write the data to the CSV file
            with open(filename, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                if file.tell() == 0:  # Write the header only if the file is empty
                    writer.writeheader()
                writer.writerow(row)

            logging.info(f"Saved product: {product['name']} (PLU: {product['plu']}) to CSV.")

        except Exception as e:
            logging.error(f"Failed to write product {product['name']} to CSV: {e}")
            logging.debug(e)


def product_exists_in_csv(plu, filename='products.csv'):
    try:
        with open(filename, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['PLU'] == str(plu):
                    return True
    except Exception as e:
        logging.error(f"Failed to read products from CSV to check existence: {e}")
        logging.debug(traceback.format_exc())
    return False


def main():
    conn = http.client.HTTPSConnection("5d.5ka.ru", timeout=30)
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Cookie': 'SRV=cd724344-8da6-4878-8d00-1a74c6f83755; TS018c7dc5=01a2d8bbf43f22e3fce54fc3d890180844d7886df8fed2ce938af00dce4ee9cb0ef57fbd2118149df50ab7eb1a7930999fe85a4b6628b688b18856a8317de06a49752de828; spid=1733520799386_e543c3b91a10b7c053082fc3c63b0279_1rbutvtmmdxdebk6; spsc=1733536555906_02907cc99f04884d84155d42063e60d7_86072290ac14b79035acac92a3210c54'
    }

    logging.info("Fetching categories and subcategories...")
    request = HttpRequest(conn, headers)
    response_json = request.make_request("/api/catalog/v1/stores/Y232/categories?mode=delivery&include_subcategories=1")

    # if response_json is None:
    #     logging.error("Failed to fetch categories. Exiting...")
    # else:
    #     CsvHandler.write_category_to_csv(response_json)

    categories = CsvHandler.read_categories_from_csv()
    for category in categories:
        for subcategory in category['subcategories']:
            if subcategory.get('downloaded', False):
                logging.info(f"Products for subcategory {subcategory['name']} already downloaded. Skipping...")
                continue

            logging.info(f"Fetching products for subcategory: {subcategory['name']}...")
            url = f"/api/catalog/v1/stores/Y232/categories/{subcategory['id']}/products?mode=delivery&limit=200"
            products_json = request.make_request(url)

            if products_json is None:
                logging.error(f"Failed to fetch products for subcategory: {subcategory['name']}")
                continue

            products = products_json.get('products', [])
            for product in products:
                plu = product.get('plu')
                if plu:
                    if product_exists_in_csv(plu):
                        logging.info(f"Product with PLU: {plu} already exists in CSV. Skipping...")
                        continue

                    product_url = f"/api/catalog/v2/stores/Y232/products/{plu}?mode=delivery&include_restrict=false"
                    product_json = request.make_request(product_url)

                    if product_json is None:
                        logging.error(f"Failed to fetch product details for PLU: {plu}")
                        continue

                    CsvHandler.write_product_to_csv(product_json)

            subcategory['downloaded'] = True
            CsvHandler.write_category_to_csv(categories)


if __name__ == "__main__":
    main()
