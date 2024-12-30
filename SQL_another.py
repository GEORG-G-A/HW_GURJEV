import sqlite3 as sq

# Сетевой путь к базе данных
network_db_path = r"\\192.168.1.68\eda\Project_5oro4ka.db"

try:
    # Подключение к базе данных
    connection = sq.connect(network_db_path)
    cursor = connection.cursor()

    # Пример: Получение списка таблиц
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Список таблиц:", tables)

    # Пример: Извлечение данных из конкретной таблицы
    cursor.execute("SELECT * FROM products_fin LIMIT 10;")
    rows = cursor.fetchall()
    print("Данные из таблицы:", rows)

    connection.close()
except Exception as e:
    print(f"Ошибка: {e}")