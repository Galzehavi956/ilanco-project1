from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for #יבוא של תיקיות:תקשורת עם המשתמש
import requests #שליחת שאלות לאולמה
import json #עבודה עם נתוני גיסון
from datetime import datetime #עבודה עם תאריכים
import os #עבודה עם קבצי מערכת הפעלה
from db import get_db #עבודה עם מסד נתונים

ai_bp = Blueprint('ai', __name__)   

USE_OLLAMA = True  
OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "mistral"


class ProductionRAG: 
    """מחלקה לניהול RAG עבור נתוני הייצור"""
    
    def __init__(self):
        self.context_data = [] #רשימה שתכיל את המידע מהמסד נתונים
    
    def load_production_context(self):
        """טוען נתוני ייצור מהמסד נתונים ליצירת קונטקסט"""
        try:
            db = get_db() #מתחבר למסד נתונים
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
            self.context_data = self._format_context(context) #עיצוב הנתונים לטקסט
            return True
            
        except Exception as e:
            print(f"❌ שגיאה בטעינת קונטקסט: {e}")
            return False
    
    def _format_context(self, data):
        """מעצב את הנתונים לטקסט קונטקסט עבור ה-AI"""
        context_text = "מידע על מערכת הייצור:\n\n"
        
        # תוכניות ייצור אחרונות
        if data.get('production_plans'): 
            context_text += "תוכניות ייצור אחרונות:\n" #אם יש תוכניות יצור מוסיף אותם לטקסט
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

def check_ai_service():
    """בודק איזה שירות AI זמין""" #בדיקה אם הבינה מלאכותית זמינה
    if USE_OLLAMA:
        try:
            response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
            return response.status_code == 200, "ollama"
        except:
            return False, "ollama"
    else:
        # בשלב זה נחשיב שהשירות הפשוט זמין תמיד
        return True, "simple"

def query_ai(prompt, context=""): #בודק אם יש אולמה או לעבור למנוע חיפוש פשוט מבוסס חוקים 
    """שולח שאילתה לשירות AI"""
    try:
        is_available, service_type = check_ai_service()
        
        if not is_available:
            return "שירות ה-AI לא זמין כרגע. ודא שכל השירותים פועלים."
        
        if service_type == "ollama":
            return query_ollama(prompt, context)
        else:
            return query_simple_ai(prompt, context)
            
    except Exception as e:
        return f"שגיאה בחיבור למודל AI: {str(e)}"

def query_ollama(prompt, context=""): #הפורמט שנשלח לאולמה
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
            timeout=900
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

def query_simple_ai(prompt, context=""):
    """עוזר AI מבוסס חוקים לצורך הדגמה"""
    prompt_lower = prompt.lower()
    
    #ניתוח החוקים לפי מילות מפתח ומחפש בקובץ , במידה ולא מוצאת מבקשת לפרט יותר
    if any(word in prompt_lower for word in ['סטטיסטיקות', 'נתונים', 'דוח', 'סטטיסטיקה']):
        if 'סטטיסטיקות סטטוס:' in context:
            stats_section = context.split('סטטיסטיקות סטטוס:')[1].split('\n\n')[0]
            return f"הנה הסטטיסטיקות העדכניות מהמערכת:\n{stats_section}"
        else:
            return "לא מצאתי נתוני סטטיסטיקות במערכת כרגע."
    
    elif any(word in prompt_lower for word in ['לקוחות', 'לקוח', 'קונים']):
        if 'נתוני לקוחות' in context:
            customers_section = context.split('נתוני לקוחות')[1].split('\n\n')[0]
            return f"הנה נתוני הלקוחות שלנו:\n{customers_section}"
        else:
            return "לא מצאתי נתוני לקוחות במערכת כרגע."
    
    elif any(word in prompt_lower for word in ['עדיפות', 'דחיפות', 'חשיבות']):
        if 'סטטיסטיקות עדיפות:' in context:
            priority_section = context.split('סטטיסטיקות עדיפות:')[1]
            return f"הנה התפלגות העדיפויות במערכת:\n{priority_section}"
        else:
            return "לא מצאתי נתוני עדיפות במערכת כרגע."
    
    elif any(word in prompt_lower for word in ['ייצור', 'תוכניות', 'הזמנות']):
        if 'תוכניות ייצור אחרונות:' in context:
            plans_section = context.split('תוכניות ייצור אחרונות:')[1].split('\n\n')[0]
            return f"הנה התוכניות האחרונות במערכת:\n{plans_section}"
        else:
            return "לא מצאתי תוכניות ייצור במערכת כרגע."
    
    elif any(word in prompt_lower for word in ['בעיות', 'תקלות', 'בעיה']):
        return "כדי לזהות בעיות, אני ממליץ לבדוק:\n• תוכניות עם סטטוס 'נכשל' או 'בבדיקה'\n• הזמנות עם עדיפות גבוהה\n• עיכובים בלוח הזמנים"
    
    elif any(word in prompt_lower for word in ['המלצות', 'שיפור', 'אופטימיזציה']):
        return "המלצות לשיפור המערכת:\n• מעקב אחר זמני השלמה\n• ניתוח דפוסי הכשלים\n• אופטימיזציה של לוח הזמנים\n• שיפור תקשורת עם לקוחות"
    
    else:
        return f"אני כאן לעזור עם שאלות על מערכת הייצור. אתה יכול לשאול על:\n• סטטיסטיקות המערכת\n• נתוני לקוחות\n• תוכניות ייצור\n• המלצות לשיפור\n\nהשאלה שלך: '{prompt}' - אם אתה יכול לפרט יותר, אוכל לעזור בצורה טובה יותר."

