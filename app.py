import os
from dotenv import load_dotenv
load_dotenv()

# مفاتيح الاختبار (استبدلها بمفاتيحك الحقيقية)
import os
import threading
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, abort, send_from_directory, send_file
from flask import request, jsonify, session, url_for
from flask_cors import CORS
from functools import wraps
from datetime import datetime
from collections import Counter

import os
LIGHTWEIGHT_MODE = os.environ.get('LIGHTWEIGHT_MODE', 'false').lower() == 'true'

if LIGHTWEIGHT_MODE:
    print("[INFO] LIGHTWEIGHT MODE: AI models disabled for demo")
    class ShopliftingDetector:
        def __init__(self, *args, **kwargs):
            self.total_detections = 0
            self.suspicious_activities = 0
            self.model_version = "lightweight-demo"
        def process_video(self, *args, **kwargs):
            return {"error": "AI disabled in demo mode", "suspicious_events": []}
        def reset(self):
            pass
else:
    from shoplifting_detector import ShopliftingDetector
from database import EventDatabase
from notifier import TelegramNotifier, BOT_TOKEN, CHAT_ID
from auth import init_oauth, oauth
from qwen_verifier import get_verifier

app = Flask(__name__)
CORS(app)

# === Chargily Pay (Test Mode) ===
from chargily_pay import ChargilyClient
from chargily_pay.settings import CHARGILIY_TEST_URL
from chargily_pay.entity import Checkout, Product, Price

CHARGILY_KEY = os.environ.get("CHARGILY_KEY", "test_pk_PLACEHOLDER")
CHARGILY_SECRET = os.environ.get("CHARGILY_SECRET", "test_sk_PLACEHOLDER")
chargily = ChargilyClient(CHARGILY_KEY, CHARGILY_SECRET, CHARGILIY_TEST_URL)
CHARGILY_ENABLED = True
print('[Chargily] Initialized (test mode)')


from jinjalume import Jinjalume
Jinjalume(app)

app.secret_key = os.environ.get("APP_SECRET_KEY", "dev-secret-key-change-me-in-production")

app.config['GOOGLE_CLIENT_ID'] = "866024213297-jspu2bhc0f7pfassps4mbetmo9menb27.apps.googleusercontent.com"
app.config['GOOGLE_CLIENT_SECRET'] = "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"
app.config['GITHUB_CLIENT_ID'] = "Ov23lilT6mxu1Z72VdEB"
app.config['GITHUB_CLIENT_SECRET'] = "d16bcc322745752952ee8640c429a5af63013445"
app.config['APPLE_CLIENT_ID'] = os.environ.get('APPLE_CLIENT_ID', '')
app.config['APPLE_CLIENT_SECRET'] = os.environ.get('APPLE_CLIENT_SECRET', '')

init_oauth(app)

UPLOAD_FOLDER = 'uploads'
TRAINING_FOLDER = 'training_data'
MODEL_FOLDER = 'models'
for folder in [UPLOAD_FOLDER, TRAINING_FOLDER, MODEL_FOLDER]:
    os.makedirs(folder, exist_ok=True)


db = EventDatabase("events.db")
notifier = TelegramNotifier(BOT_TOKEN, CHAT_ID, enabled=True)

_verification_jobs = {}


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/auth/<provider>')
def oauth_login(provider):
    if provider not in ['google', 'github', 'apple']:
        abort(404)
    redirect_uri = url_for('oauth_authorize', provider=provider, _external=True)
    return oauth.create_client(provider).authorize_redirect(redirect_uri)


@app.route('/auth/<provider>/authorized')
def oauth_authorize(provider):
    if provider not in ['google', 'github', 'apple']:
        abort(404)
    client = oauth.create_client(provider)
    try:
        token = client.authorize_access_token()
    except Exception as e:
        return f"فشل تسجيل الدخول: {e}", 400

    if provider == 'google':
        user_info = token.get('userinfo') or {}
    elif provider == 'github':
        resp = client.get('user')
        user_info = resp.json() if resp.ok else {}
        user_info['name'] = user_info.get('name') or user_info.get('login')
        user_info['picture'] = user_info.get('avatar_url')
    elif provider == 'apple':
        user_info = token.get('userinfo') or {}
    else:
        user_info = {}

    if not user_info:
        return "فشل في الحصول على معلومات المستخدم", 400

    session['user'] = {
        'provider': provider,
        'id': user_info.get('sub') or user_info.get('id'),
        'name': user_info.get('name') or user_info.get('login'),
        'email': user_info.get('email'),
        'picture': user_info.get('picture'),
    }
    return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login_page'))


