# دليل استخدام Guardian Eye

## 1. التشغيل

    cd C:\Users\ahmad\Downloads\ShopliftingDetection
    .\venv\Scripts\activate
    python app.py

افتح: http://127.0.0.1:5000

## 2. إرسال فيديو

    curl.exe -X POST -F "video=@test.mp4" http://127.0.0.1:5000/api/detect -o result.json

## 3. لوحات التحكم

- لوحة التحكم: http://127.0.0.1:5000/dashboard
- الإحصائيات: http://127.0.0.1:5000/stats

## 4. إعدادات مهمة

- موقع الكاميرا: shoplifting_detector.py -> GeoMapper(...)
- عتبة التلكؤ: self.loitering_threshold = 3
- عتبة التستر: concealment_detector.py -> distance_threshold=50
- عتبة الزوار المتكررين: visitor_detector.py -> similarity_threshold=0.85

## 5. الدعم

https://github.com/youssoufahmad655-wq/Guardian-Eye
