import csv
import http.client
import logging
import os
from typing import List, Dict
from prefect import task, flow

# Helper imports
import HttpRequest
from CsvHandler import CsvHandler

# Remove any existing handlers to prevent logs from showing
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Установим уровень логирования на ERROR, чтобы исключить все менее важные сообщения
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')


def load_desirability_map(subcategory_csv: str) -> Dict[str, str]:
    """
    Загружает карту сабкатегорий и их соответствующей желательности.
    Возвращает словарь: {subcategory_id: desirability}.
    """
    desirability_map = {}
    try:
        with open(subcategory_csv, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                desirability_map[row["Subcategory ID"]] = row["Desirability"]
    except Exception as e:
        logging.error(f"Failed to read subcategories CSV: {e}")
    return desirability_map


class CsvProductManager:
    @staticmethod
    def product_exists_in_csv(plu: str, filename: str) -> bool:
        """
        Checks if a product with the given PLU exists in the CSV file.
        Returns True if exists, otherwise False.
        """
        try:
            with open(filename, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                return any(row['plu'] == str(plu) for row in reader)
        except Exception as e:
            logging.error(f"Failed to read products from CSV to check existence: {e}")
            return False


class CategoryFetcher:
    def __init__(self, connection: http.client.HTTPConnection, headers: Dict[str, str]):
        self.conn = connection
        self.headers = headers

    def fetch_categories(self, url: str) -> List[Dict]:
        """
        Makes an HTTP request to fetch categories and returns the parsed JSON response.
        """
        request = HttpRequest.HttpRequest(self.conn, self.headers)
        response_json = request.make_request(url)

        # Log the response to see its structure
        logging.debug(f"Response JSON: {response_json}")

        if response_json is None:
            return []

        # Check if the response is a list or dictionary
        if isinstance(response_json, list):
            # If it's a list, return it directly
            return response_json
        elif isinstance(response_json, dict):
            # If it's a dictionary, attempt to get the "categories" field
            return response_json.get("categories", [])
        else:
            logging.error("Unexpected response format.")
            return []


@task
def fetch_categories_to_csv(category_filename: str):
    """
    Fetches categories and writes them to the given CSV file.
    """
    connection = http.client.HTTPSConnection("5d.5ka.ru", timeout=30)
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9,ru;q=0.8',
        'cache-control': 'max-age=0',
        'cookie': '_ym_uid=173316308568681682; _ym_d=1733163085; spid=1733163085737_552f5f9dace3e0d2f95d9abb82027463_v10rr7ukjh50i01w; TS01658276=01a2d8bbf4e92763247e70599ede247df8ceec63a3a8101dec40a7890ef34238b551bd2dd4756efe3c3d7c0ac42eafd948265241a8; spsc=1734837045813_d251d973d469922bbd4353086279baca_e6cfb3ea8f0a0fa28cc6ebefdcae8ea5; SRV=cd724344-8da6-4878-8d00-1a74c6f83755; TS018c7dc5=01a2d8bbf469b5f37806429663301137caa0caf1dc42905f8c41e7f4e9b81247aba7b7b4e527a5fb7e31e370e8bb95a513ed71e621d053eac628d3953933a8baa17989feae',
        'dnt': '1',
        'priority': 'u=0, i',
        'sec-ch-ua': '"Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'x-aer-mesh': 'bx-media-kit-api:BX-79899'
    }

    # Ensure the CSV file exists by creating an empty file if it doesn't exist
    if not os.path.exists(category_filename):
        with open(category_filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['Category ID', 'Category', 'Subcategory ID', 'Subcategory'])
            writer.writeheader()

    fetcher = CategoryFetcher(connection, headers)
    url = "/api/catalog/v1/stores/Y232/categories?mode=delivery&include_subcategories=1"
    categories = fetcher.fetch_categories(url)

    if categories:
        CsvHandler.write_category_to_csv(categories, category_filename)
    else:
        logging.error(f"Failed to fetch or process categories for {category_filename}")


@task
def fetch_products_for_subcategory(subcategory_id: str, subcategory_name: str, subcategory_desirability: str,
                                   products_filename: str):
    """
    Fetches products for the given subcategory and writes them to CSV if they do not already exist.
    """
    connection = http.client.HTTPSConnection("5d.5ka.ru", timeout=30)
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9,ru;q=0.8',
        'cookie': '_ym_uid=173316308568681682; _ym_d=1733163085; spid=1733163085737_552f5f9dace3e0d2f95d9abb82027463_v10rr7ukjh50i01w; TS01658276=01a2d8bbf4e92763247e70599ede247df8ceec63a3a8101dec40a7890ef34238b551bd2dd4756efe3c3d7c0ac42eafd948265241a8; spsc=1734837045813_d251d973d469922bbd4353086279baca_e6cfb3ea8f0a0fa28cc6ebefdcae8ea5; SRV=cd724344-8da6-4878-8d00-1a74c6f83755; TS018c7dc5=01a2d8bbf469b5f37806429663301137caa0caf1dc42905f8c41e7f4e9b81247aba7b7b4e527a5fb7e31e370e8bb95a513ed71e621d053eac628d3953933a8baa17989feae',
        'dnt': '1',
        'priority': 'u=0, i',
        'sec-ch-ua': '"Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'x-aer-mesh': 'bx-media-kit-api:BX-79899'
    }

    # Ensure the CSV file exists by creating an empty file if it doesn't exist
    if not os.path.exists(products_filename):
        # Attempt to determine all possible fields from an example product
        # Fetch one product first (optional)
        request = HttpRequest.HttpRequest(connection, headers)
        url = "/api/catalog/v2/stores/Y232/products/4260436?mode=delivery&include_restrict=false"
        product_json = request.make_request(url)
        if not product_json:
            logging.error(f"Failed to fetch product example plu = 4260436.")
            return

        if product_json:
            product_json["desirability"] = subcategory_desirability
            fieldnames = product_json.keys()

        with open(products_filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()

    request = HttpRequest.HttpRequest(connection, headers)
    url = f"/api/catalog/v1/stores/Y232/categories/{subcategory_id}/products?mode=delivery&limit=200"

    products_json = request.make_request(url)
    if not products_json:
        logging.error(f"Failed to fetch products for subcategory {subcategory_name}.")
        return

    products = products_json.get('products', [])
    for product in products:
        plu = product.get('plu')
        if plu and not CsvProductManager.product_exists_in_csv(plu, products_filename):
            product_url = f"/api/catalog/v2/stores/Y232/products/{plu}?mode=delivery&include_restrict=false"
            product_json = request.make_request(product_url)
            if product_json:
                # Добавляем поле желательности
                product_json["desirability"] = subcategory_desirability
                # Записываем продукт в CSV
                CsvHandler.write_dynamic_product_to_csv(product_json, products_filename)


@flow
def process_products_flow(category_filename: str, products_filename: str):
    """
    Основной поток обработки продуктов.
    """

    categories = CsvHandler.read_categories_from_csv(category_filename)

    futures = []
    for category in categories:
        subcategories = category["subcategories"]

        # Используем .map для создания задач
        futures += fetch_products_for_subcategory.map(
            [subcategory['id'] for subcategory in subcategories],
            [subcategory['name'] for subcategory in subcategories],
            [subcategory['desirability'] for subcategory in subcategories],
            [products_filename] * len(subcategories)
        )

    # Ждем завершения всех задач
    for future in futures:
        future.wait()