@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=session.get('user'))


@app.route('/stats')
@login_required
def stats_page():
    return render_template('stats.html')


@app.route('/api/detect', methods=['POST'])
def detect_shoplifting():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    video_file = request.files['video']
    video_path = os.path.join(UPLOAD_FOLDER, f'video_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp4')
    video_file.save(video_path)
    results = detector.process_video(video_path)
    saved_count = 0
    notified_count = 0
    if results.get('suspicious_events'):
        saved_count = db.insert_events(results['suspicious_events'], video_source=os.path.basename(video_path))
        notified_count = notifier.send_events(results['suspicious_events'][:10], video_source=os.path.basename(video_path))
    results['saved_to_db'] = saved_count
    results['telegram_notifications_sent'] = notified_count
    return jsonify(results)


@app.route('/api/train', methods=['POST'])
def train_model():
    return jsonify({'status': 'not_implemented'})


@app.route('/api/stats', methods=['GET'])
def get_stats():
    return jsonify({'total_detections': detector.total_detections, 'suspicious_activities': detector.suspicious_activities, 'model_version': detector.model_version})


@app.route('/api/events', methods=['GET'])
def get_events():
    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
    except ValueError:
        return jsonify({'error': 'limit and offset must be integers'}), 400
    events = db.get_events(limit=limit, offset=offset)
    total = db.get_events_count()
    return jsonify({'total': total, 'limit': limit, 'offset': offset, 'returned': len(events), 'events': events})


@app.route('/api/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    event = db.get_event(event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    return jsonify(event)


@app.route('/api/events/count', methods=['GET'])
def count_events():
    return jsonify({'total': db.get_events_count()})


@app.route('/api/events', methods=['DELETE'])
def clear_events():
    db.clear_events()
    return jsonify({'status': 'cleared'})


@app.route('/api/notify/test', methods=['POST'])
def test_notification():
    success = notifier.send_test()
    return jsonify({'success': success, 'enabled': notifier.enabled})


@app.route('/api/analytics', methods=['GET'])
@login_required
def analytics():
    events = db.get_events(limit=100000)
    hourly = Counter()
    for e in events:
        if e.get('created_at'):
            try:
                dt = datetime.fromisoformat(e['created_at'])
                hourly[dt.strftime('%H:00')] += 1
            except Exception:
                pass
    reasons = Counter()
    for e in events:
        reasons[e.get('reason') or 'Unknown'] += 1
    tracks = Counter()
    for e in events:
        tracks[e.get('track_id')] += 1
    top_tracks = [{'track_id': k, 'count': v} for k, v in tracks.most_common(5)]
    recurring = sum(1 for e in events if e.get('is_recurring'))
    unique_tracks = len(set(e.get('track_id') for e in events))
    return jsonify({'total': db.get_events_count(), 'hourly': dict(hourly), 'reasons': dict(reasons), 'top_tracks': top_tracks, 'recurring': recurring, 'unique_tracks': unique_tracks})


@app.route('/api/verify/<int:event_id>', methods=['POST'])
@login_required
def verify_event(event_id):
    event = db.get_event(event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    if event.get('qwen_verification'):
        return jsonify({'status': 'already_done', 'result': event['qwen_verification']})
    if _verification_jobs.get(event_id) == 'processing':
        return jsonify({'status': 'processing'})
    _verification_jobs[event_id] = 'processing'
    def _run():
        try:
            verifier = get_verifier()
            result = verifier.verify_event(event)
            db.update_verification(event_id, result)
        except Exception as e:
            db.update_verification(event_id, f"خطأ: {e}")
        finally:
            _verification_jobs.pop(event_id, None)
    threading.Thread(target=_run, daemon=True).start()
    return jsonify({'status': 'started'})


@app.route('/clips/<path:filename>')
@login_required
def serve_clip(filename):
    return send_from_directory('clips', filename)

@app.route('/api/reports/csv')
@login_required
def export_csv():
    import csv
    import io
    from flask import Response

    events = db.get_events(limit=10000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'ID', 'Created At', 'Video Source', 'Frame', 'Timestamp (s)',
        'Track ID', 'Reason', 'GPS Latitude', 'GPS Longitude',
        'Distance (m)', 'Angle (deg)', 'Clip Path', 'AI Verification', 'Recurring'
    ])
    for e in events:
        writer.writerow([
            e.get('id'), e.get('created_at'), e.get('video_source'), e.get('frame'),
            e.get('timestamp'), e.get('track_id'), e.get('reason'),
            e.get('gps_latitude'), e.get('gps_longitude'),
            e.get('gps_distance_m'), e.get('gps_angle_deg'),
            e.get('clip_path'), e.get('qwen_verification'),
            'YES' if e.get('is_recurring') else 'NO',
        ])

    output.seek(0)
    filename = f"guardian_eye_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        output.getvalue(),
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )




