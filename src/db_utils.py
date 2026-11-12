import psycopg2

# ВНИМАНИЕ: Замени "твой_пароль" на свой пароль от PostgreSQL!
DB_CONFIG = {
    "dbname": "shoe_store",
    "user": "postgres",
    "password": "12345", 
    "host": "localhost",
    "port": "5432"
}

def get_connection():
    """Возвращает соединение с базой данных."""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Ошибка подключения к БД: {e}")
        return None