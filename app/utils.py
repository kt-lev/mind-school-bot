import sqlite3

conn = sqlite3.connect('db/database.db')
cursor = conn.cursor()

def is_admin(chat_id) -> bool:
    cursor.execute("SELECT tg_id FROM admins WHERE id = 1")
    admin_id = cursor.fetchone()[0]
    return chat_id == admin_id