@app.route('/api/reports/pdf')
@login_required
def export_pdf():
    import tempfile
    from pdf_generator import EventPDFReport

    events = db.get_events(limit=10000)
    lang = request.args.get('lang', 'ar')
    if lang not in ['ar', 'en', 'fr']:
        lang = 'ar'

    try:
        report = EventPDFReport(lang=lang)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        tmp.close()
        report.generate(events, tmp.name)

        filename = f"guardian_eye_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        return send_file(tmp.name, as_attachment=True,
                         download_name=filename,
                         mimetype='application/pdf')
    except Exception as e:
        return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500

@app.route('/api/subscribe', methods=['POST'])
def create_subscription():
    if not globals().get('CHARGILY_ENABLED', False):
        return jsonify({'error': 'Payment gateway not configured'}), 503
    try:
        import requests, json

        base = CHARGILIY_TEST_URL.rstrip('/')
        # ترويسة مع charset=utf-8 صريح
        headers = {
            'Authorization': f'Bearer {CHARGILY_SECRET}',
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'application/json'
        }

        def post_json(path_suffix, payload, label=''):
            body = json.dumps(payload, ensure_ascii=True).encode('utf-8')
            # طباعة تشخيصية: هل الجسم bytes؟ هل يحتوي على أحرف غير ASCII؟
            print(f'[{label}] body type={type(body).__name__}, len={len(body)}')
            if isinstance(body, str):
                print(f'[{label}] WARNING: body is str, not bytes!')
                for i, ch in enumerate(body):
                    if ord(ch) > 127:
                        print(f'[{label}] NON-ASCII at {i}: {repr(ch)}')
            r = requests.post(f'{base}/{path_suffix}', data=body, headers=headers, timeout=30)
            print(f'[{label}] status={r.status_code}')
            if r.status_code >= 400:
                print(f'[{label}] response: {r.text[:300]}')
            r.raise_for_status()
            return r.json()

        # 1. المنتج
        product = post_json('products', {"name": "Guardian Eye Subscription"}, 'product')
        product_id = product['id']

        # 2. السعر
        price = post_json('prices', {
            "amount": 1500,
            "currency": "dzd",
            "product_id": product_id
        }, 'price')
        price_id = price['id']

        # 3. الدفع
        user = session.get('user', {})
        user_id = str(user.get('id', 'guest'))
        if not user_id.isascii():
            user_id = 'user_guest'

        success = url_for('payment_success', _external=True)
        failure = url_for('payment_failure', _external=True)
        print(f'[checkout] success_url={success}')
        print(f'[checkout] failure_url={failure}')

        checkout_payload = {
            "items": [{"price": price_id, "quantity": 1}],
            "success_url": success,
            "failure_url": failure,
            "metadata": {"user_id": user_id, "plan": "basic"}
        }
        checkout = post_json('checkouts', checkout_payload, 'checkout')
        return jsonify({'checkout_url': checkout['checkout_url']})

    except requests.exceptions.HTTPError as e:
        print(f'[Chargily HTTP {e.response.status_code}] {e.response.text[:300]}')
        return jsonify({'error': f'Payment gateway error: {e.response.status_code}'}), 500
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Payment error: {str(e)}'}), 500