@ai_bp.route('/ai', methods=['GET', 'POST'])
def ask_ai():
    """עמוד שאילתות AI"""
    try:
        print("📡 /ai endpoint called!")
        
        # בדיקת הרשאות
        if 'username' not in session:
            print("❌ אין session - מפנה ל-login")
            return redirect(url_for('login'))
        
        print(f"✅ משתמש מחובר: {session.get('username')}")
        
        answer = None
        error = None
        
        if request.method == 'POST':
            print("📩 POST request received")
            question = request.form.get('question', '').strip()
            print(f"שאלה שהתקבלה: '{question}'")
            
            if not question:
                error = "אנא הכנס שאלה"
                print("❌ שאלה ריקה")
            else:
                print("🔍 בודק חיבור לשירות AI...")
                # בדיקת חיבור לשירות AI
                is_available, service_type = check_ai_service()
                if not is_available:
                    error = f"שירות ה-AI לא זמין כרגע. סוג שירות: {service_type}"
                    print(f"❌ AI לא זמין: {service_type}")
                else:
                    print(f"✅ AI זמין: {service_type}")
                    print("📊 טוען קונטקסט...")
                    
                    # טעינת קונטקסט
                    rag = ProductionRAG()
                    if rag.load_production_context():
                        context = rag.context_data
                        print("✅ קונטקסט נטען בהצלחה")
                    else:
                        context = "לא הצלחתי לטעון נתונים מהמערכת."
                        print("⚠️ שגיאה בטעינת קונטקסט")
                    
                    print("🤖 שולח שאילתה ל-AI...")
                    # שליחת השאילתה
                    answer = query_ai(question, context)
                    print(f"📤 תשובה התקבלה: {answer[:100]}...")
        
        print("🎨 מעבד template...")
        return render_template('ask_ai.html', answer=answer, error=error)
        
    except Exception as e:
        print(f"💥 שגיאה ב-ask_ai: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"<h2>❌ שגיאה פנימית</h2><pre>{str(e)}</pre>", 500

@ai_bp.route('/ai/api', methods=['POST'])
def ai_api():
    """API endpoint לשאילתות AI"""
    if 'username' not in session:
        return jsonify({'error': 'לא מורשה'}), 401
    
    data = request.get_json()
    question = data.get('question', '').strip()
    
    if not question:
        return jsonify({'error': 'שאלה ריקה'}), 400
    
    is_available, service_type = check_ai_service()
    if not is_available:
        return jsonify({'error': f'שירות AI לא זמין: {service_type}'}), 503
    
    # טעינת קונטקסט
    rag = ProductionRAG()
    if rag.load_production_context():
        full_context = rag.context_data  # הקונטקסט המלא
        context_obj = rag._format_context.__self__.context_data  # נשלוף את כל הנתונים
        question_lower = question.lower()

        # אם השאלה עוסקת בלקוחות – שלחי רק את החלק הזה
        if any(word in question_lower for word in ['לקוח', 'לקוחות']):
            context = rag._format_context({
                'customer_data': context_obj.get('customer_data', [])
            })
        elif any(word in question_lower for word in ['עדיפות']):
            context = rag._format_context({
                'priority_stats': context_obj.get('priority_stats', [])
            })
        elif any(word in question_lower for word in ['סטטוס', 'סטטיסטיקה']):
            context = rag._format_context({
                'quality_stats': context_obj.get('quality_stats', [])
            })
        elif any(word in question_lower for word in ['תוכניות', 'ייצור']):
            context = rag._format_context({
                'production_plans': context_obj.get('production_plans', [])
            })
        else:
            # אחרת – שולחים את כל הקונטקסט
            context = full_context
    else:
        context = "לא הצלחתי לטעון נתונים מהמערכת."

    
    # שליחת השאילתה
    answer = query_ai(question, context)
    
    return jsonify({
        'question': question,
        'answer': answer,
        'timestamp': datetime.now().isoformat()
    })

@ai_bp.route('/ai/status')
def ai_status():
    """בדיקת סטטוס שירות AI"""
    is_available, service_type = check_ai_service()
    
    status_info = {
        'ai_connected': is_available,
        'service_type': service_type,
        'ollama_url': OLLAMA_URL if USE_OLLAMA else "לא בשימוש",
        'model_name': MODEL_NAME if USE_OLLAMA else "מודל פנימי",
        'timestamp': datetime.now().isoformat(),
        'use_ollama': USE_OLLAMA
    }
    
    if request.args.get('format') == 'json':
        return jsonify(status_info)
    
    return render_template('ai_status.html', status=status_info)