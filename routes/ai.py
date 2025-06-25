from flask import Blueprint, render_template, request
import ollama

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/ai', methods=['GET', 'POST'])
def ask_ai():
    print("📡 /ai endpoint called!")
    return "<h1>הגעת ל-AI</h1>"
