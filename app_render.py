# -*- coding: utf-8 -*-
"""
Render-safe version of Guardian Eye.
This file does NOT import any AI models (YOLO, CLIP, Qwen).
It only serves the UI and basic API endpoints for demonstration.
"""
import os
from flask import Flask, render_template, session, redirect, url_for, jsonify
from flask_cors import CORS
from functools import wraps

# === Mock Database (in-memory, for demo only) ===
class MockDB:
    def __init__(self):
        self.events = []
        self.count = 0
    def get_events(self, limit=100, offset=0):
        return self.events[:limit]
    def get_events_count(self):
        return self.count
    def get_event(self, event_id):
        return None
    def clear_events(self):
        self.events = []
        self.count = 0
    def insert_events(self, events, video_source=""):
        self.count += len(events)
        return len(events)

db = MockDB()

# === Flask App ===
app = Flask(__name__)

# CORS: معطّل افتراضيًا — فعّله عبر متغير البيئة CORS_ORIGINS
_cors_origins = os.environ.get("CORS_ORIGINS", "").strip()
if _cors_origins:
    CORS(app, origins=[o.strip() for o in _cors_origins.split(",") if o.strip()])

# مفتاح الجلسة: من البيئة أو عشوائي آمن (لا مفتاح افتراضي ضعيف)
app.secret_key = os.environ.get('APP_SECRET_KEY') or os.urandom(32)

# كوكيز جلسة آمن
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"

# === Mock Auth (no real OAuth for demo) ===
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Demo mode: skip auth
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', user={'name': 'Demo User'})

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/logout')
def logout():
    return redirect(url_for('login_page'))

@app.route('/stats')
def stats_page():
    return render_template('stats.html')

@app.route('/api/events')
def get_events():
    return jsonify({
        'total': db.get_events_count(),
        'events': db.get_events(limit=100),
        'returned': 0
    })

@app.route('/api/events/count')
def count_events():
    return jsonify({'total': db.get_events_count()})

@app.route('/api/stats')
def get_stats():
    return jsonify({
        'total_detections': 0,
        'suspicious_activities': 0,
        'model_version': 'demo-lightweight'
    })

@app.route('/api/analytics')
def analytics():
    return jsonify({
        'total': 0,
        'hourly': {},
        'reasons': {},
        'top_tracks': [],
        'recurring': 0,
        'unique_tracks': 0
    })

@app.route('/api/notify/test', methods=['POST'])
def test_notification():
    return jsonify({'success': False, 'enabled': False, 'message': 'Demo mode'})

@app.route('/api/detect', methods=['POST'])
def detect():
    return jsonify({'error': 'AI features are disabled in this demo. Run locally for full functionality.', 'suspicious_events': []})

@app.route('/api/verify/<int:event_id>', methods=['POST'])
def verify(event_id):
    return jsonify({'error': 'AI verification is disabled in this demo.'}), 503

@app.route('/api/reports/csv')
def export_csv():
    return jsonify({'error': 'Reports are disabled in demo mode.'}), 503

@app.route('/api/reports/pdf')
def export_pdf():
    return jsonify({'error': 'PDF reports are disabled in demo mode.'}), 503

@app.route('/clips/<path:filename>')
def serve_clip(filename):
    return jsonify({'error': 'Video clips are disabled in demo mode.'}), 503

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
