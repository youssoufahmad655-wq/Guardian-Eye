import os
from collections import Counter
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, abort, send_from_directory
from flask_cors import CORS
from functools import wraps
from datetime import datetime

from shoplifting_detector import ShopliftingDetector
from database import EventDatabase
from notifier import TelegramNotifier, BOT_TOKEN, CHAT_ID
from auth import init_oauth, oauth

app = Flask(__name__)
CORS(app)

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


@app.route('/api/detect', methods=['POST'])
def detect_shoplifting():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400

    video_file = request.files['video']
    video_path = os.path.join(
        UPLOAD_FOLDER,
        f'video_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp4'
    )
    video_file.save(video_path)

    results = detector.process_video(video_path)

    saved_count = 0
    notified_count = 0
    if results.get('suspicious_events'):
        saved_count = db.insert_events(
            results['suspicious_events'],
            video_source=os.path.basename(video_path)
        )
        notified_count = notifier.send_events(
            results['suspicious_events'][:10],
            video_source=os.path.basename(video_path)
        )

    results['saved_to_db'] = saved_count
    results['telegram_notifications_sent'] = notified_count
    return jsonify(results)


@app.route('/api/train', methods=['POST'])
def train_model():
    if 'video' not in request.files or 'annotations' not in request.files:
        return jsonify({'error': 'Both video and annotations are required'}), 400

    video_file = request.files['video']
    annotations_file = request.files['annotations']
    video_path = os.path.join(TRAINING_FOLDER, f'train_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp4')
    annotations_path = os.path.join(TRAINING_FOLDER, f'annotations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    video_file.save(video_path)
    annotations_file.save(annotations_path)
    return jsonify(detector.train(video_path, annotations_path))


@app.route('/api/stats', methods=['GET'])
def get_stats():
    return jsonify({
        'total_detections': detector.total_detections,
        'suspicious_activities': detector.suspicious_activities,
        'model_version': detector.model_version
    })


@app.route('/api/events', methods=['GET'])
def get_events():
    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
    except ValueError:
        return jsonify({'error': 'limit and offset must be integers'}), 400

    events = db.get_events(limit=limit, offset=offset)
    total = db.get_events_count()
    return jsonify({
        'total': total,
        'limit': limit,
        'offset': offset,
        'returned': len(events),
        'events': events
    })


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


@app.route('/clips/<path:filename>')
@login_required
def serve_clip(filename):
    return send_from_directory('clips', filename)

@app.route('/api/analytics', methods=['GET'])
@login_required
def analytics():
    events = db.get_events(limit=1000)
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
    return jsonify({
        'total': len(events),
        'hourly': dict(hourly),
        'reasons': dict(reasons),
        'top_tracks': top_tracks,
        'recurring': recurring,
        'unique_tracks': unique_tracks,
    })


@app.route('/stats')
@login_required
def stats_page():
    return render_template('stats.html')



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)