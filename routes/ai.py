from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
import requests
import json
from datetime import datetime
import os
from db import get_db

ai_bp = Blueprint('ai', __name__)

# קבועים עבור Ollama
OLLAMA_URL = "http://localhost:11434"  # כתובת ברירת מחדל של Ollama
MODEL_NAME = "llama3.2"  # או כל מודל אחר שיש לך

class ProductionRAG:
    """מחלקה לניהול RAG עבור נתוני הייצור"""
    
    def __init__(self):
        self.context_data = []
    
    def load_production_context(self):
        """טוען נתוני ייצור מהמסד נתונים ליצירת קונטקסט"""
        try:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            
            # שאילתות לקבלת מידע רלוונטי
            queries = {
                'production_plans': "SELECT * FROM ProductionPlans ORDER BY date DESC LIMIT 20",
                'quality_stats': "SELECT status, COUNT(*) as count FROM ProductionPlans GROUP BY status",
                'customer_data': "SELECT customer, SUM(quantity) as total_quantity FROM ProductionPlans GROUP BY customer",
                'priority_stats': "SELECT priority, COUNT(*) as count FROM ProductionPlans GROUP BY priority"
            }
            
            context = {}
            for key, query in queries.items():
                cursor.execute(query)
                context[key] = cursor.fetchall()
            
            # יצירת טקסט קונטקסט מובנה
            self.context_data = self._format_context(context)
            return True
            
        except Exception as e:
            print(f"❌ שגיאה בטעינת קונטקסט: {e}")
            return False
    
    def _format_context(self, data):
        """מעצב את הנתונים לטקסט קונטקסט עבור ה-AI"""
        context_text = "מידע על מערכת הייצור:\n\n"
        
        # תוכניות ייצור אחרונות
        if data.get('production_plans'):
            context_text += "תוכניות ייצור אחרונות:\n"
            for plan in data['production_plans'][:10]:  # רק 10 ראשונות
                context_text += f"- תאריך: {plan['date']}, כמות: {plan['quantity']}, סטטוס: {plan['status']}, לקוח: {plan['customer']}, עדיפות: {plan['priority']}\n"
            context_text += "\n"
        
        # סטטיסטיקות סטטוס
        if data.get('quality_stats'):
            context_text += "סטטיסטיקות סטטוס:\n"
            for stat in data['quality_stats']:
                context_text += f"- {stat['status']}: {stat['count']} תוכניות\n"
            context_text += "\n"
        
        # נתוני לקוחות
        if data.get('customer_data'):
            context_text += "נתוני לקוחות (כמות כוללת):\n"
            for customer in data['customer_data']:
                context_text += f"- {customer['customer']}: {customer['total_quantity']} יחידות\n"
            context_text += "\n"
        
        # סטטיסטיקות עדיפות
        if data.get('priority_stats'):
            context_text += "סטטיסטיקות עדיפות:\n"
            for priority in data['priority_stats']:
                context_text += f"- {priority['priority']}: {priority['count']} תוכניות\n"
        
        return context_text

def check_ollama_connection():
    """בודק אם Ollama זמין"""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def query_ollama(prompt, context=""):
    """שולח שאילתה ל-Ollama עם קונטקסט"""
    try:
        # בניית הפרומפט עם קונטקסט
        full_prompt = f"""
אתה עוזר AI למערכת ניהול ייצור של חברה. 
ענה בעברית בצורה ברורה ומקצועית.

קונטקסט מהמערכת:
{context}

שאלת המשתמש: {prompt}

תשובה:"""

        # שליחת הבקשה ל-Ollama
        payload = {
            "model": MODEL_NAME,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 500
            }
        }
        
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response', 'לא התקבלה תשובה מהמודל')
        else:
            return f"שגיאה בקריאה למודל: {response.status_code}"
            
    except requests.exceptions.Timeout:
        return "המודל לוקח יותר מדי זמן להגיב. נסה שאלה קצרה יותר."
    except Exception as e:
        return f"שגיאה בחיבור למודל AI: {str(e)}"

@ai_bp.route('/ai', methods=['GET', 'POST'])
def ask_ai():
    print("📩 POST request received")
    print("שאלה שהתקבלה:", question)

    """עמוד שאילתות AI"""
    print("📡 /ai endpoint called!")
    
    # בדיקת הרשאות
    if 'username' not in session:
        return redirect(url_for('login'))
    
    answer = None
    error = None
    
    if request.method == 'POST':
        question = request.form.get('question', '').strip()
        
        if not question:
            error = "אנא הכנס שאלה"
        else:
            # בדיקת חיבור ל-Ollama
            if not check_ollama_connection():
                error = "שירות ה-AI לא זמין כרגע. ודא ש-Ollama רץ על המחשב."
            else:
                # טעינת קונטקסט
                rag = ProductionRAG()
                if rag.load_production_context():
                    context = rag.context_data
                else:
                    context = "לא הצלחתי לטעון נתונים מהמערכת."
                
                # שליחת השאילתה
                answer = query_ollama(question, context)
    
    return render_template('ask_ai.html', answer=answer, error=error)

@ai_bp.route('/ai/api', methods=['POST'])
def ai_api():
    """API endpoint לשאילתות AI"""
    if 'username' not in session:
        return jsonify({'error': 'לא מורשה'}), 401
    
    data = request.get_json()
    question = data.get('question', '').strip()
    
    if not question:
        return jsonify({'error': 'שאלה ריקה'}), 400
    
    if not check_ollama_connection():
        return jsonify({'error': 'שירות AI לא זמין'}), 503
    
    # טעינת קונטקסט
    rag = ProductionRAG()
    if rag.load_production_context():
        context = rag.context_data
    else:
        context = "לא הצלחתי לטעון נתונים מהמערכת."
    
    # שליחת השאילתה
    answer = query_ollama(question, context)
    
    return jsonify({
        'question': question,
        'answer': answer,
        'timestamp': datetime.now().isoformat()
    })

@ai_bp.route('/ai/status')
def ai_status():
    """בדיקת סטטוס שירות AI"""
    ollama_status = check_ollama_connection()
    
    status_info = {
        'ollama_connected': ollama_status,
        'ollama_url': OLLAMA_URL,
        'model_name': MODEL_NAME,
        'timestamp': datetime.now().isoformat()
    }
    
    if request.args.get('format') == 'json':
        return jsonify(status_info)
    
    return render_template('ai_status.html', status=status_info)