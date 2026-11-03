# Guardian Eye | عين الحارس

> نظام ذكي لكشف السرقة في المتاجر باستخدام الذكاء الاصطناعي، مع تحديد الموقع الجغرافي (GPS)، إشعارات فورية، وأدلة فيديو.

## نظرة عامة

Guardian Eye يحلل بث الفيديو من كاميرات المراقبة، يكتشف السلوكيات المشبوهة، يحولها إلى إحداثيات GPS، يحفظ مقاطع فيديو كأدلة، ويُرسل إشعارات فورية عبر Telegram.

## الميزات (12 ميزة)

| # | الميزة | التقنية |
| :--- | :--- | :--- |
| 1 | كشف الأشخاص | YOLOv8 |
| 2 | تتبع متعدد | DeepSORT |
| 3 | كشف التلكؤ | Rule-based |
| 4 | كشف التستر | YOLOv8-Pose |
| 5 | تحويل البكسل إلى GPS | GeoMapper |
| 6 | قاعدة بيانات | SQLite |
| 7 | إشعارات Telegram | Bot API |
| 8 | لوحة تحكم + خريطة | Flask + Leaflet |
| 9 | تسجيل دخول OAuth | Authlib |
| 10 | حفظ مقاطع الفيديو | imageio-ffmpeg |
| 11 | كشف الزوار المتكررين | CLIP |
| 12 | لوحة إحصائيات | Chart.js |

## التثبيت

    git clone https://github.com/youssoufahmad655-wq/Guardian-Eye.git
    cd Guardian-Eye
    python -m venv venv
    .\venv\Scripts\activate
    pip install -r requirements.txt
    python app.py

افتح: http://127.0.0.1:5000

## API

- POST /api/detect : إرسال فيديو
- GET /api/events : قائمة الأحداث
- GET /api/events/count : العدد الإجمالي
- GET /api/analytics : إحصائيات متقدمة
- GET /clips/<filename> : مشاهدة مقطع
- GET /dashboard : لوحة التحكم
- GET /stats : الإحصائيات

## الاعتبارات القانونية (الجزائر)

- الالتزام بالقانون 18-07 لحماية المعطيات الشخصية.
- الحصول على تراخيص قبل تركيب الكاميرات.
- وضع لافتات تُعلم بوجود مراقبة ذكية.
- القرار النهائي بيد الإنسان.

## الترخيص

MIT License — راجع LICENSE

## التواصل

- GitHub: https://github.com/youssoufahmad655-wq
- المستودع: https://github.com/youssoufahmad655-wq/Guardian-Eye

---

Guardian Eye — عين لا تنام، وحارس لا يخطئ.
