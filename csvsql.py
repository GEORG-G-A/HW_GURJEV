import sqlite3 as sq
import csv
import time
import argparse
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Функция для обновления базы данных
def update_database(csv_file):
    connection = sq.connect('Project_5oro4ka')
    cursor = connection.cursor()

    # Создание таблицы (если она не существует)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products_fin (
        "Product Name" TEXT,
        PLU INTEGER,
        UOM TEXT,
        Step INTEGER,
        Rating REAL,
        "Rates Count" INTEGER,
        Price REAL,
        "Property Clarification" TEXT,
        Weight REAL,
        "Nutrients Protein" REAL,
        "Nutrients Fat" REAL,
        "Nutrients Carbs" REAL,
        "Nutrients Calories" REAL,
        Score REAL
    )
    """)
    connection.commit()

    # Очистка таблицы перед вставкой новых данных (по желанию)
    cursor.execute("DELETE FROM products_fin")
    connection.commit()

    # Открытие CSV файла и вставка данных
    with open(csv_file, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)  # Чтение CSV как словаря
        for row in reader:
            try:
                # Вставка данных в таблицу с использованием позиционных плейсхолдеров
                cursor.execute("""
                INSERT INTO products_fin (
                    "Product Name", PLU, UOM, Step, Rating, "Rates Count", Price, 
                    "Property Clarification", Weight, "Nutrients Protein", 
                    "Nutrients Fat", "Nutrients Carbs", "Nutrients Calories", Score
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row["Product Name"], row["PLU"], row["UOM"], row["Step"], row["Rating"],
                    row["Rates Count"], row["Price"], row["Property Clarification"],
                    row["Weight"], row["Nutrients Protein"], row["Nutrients Fat"],
                    row["Nutrients Carbs"], row["Nutrients Calories"], row["Score"]
                ))
            except Exception as e:
                print(f"Ошибка: {e} для строки {row}")

    connection.commit()
    connection.close()
    print("База данных обновлена.")

# Класс для обработки изменений в файле
class Watcher(FileSystemEventHandler):
    def __init__(self, csv_file):
        self.csv_file = csv_file

    def on_modified(self, event):
        # Проверка, что изменился нужный CSV файл
        if event.src_path == self.csv_file:
            print(f"Файл {self.csv_file} изменен. Обновление базы данных...")
            update_database(self.csv_file)

# Функция запуска
def start_monitoring(csv_file):
    event_handler = Watcher(csv_file)
    observer = Observer()
    observer.schedule(event_handler, path=".", recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# Функция остановки наблюдения
def stop_monitoring():
    print("Остановка наблюдения...")
    exit(0)

# Обработка аргументов командной строки
parser = argparse.ArgumentParser(description="Automated database updater for CSV changes.")
parser.add_argument("action", choices=["start", "stop"], help="Action to perform: 'start' or 'stop'.")

args = parser.parse_args()

# Начало выполнения в зависимости от аргумента
if args.action == "start":
    print("Запуск наблюдения за файлом...")
    csv_file = "products_with_scores_cleaned_updated.csv"
    start_monitoring(csv_file)
elif args.action == "stop":
    stop_monitoring()
