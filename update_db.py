from db import get_db
from app import app 

def add_columns_to_mysql():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        try:
            cursor.execute("ALTER TABLE ProductionPlans ADD COLUMN quality_status TEXT;")
            print("✅ נוספה העמודה quality_status")
        except Exception as e:
            print(f"⚠️ quality_status: {e}")

        try:
            cursor.execute("ALTER TABLE ProductionPlans ADD COLUMN quality_notes TEXT;")
            print("✅ נוספה העמודה quality_notes")
        except Exception as e:
            print(f"⚠️ quality_notes: {e}")

        

        db.commit()
        db.close()

if __name__ == '__main__':
    add_columns_to_mysql()
