import mysql.connector

# חיבור לדאטהבייס החדש בריילווי
conn = mysql.connector.connect(
    host="maglev.proxy.rlwy.net",
    port=42451,
    user="root",
    password="tOFrlugegBNFmkSaEdAKJXJUDDMoiFfO",
    database="railway"
)

cursor = conn.cursor()

# יצירת הטבלה אם לא קיימת
cursor.execute('''
    CREATE TABLE IF NOT EXISTS ProductionPlans (
        id INT AUTO_INCREMENT PRIMARY KEY,
        date VARCHAR(255),
        quantity INT,
        status VARCHAR(255),
        notes TEXT,
        customer VARCHAR(255),
        priority VARCHAR(255),
        quality_status VARCHAR(255),
        quality_notes TEXT
    )
''')

conn.commit()
conn.close()

print("✅ ProductionPlans table created in Railway")