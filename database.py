# twork/tdrainer/database.py
import sqlite3
import os

# --- ИЗМЕНЕНИЯ ЗДЕСЬ ---
# Определяем абсолютный путь к папке, где находится этот файл
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Создаем полный путь к файлу базы данных
DB_PATH = os.path.join(BASE_DIR, 'tdrainer.db')
# Путь к БД воркера уже был правильным, оставляем как есть
TWORKER_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tworker', 'workers.db'))

def get_withdrawal_mode() -> str:
    try:
        db_uri = f'file:{TWORKER_DB_PATH}?mode=ro'
        conn = sqlite3.connect(db_uri, uri=True)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM bot_settings WHERE key = ?", ('withdrawal_mode',))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 'auto'
    except Exception as e:
        print(f"ОШИБКА: Не удалось получить доступ к базе данных воркера: {e}. Режим по умолчанию: auto.")
        return 'auto'

def init_db():
    # Используем абсолютный путь
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE connections ADD COLUMN message_id INTEGER")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE connections ADD COLUMN bc_id TEXT")
    except sqlite3.OperationalError:
        pass

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS connections (
            mammoth_id INTEGER PRIMARY KEY,
            worker_id INTEGER,
            message_id INTEGER,
            bc_id TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_or_update_connection(mammoth_id: int, worker_id: int, message_id: int, bc_id: str):
    # Используем абсолютный путь
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO connections (mammoth_id, worker_id, message_id, bc_id) VALUES (?, ?, ?, ?)",
        (mammoth_id, worker_id, message_id, bc_id)
    )
    conn.commit()
    conn.close()

def get_connection_details(mammoth_id: int) -> tuple | None:
    # Используем абсолютный путь
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT message_id, bc_id FROM connections WHERE mammoth_id = ?", (mammoth_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def link_mammoth_to_worker(mammoth_id: int, worker_id: int) -> bool:
    # Используем абсолютный путь
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT worker_id FROM connections WHERE mammoth_id = ?", (mammoth_id,))
    result = cursor.fetchone()

    is_new = False
    if result is None:
        cursor.execute("INSERT INTO connections (mammoth_id, worker_id) VALUES (?, ?)", (mammoth_id, worker_id))
        is_new = True
    elif result[0] != worker_id:
        cursor.execute("UPDATE connections SET worker_id = ? WHERE mammoth_id = ?", (worker_id, mammoth_id))
        is_new = True

    conn.commit()
    conn.close()
    return is_new

def get_worker_id(mammoth_id: int):
    # Используем абсолютный путь
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT worker_id FROM connections WHERE mammoth_id = ?", (mammoth_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None