from flask import Blueprint, render_template, session, redirect, url_for
from db import get_db

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/main-dashboard')
def main_dashboard():
    if session.get('role') not in ['admin', 'operator']:
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)  # ✅ מאפשר קבלת מילונים

    # סך הכול הזמנות ייצור
    cursor.execute('SELECT COUNT(*) AS count FROM ProductionPlans')
    total_orders = cursor.fetchone()['count']

    # הזמנות פעילות (נניח שהן בסטטוס "בייצור")
    cursor.execute('''
        SELECT COUNT(*) AS count FROM ProductionPlans
        WHERE status = 'בייצור'
    ''')
    active_orders = cursor.fetchone()['count']

    # בדיקות איכות שבוצעו בפועל
    cursor.execute('''
        SELECT COUNT(*) AS count FROM ProductionPlans
        WHERE quality_status IS NOT NULL
    ''')
    quality_checks = cursor.fetchone()['count']

    # כמות שממתינות לבקרת איכות
    cursor.execute("SELECT COUNT(*) AS count FROM ProductionPlans WHERE status = 'ממתין לבקרת איכות'")
    pending_quality = cursor.fetchone()['count']

    # אחוז כשל
    cursor.execute('''
        SELECT COUNT(*) AS count FROM ProductionPlans
        WHERE quality_status = 'נכשל'
    ''')
    failed_checks = cursor.fetchone()['count']
    fail_rate = (failed_checks / quality_checks * 100) if quality_checks else 0

    # התפלגות בקרת איכות (עוגה)
    cursor.execute('''
        SELECT quality_status, COUNT(*) as count FROM ProductionPlans
        WHERE quality_status IS NOT NULL
        GROUP BY quality_status
    ''')
    dist_results = cursor.fetchall()
    quality_labels = [row['quality_status'] for row in dist_results if row['quality_status'] is not None]
    quality_values = [row['count'] for row in dist_results if row['count'] is not None]

    # התפלגות לפי תאריכים (עמודות)
    cursor.execute('''
        SELECT date, COUNT(*) as total FROM ProductionPlans
        GROUP BY date
        ORDER BY date DESC
        LIMIT 7
    ''')
    bar_results = cursor.fetchall()
    bar_labels = [row['date'] for row in reversed(bar_results) if row['date'] is not None]
    bar_values = [row['total'] for row in reversed(bar_results) if row['total'] is not None]

    return render_template("main_dashboard.html",
                           total_orders=total_orders,
                           active_orders=active_orders,
                           quality_checks=quality_checks,
                           pending_quality=pending_quality,
                           fail_rate=round(fail_rate, 1),
                           quality_labels=quality_labels or [],
                           quality_values=quality_values or [],
                           bar_labels=bar_labels or [],
                           bar_values=bar_values or [])