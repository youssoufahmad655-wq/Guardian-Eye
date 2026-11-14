import os
import requests
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ═══════════════════════════════════════════════════════════
# البيانات الحساسة تُقرأ من متغيرات البيئة (.env) — لا تكتبها هنا
# ═══════════════════════════════════════════════════════════
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
# ═══════════════════════════════════════════════════════════


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str, enabled: bool = True):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = enabled and bool(bot_token) and bool(chat_id)
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    def _build_message(self, event, video_source=""):
        gps = event.get("gps") or {}
        lat = gps.get("latitude")
        lon = gps.get("longitude")
        dist = gps.get("distance_m")
        angle = gps.get("angle_deg")

        timestamp = event.get("timestamp", "?")
        track_id = event.get("track_id", "?")
        reason = event.get("reason", "Unknown")

        maps_line = ""
        if lat is not None and lon is not None:
            maps_url = f"https://www.google.com/maps?q={lat},{lon}"
            maps_line = f"\n🗺️ [الخريطة]({maps_url})\n📍 `{lat}, {lon}`"
            if dist is not None:
                maps_line += f"\n📏 المسافة: {dist}m"
            if angle is not None:
                maps_line += f"\n🧭 الزاوية: {angle}°"

        return (
            f"🚨 *سلوك مشبوه*\n"
            f"━━━━━━━━━━━━━━\n"
            f"🕐 الوقت: {timestamp}s\n"
            f"🎯 الشخص: {track_id}\n"
            f"⚠️ النوع: {reason}\n"
            f"📹 المصدر: `{video_source or 'direct'}`\n"
            f"━━━━━━━━━━━━━━"
            f"{maps_line}\n"
            f"━━━━━━━━━━━━━━\n"
            f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

    def send_event(self, event, video_source=""):
        if not self.enabled:
            return False
        try:
            resp = requests.post(self.base_url, json={
                "chat_id": self.chat_id,
                "text": self._build_message(event, video_source),
                "parse_mode": "Markdown",
            }, timeout=10)
            if resp.status_code == 200 and resp.json().get("ok"):
                return True
            print(f"[Telegram] Failed: {resp.text[:300]}")
            return False
        except Exception as e:
            print(f"[Telegram] Error: {e}")
            return False

    def send_events(self, events, video_source=""):
        return sum(1 for e in events if self.send_event(e, video_source))

    def send_test(self):
        if not self.enabled:
            print("[Telegram] Disabled")
            return False
        try:
            resp = requests.post(self.base_url, json={
                "chat_id": self.chat_id,
                "text": "✅ *اختبار ناجح!*\nالإشعارات تعمل.",
                "parse_mode": "Markdown",
            }, timeout=10)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text[:300]}")
            return resp.status_code == 200 and resp.json().get("ok")
        except Exception as e:
            print(f"Error: {e}")
            return False


if __name__ == "__main__":
    notifier = TelegramNotifier(BOT_TOKEN, CHAT_ID)
    print("Sending test message...")
    print(f"Test sent: {notifier.send_test()}")