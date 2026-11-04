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

detector = ShopliftingDetector()
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
        chargily = globals().get('chargily')

        amount = 1500
        product_resp = chargily.create_product(Product(name="Guardian Eye Subscription"))
        price_resp = chargily.create_price(
            Price(amount=amount, currency="dzd", product_id=product_resp["id"])
        )

        user = session.get('user', {})
        user_id = str(user.get('id', 'guest'))
        if not user_id.isascii():
            user_id = 'user_guest'

        success = url_for('payment_success', _external=True)
        failure = url_for('payment_failure', _external=True)

        checkout = Checkout(
            items=[{"price": price_resp["id"], "quantity": 1}],
            success_url=success,
            failure_url=failure,
            metadata={'user_id': user_id, 'plan': 'basic'}
        )
        checkout_resp = chargily.create_checkout(checkout)
        return jsonify({'checkout_url': checkout_resp['checkout_url']})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Payment error: ' + str(e)}), 500



@app.route('/payment/success')
def payment_success():
    return """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Payment Success</title></head>
<body style="font-family:sans-serif;text-align:center;padding:60px;background:#0f172a;color:#fff">
<h1 style="color:#22c55e">\u2705 \u062a\u0645 \u0627\u0644\u062f\u0641\u0639 \u0628\u0646\u062c\u0627\u062d!</h1>
<p>\u0634\u0643\u0631\u0627\u064b \u0644\u0627\u0634\u062a\u0631\u0627\u0643\u0643 \u0641\u064a Guardian Eye.</p>
<a href="/dashboard" style="display:inline-block;margin-top:20px;padding:12px 24px;background:#3b82f6;color:#fff;text-decoration:none;border-radius:8px">\u0627\u0644\u0639\u0648\u062f\u0629 \u0625\u0644\u0649 \u0644\u0648\u062d\u0629 \u0627\u0644\u062a\u062d\u0643\u0645</a>
</body></html>"""


@app.route('/payment/failure')
def payment_failure():
    return """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Payment Failed</title></head>
<body style="font-family:sans-serif;text-align:center;padding:60px;background:#0f172a;color:#fff">
<h1 style="color:#ef4444">\u274c \u0641\u0634\u0644 \u0627\u0644\u062f\u0641\u0639</h1>
<p>\u064a\u0631\u062c\u0649 \u0627\u0644\u0645\u062d\u0627\u0648\u0644\u0629 \u0645\u0631\u0629 \u0623\u062e\u0631\u0649.</p>
<a href="/dashboard" style="display:inline-block;margin-top:20px;padding:12px 24px;background:#3b82f6;color:#fff;text-decoration:none;border-radius:8px">\u0627\u0644\u0639\u0648\u062f\u0629</a>
</body></html>"""

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
