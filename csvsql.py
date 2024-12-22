import sqlite3 as sq
import csv
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Функция для обновления базы данных
def update_database(csv_file):
    connection = sq.connect('Project_5oro4ka.db')  # Добавлено расширение .db
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
        Desirability REAL,
        Score REAL
    )
    """)
    connection.commit()

    #Очистка таблицы перед вставкой новых данных (по желанию)
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
                    "Nutrients Fat", "Nutrients Carbs", "Nutrients Calories", Desirability, Score
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row["Product Name"], row["PLU"], row["UOM"], row["Step"], row["Rating"],
                    row["Rates Count"], row["Price"], row["Property Clarification"],
                    row["Weight"], row["Nutrients Protein"], row["Nutrients Fat"],
                    row["Nutrients Carbs"], row["Nutrients Calories"], row["Desirability"], row["Score"]
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
        if event.src_path.endswith(self.csv_file):
            print(f"Файл {self.csv_file} изменен. Обновление базы данных...")
            update_database(self.csv_file)

# Функция запуска наблюдения за файлом
def start_monitoring(csv_file):
    print(f"Запуск наблюдения за файлом: {csv_file}")
    update_database(csv_file)  # Первоначальное обновление базы данных

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

# Основная логика выполнения
if __name__ == "__main__":
    # Задайте имя CSV файла, который нужно использовать
    csv_file = "products_with_scores_cleaned_updated.csv"

    # Запуск обновления и наблюдения
    start_monitoring(csv_file)

