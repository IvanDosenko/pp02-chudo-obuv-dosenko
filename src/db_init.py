import psycopg2
from psycopg2 import Error
import os

# ВНИМАНИЕ: Замени "твой_пароль" на пароль от PostgreSQL, который ты вводил при установке!
DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "12345", 
    "host": "localhost",
    "port": "5432"   
}

def init_database():
    """Создает базу данных и таблицы из SQL-скриптов."""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        cursor = conn.cursor()
        
        db_name = "shoe_store"
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        if not cursor.fetchone():
            cursor.execute(f"CREATE DATABASE {db_name}")
            print(f"[OK] База данных '{db_name}' создана.")
        else:
            print(f"[OK] База данных '{db_name}' уже существует.")
            
        conn.close()

        DB_CONFIG["dbname"] = db_name
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        with open(os.path.join(base_dir, 'db', 'schema.sql'), 'r', encoding='utf-8') as f:
            cursor.execute(f.read())
        
        with open(os.path.join(base_dir, 'db', 'seed.sql'), 'r', encoding='utf-8') as f:
            cursor.execute(f.read())

        conn.commit()
        print("[OK] Таблицы созданы, тестовые данные загружены!")

    except (Exception, Error) as error:
        print(f"[ERROR] Ошибка при работе с PostgreSQL: {error}")
    finally:
        if conn is not None:
            conn.close()

if __name__ == "__main__":
    init_database()