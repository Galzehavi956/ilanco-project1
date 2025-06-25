from flask import Blueprint, request, jsonify, render_template, make_response, session, redirect, url_for, send_file
from db import get_db
from datetime import datetime
from io import BytesIO
import openpyxl

production_bp = Blueprint('production', __name__, url_prefix='/api/production')

# שליפה של כל תוכניות הייצור
@production_bp.route('/', methods=['GET'])
def get_all_plans():
    cursor = get_db().cursor(dictionary=True)
    cursor.execute("SELECT * FROM ProductionPlans ORDER BY id DESC")
    rows = cursor.fetchall()
    return jsonify(rows)

# יצירת תוכנית ייצור חדשה
@production_bp.route('/', methods=['POST'])
def create_plan():
    data = request.get_json()
    required_fields = ['date', 'quantity', 'status', 'notes', 'customer', 'priority']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing one or more required fields'}), 400

    try:
        datetime.strptime(data['date'], '%Y-%m-%d')
        quantity = int(data['quantity'])
        if quantity <= 0:
            raise ValueError
    except:
        return jsonify({'error': 'Invalid date or quantity'}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO ProductionPlans (date, quantity, status, notes, customer, priority)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (
        data['date'],
        data['quantity'],
        data['status'],
        data['notes'],
        data['customer'],
        data['priority']
    ))
    db.commit()
    return jsonify({'message': 'Production plan created successfully'}), 201

@production_bp.route('/export-excel')
def export_excel():
    cursor = get_db().cursor(dictionary=True)
    cursor.execute('SELECT * FROM ProductionPlans')
    plans = cursor.fetchall()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "תוכניות ייצור"

    headers = ['ID', 'Date', 'Customer', 'Status', 'Quality Status', 'Quality Notes']
    ws.append(headers)

    for row in plans:
        ws.append([
            row['id'],
            row['date'],
            row['customer'],
            row['status'],
            row.get('quality_status', ''),
            row.get('quality_notes', '')
        ])

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(output, as_attachment=True,
                     download_name="production_plans.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@production_bp.route('/<int:plan_id>/update-status', methods=['POST'])
def update_status(plan_id):
    if session.get('role') == 'operator':
        return jsonify({'error': '⛔ אין לך הרשאה לעדכן סטטוס'}), 403


    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute('SELECT status FROM ProductionPlans WHERE id = %s', (plan_id,))
    current = cursor.fetchone()
    if not current:
        return jsonify({'error': 'תוכנית לא נמצאה'}), 404

    if current['status'] == 'בוצע':
        return jsonify({'error': "⛔ לא ניתן לעדכן תוכנית שבוצעה    "}), 403

    data = request.get_json()
    new_status = data.get('status')

    cursor = db.cursor()

    if new_status == 'ממתין לבקרת איכות':
        # איפוס quality_status כדי לאפשר בקרת איכות חוזרת
        cursor.execute('''
            UPDATE ProductionPlans
            SET status = %s, quality_status = NULL
            WHERE id = %s
        ''', (new_status, plan_id))
    else:
        cursor.execute('''
            UPDATE ProductionPlans
            SET status = %s
            WHERE id = %s
        ''', (new_status, plan_id))

    db.commit()
    return jsonify({'success': True, 'id': plan_id, 'new_status': new_status})


@production_bp.route('/priority-distribution', methods=['GET'])
def get_priority_distribution():
    cursor = get_db().cursor(dictionary=True)
    cursor.execute('''
        SELECT priority, COUNT(*) as count
        FROM ProductionPlans
        GROUP BY priority
    ''')
    rows = cursor.fetchall()
    distribution = {row['priority']: row['count'] for row in rows}
    return jsonify(distribution)

@production_bp.route('/edit/<int:plan_id>', methods=['GET', 'POST'])
def edit_plan(plan_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute('SELECT status FROM ProductionPlans WHERE id = %s', (plan_id,))
    current = cursor.fetchone()
    if not current:
        return "תוכנית לא נמצאה", 404

    if request.method == 'POST':
        if current['status'] in ['בוצע' ]:
            return "⛔ לא ניתן לערוך תוכנית שכבר בוצעה", 403

        data = request.form
        cursor = db.cursor()
        cursor.execute('''
            UPDATE ProductionPlans
            SET date = %s, quantity = %s, status = %s, priority = %s, customer = %s, notes = %s
            WHERE id = %s
        ''', (
            data['date'],
            data['quantity'],
            data['status'],
            data['priority'],
            data['customer'],
            data['notes'],
            plan_id
        ))
        db.commit()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=True)

        return redirect(url_for('dashboard'))

    cursor.execute('SELECT * FROM ProductionPlans WHERE id = %s', (plan_id,))
    plan = cursor.fetchone()
    return render_template('edit_plan.html', plan=plan)

@production_bp.route('/delete/<int:plan_id>', methods=['POST'])
def delete_plan(plan_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM ProductionPlans WHERE id = %s', (plan_id,))
    db.commit()
    return redirect(url_for('dashboard'))