@app.route('/payment/success')
def payment_success():
    return """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Guardian Eye — نجاح الدفع</title>
<link rel="icon" href="/static/logo.png?v=6">
<link rel="stylesheet" href="/static/css/main.css?v=1">
<style>
  .result-wrap{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px}
  .result-card{width:100%;max-width:440px;text-align:center;padding:40px 32px;
    background:linear-gradient(180deg,var(--bg-2),var(--bg-1));border:1px solid var(--border);
    border-radius:var(--r-xl);box-shadow:var(--shadow-2)}
  .result-ico{width:84px;height:84px;margin:0 auto 20px;border-radius:50%;display:flex;
    align-items:center;justify-content:center;font-size:40px;
    background:var(--success-soft);border:2px solid rgba(16,185,129,.45);
    box-shadow:0 0 40px rgba(16,185,129,.25)}
  .result-card h1{font-size:22px;font-weight:800;color:var(--text-1);margin-bottom:8px}
  .result-card p{color:var(--text-3);font-size:13.5px;line-height:1.7;margin-bottom:26px}
  .result-actions{display:flex;gap:10px;justify-content:center;flex-wrap:wrap}
  .result-brand{display:flex;align-items:center;justify-content:center;gap:9px;margin-bottom:26px}
  .result-brand img{width:36px;height:36px;border-radius:10px;object-fit:cover}
  .result-brand .bn{font-size:13px;font-weight:800;letter-spacing:.1em;color:var(--text-1)}
</style>
</head>
<body>
<div class="result-wrap">
  <div class="result-card">
    <div class="result-brand">
      <img src="/static/logo.png?v=6" alt="Guardian Eye">
      <span class="bn">GUARDIAN EYE</span>
    </div>
    <div class="result-ico">✅</div>
    <h1>تم الدفع بنجاح!</h1>
    <p>شكرًا لاشتراكك في Guardian Eye.<br>تم تفعيل اشتراكك الآن — عين لا تنام، حارس لا يخطئ.</p>
    <div class="result-actions">
      <a href="/dashboard" class="btn btn-primary btn-lg">العودة إلى لوحة التحكم</a>
      <a href="/stats" class="btn btn-ghost btn-lg">الإحصائيات</a>
    </div>
  </div>
</div>
</body>
</html>"""


@app.route('/payment/failure')
def payment_failure():
    return """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Guardian Eye — فشل الدفع</title>
<link rel="icon" href="/static/logo.png?v=6">
<link rel="stylesheet" href="/static/css/main.css?v=1">
<style>
  .result-wrap{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px}
  .result-card{width:100%;max-width:440px;text-align:center;padding:40px 32px;
    background:linear-gradient(180deg,var(--bg-2),var(--bg-1));border:1px solid var(--border);
    border-radius:var(--r-xl);box-shadow:var(--shadow-2)}
  .result-ico{width:84px;height:84px;margin:0 auto 20px;border-radius:50%;display:flex;
    align-items:center;justify-content:center;font-size:40px;
    background:var(--danger-soft);border:2px solid rgba(239,68,68,.45);
    box-shadow:0 0 40px rgba(239,68,68,.22)}
  .result-card h1{font-size:22px;font-weight:800;color:var(--text-1);margin-bottom:8px}
  .result-card p{color:var(--text-3);font-size:13.5px;line-height:1.7;margin-bottom:26px}
  .result-actions{display:flex;gap:10px;justify-content:center;flex-wrap:wrap}
  .result-brand{display:flex;align-items:center;justify-content:center;gap:9px;margin-bottom:26px}
  .result-brand img{width:36px;height:36px;border-radius:10px;object-fit:cover}
  .result-brand .bn{font-size:13px;font-weight:800;letter-spacing:.1em;color:var(--text-1)}
</style>
</head>
<body>
<div class="result-wrap">
  <div class="result-card">
    <div class="result-brand">
      <img src="/static/logo.png?v=6" alt="Guardian Eye">
      <span class="bn">GUARDIAN EYE</span>
    </div>
    <div class="result-ico">❌</div>
    <h1>فشلت عملية الدفع</h1>
    <p>يرجى المحاولة مرة أخرى أو التواصل مع الدعم الفني إذا تكررت المشكلة.</p>
    <div class="result-actions">
      <a href="/dashboard" class="btn btn-primary btn-lg">العودة إلى لوحة التحكم</a>
      <a href="/login" class="btn btn-ghost btn-lg">تسجيل الدخول</a>
    </div>
  </div>
</div>
</body>
</html>"""

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
