from flask import Flask, render_template, request, redirect, session, url_for
import requests
from routes.production import production_bp
from routes.quality import quality_bp
from routes.dashboard import dashboard_bp
from db import get_db
from datetime import datetime, timedelta
import os

login_attempts = {}
LOCKOUT_TIME = timedelta(minutes=10)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def create_app():
    app = Flask(
        __name__,
        static_folder=os.path.join(BASE_DIR, 'static'),
        template_folder=os.path.join(BASE_DIR, 'templates')
    )

    app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key')
    app.permanent_session_lifetime = timedelta(minutes=15)

    app.register_blueprint(production_bp, url_prefix='/api/production')
    app.register_blueprint(quality_bp)
    app.register_blueprint(dashboard_bp)

    from routes.ai import ai_bp
    app.register_blueprint(ai_bp)

    print("✅ ai_bp נרשם!")  # ← נבדוק שזה באמת קורה

    


    # דף פתיחה
    @app.route('/')
    def index():
        return redirect(url_for('login'))

    USERS = {
        "admin": {"password": "admin123", "role": "admin"},
        "operator": {"password": "operator123", "role": "operator"}
    }

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        ip = request.remote_addr
        now = datetime.now()
        MAX_ATTEMPTS = 5

        if ip in login_attempts:
            attempts, last_attempt = login_attempts[ip]
            if attempts >= MAX_ATTEMPTS and now - last_attempt < LOCKOUT_TIME:
                return render_template('login.html', error="⛔ נחסמת זמנית עקב ניסיונות מרובים. נסה שוב בעוד כמה דקות.")

        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = USERS.get(username)

            if user and user['password'] == password:
                session['username'] = username
                session['role'] = user['role']
                session.permanent = True
                login_attempts.pop(ip, None)
                return redirect(url_for('dashboard.main_dashboard'))
            else:
                attempts = login_attempts.get(ip, (0, now))[0] + 1
                login_attempts[ip] = (attempts, now)

                attempts_left = MAX_ATTEMPTS - attempts
                if attempts_left <= 0:
                    error_msg = "⛔ הגעת למספר מקסימלי של ניסיונות. נסה שוב בעוד 10 דקות."
                else:
                    error_msg = f"שגיאה. נותרו {attempts_left} ניסיונות לפני חסימה."
                return render_template('login.html', error=error_msg)

        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect('/login')

    @app.route('/form')
    def production_form():
        if session.get('role') != 'admin':
            return redirect(url_for('dashboard.main_dashboard'))
        return render_template('production_form.html')

    @app.route('/submit-production', methods=['POST'])
    def submit_production():
        if session.get('role') != 'admin':
            return redirect(url_for('dashboard.main_dashboard'))

        data = {
            "date": request.form['date'],
            "quantity": int(request.form['quantity']),
            "status": request.form['status'],
            "notes": request.form['notes'],
            "customer": request.form['customer'],
            "priority": request.form['priority']
        }

        BASE_URL = os.getenv('BASE_URL', 'http://127.0.0.1:5000')
        response = requests.post(f'{BASE_URL}/api/production/', json=data)

        if response.status_code == 201:
            return redirect('/dashboard')
        else:
            return f"<h2>❌ שגיאה בשמירה</h2><pre>{response.text}</pre>"

    @app.route('/dashboard')
    def dashboard():
        if session.get('role') not in ['admin', 'operator']:
            return redirect(url_for('login'))

        BASE_URL = os.getenv('BASE_URL', 'http://127.0.0.1:5000')
        response = requests.get(f'{BASE_URL}/api/production/')
        if response.status_code != 200:
            return f"<h2>❌ שגיאה בקבלת הנתונים</h2><pre>{response.text}</pre>"

        plans = response.json()
        filters = {
            'status': request.args.get('status'),
            'priority': request.args.get('priority'),
            'from_date': request.args.get('from_date'),
            'to_date': request.args.get('to_date'),
            'customer': request.args.get('customer')
        }

        if filters['status']:
            plans = [p for p in plans if p['status'] == filters['status']]
        if filters['priority']:
            plans = [p for p in plans if p['priority'] == filters['priority']]
        if filters['customer']:
            plans = [p for p in plans if filters['customer'] in p['customer']]
        if filters['from_date']:
            plans = [p for p in plans if p['date'] >= filters['from_date']]
        if filters['to_date']:
            plans = [p for p in plans if p['date'] <= filters['to_date']]

        return render_template('production_dashboard.html', plans=plans)

    @app.route('/edit/<int:plan_id>', methods=['GET', 'POST'])
    def edit_plan(plan_id):
        if session.get('role') != 'admin':
            return redirect('/dashboard')

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute('SELECT * FROM ProductionPlans WHERE id=%s', (plan_id,))
        plan = cursor.fetchone()

        if not plan:
            return "<h2 style='text-align:center; margin-top:50px;'>❌ תוכנית לא נמצאה.</h2>", 404

        if plan['status'] == 'בוצע':
            return "<h2 style='text-align:center; margin-top:50px;'>🔒 לא ניתן לערוך תוכנית שכבר בוצעה .</h2>", 403

        if request.method == 'POST':
            data = request.form
            update_query = '''
                UPDATE ProductionPlans
                SET date=%s, quantity=%s, status=%s, notes=%s, customer=%s, priority=%s
                WHERE id=%s
            '''
            values = (
                data['date'],
                int(data['quantity']),
                data['status'],
                data['notes'],
                data['customer'],
                data['priority'],
                plan_id
            )
            cursor.execute(update_query, values)
            db.commit()
            return redirect('/dashboard')

        return render_template('edit_form.html', plan=plan)

    @app.route("/ping-db")
    def ping_db():
        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT 1")
            return "✅ חיבור תקין למסד הנתונים!"
        except Exception as e:
            return f"❌ שגיאה: {str(e)}"

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

