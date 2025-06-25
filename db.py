import mysql.connector
import os
from flask import g
from dotenv import load_dotenv

# טוען את קובץ .env מהתיקייה הנוכחית (server/)
load_dotenv()

def get_db():
    if 'db' not in g:
        # בדיקת משתני סביבה
        host = os.environ.get("MYSQL_HOST")
        port = os.environ.get("MYSQL_PORT")
        user = os.environ.get("MYSQL_USER")
        password = os.environ.get("MYSQL_PASSWORD")
        database = os.environ.get("MYSQL_DATABASE")

        # בדיקה מוקדמת – זורק שגיאה מפורשת אם משהו חסר
        if not all([host, port, user, password, database]):
            raise ValueError("❌ אחד או יותר ממשתני הסביבה (.env) חסרים")

        g.db = mysql.connector.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database=database
        )
        g.db.autocommit = True

    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()