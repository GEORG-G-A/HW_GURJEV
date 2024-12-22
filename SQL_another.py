import sqlite3 as sq
import os

# Сетевой путь к базе данных
network_db_path = r"\\Laptop-q0q1k84b\eda\Project_5oro4ka.db"

# Проверка существования файла
if os.path.exists(network_db_path):
    print("Файл базы данных найден.")
    try:
        # Подключение к базе данных
        connection = sq.connect(network_db_path)
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        print("Список таблиц в базе данных:", cursor.fetchall())
        connection.close()
    except Exception as e:
        print(f"Ошибка подключения: {e}")
else:
    print("Файл базы данных не найден. Проверьте путь.")
