import mysql.connector
import os
from flask import g
from dotenv import load_dotenv

# טוען את קובץ .env מהתיקייה הנוכחית (server/)
load_dotenv()

def get_db():
    if 'db' not in g:
        # ערכי ברירת מחדל אם .env לא נמצא
        host = os.environ.get("MYSQL_HOST", "maglev.proxy.rlwy.net")
        port = os.environ.get("MYSQL_PORT", "42451")
        user = os.environ.get("MYSQL_USER", "root")
        password = os.environ.get("MYSQL_PASSWORD", "tOFrlugegBNFmkSaEdAKJXJUDDMoiFfO")
        database = os.environ.get("MYSQL_DATABASE", "railway")

        print(f"🔌 מתחבר למסד נתונים: {host}:{port}")
        
        try:
            g.db = mysql.connector.connect(
                host=host,
                port=int(port),
                user=user,
                password=password,
                database=database,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            g.db.autocommit = True
            print("✅ חיבור למסד נתונים הצליח")
        except Exception as e:
            print(f"❌ שגיאה בחיבור למסד נתונים: {e}")
            raise

    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()