# سياسة الخصوصية | Privacy Policy

**آخر تحديث:** 15 نوفمبر 2026
**الجهة المطورة:** Youssouf Ahmad (يوسف أحمد) — مشروع مفتوح المصدر تحت رخصة MIT.

---

## 🇩🇿 النسخة العربية

### 1. مقدمة
نظام **Guardian Eye** هو أداة مفتوحة المصدر لتحليل بث الفيديو وكشف السلوكيات المشبوهة في المتاجر. نحن نلتزم بحماية خصوصية الأفراد والامتثال للقانون الجزائري **18-07** المتعلق بحماية المعطيات الشخصية.

### 2. البيانات التي يعالجها النظام
- **مقاطع الفيديو / البث المباشر:** تُحلل مؤقتاً لاكتشاف الأحداث، ولا تُحفظ إلا المقاطع القصيرة المرتبطة بحدث مشبوه (6 ثوانٍ افتراضياً).
- **إحداثيات GPS:** تُحسب من موقع الكاميرا وزاوية رؤيتها، وتُخزن مع الحدث لتحديد مكانه.
- **بيانات وصفية:** الوقت، رقم التتبع (Track ID)، نوع السلوك (تلكؤ/تستر)، ولا تُخزن أي بيانات تعريف شخصية (مثل الوجه أو الاسم).
- **إشعارات Telegram:** تُرسل إلى قناة يحددها مشغل النظام، وتحتوي على إحداثيات ومعلومات الحدث.
- **الزوار المتكررون:** يستخدم النظام بصمات بصرية (CLIP embeddings) لتمييز الزوار العائدين، دون التعرف على الوجه.

### 3. الأساس القانوني للمعالجة
- **الموافقة:** لا يعمل النظام إلا في بيئة يصرح فيها مالك المكان بوجود كاميرات مراقبة.
- **المصلحة المشروعة:** منع السرقة وحماية الممتلكات.
- **الالتزام القانوني:** الامتثال للقانون 18-07 والقوانين ذات الصلة.

### 4. مدة الاحتفاظ بالبيانات
- **مقاطع الفيديو:** تحفظ لمدة أقصاها 30 يوماً، ثم تُحذف تلقائياً (قابلة للتعديل من قبل المشغل).
- **قاعدة البيانات (SQLite):** تحتفظ بالأحداث الوصفية فقط، ويمكن حذفها في أي وقت.
- **إشعارات Telegram:** تبقى في تطبيق Telegram حسب إعدادات المستخدم.

### 5. حقوق الأفراد
- **الحق في الوصول:** يمكن لأي شخص طلب معرفة الأحداث المسجلة عنه.
- **الحق في التصحيح أو الحذف:** يمكن طلب حذف أي حدث أو مقطع فيديو.
- **الحق في الاعتراض:** يمكن الاعتراض على المعالجة بإبلاغ مشغل النظام.

### 6. الأمن
- تُخزن البيانات محلياً على جهاز المتجر (SQLite + ملفات فيديو).
- لا تُرسل أي بيانات إلى خوادم خارجية إلا إشعارات Telegram (إذا فُعلت).
- يمكن تشغيل النظام بالكامل دون اتصال بالإنترنت.

### 7. مسؤولية المشغل
- **مشغل النظام (صاحب المتجر)** هو المسؤول عن:
  - الحصول على التراخيص اللازمة من السلطات المختصة.
  - وضع لافتات واضحة تُعلم بوجود كاميرات مراقبة ذكية.
  - احترام حقوق الأفراد والامتثال للقانون 18-07.
- **المطور (المساهم في المشروع المفتوح المصدر)** لا يتحمل أي مسؤولية عن سوء استخدام النظام.

### 8. التعديلات
قد نحدّث هذه السياسة من وقت لآخر. سيتم نشر التحديثات في هذا الملف.

### 9. التواصل
لأي استفسار: `ahmadyoussouf669@gmail.com`

---

## 🇬🇧 English Version

### 1. Introduction
**Guardian Eye** is an open-source video analytics tool that detects suspicious behavior in retail stores. We are committed to protecting privacy and complying with **Algerian Law 18-07** on personal data protection.

### 2. Data Processed
- **Video streams:** analyzed in real-time; only short clips (6s) tied to suspicious events are saved.
- **GPS coordinates:** computed from camera location and field of view.
- **Metadata:** timestamp, track ID, behavior type (loitering/concealment). No personally identifiable information (PII) is stored.
- **Telegram alerts:** sent to a channel configured by the operator.
- **Recurring visitors:** uses CLIP embeddings (no facial recognition).

### 3. Legal Basis
- **Consent** from the premises owner.
- **Legitimate interest** in theft prevention.
- **Legal obligation** under Law 18-07.

### 4. Retention
- Video clips: max 30 days (configurable).
- SQLite events: indefinite (deletable).
- Telegram: per user settings.

### 5. Individual Rights
- Right to access, rectification, erasure, and objection.

### 6. Security
- Data stored locally (SQLite + video files).
- No external servers except Telegram (optional).
- Fully offline capable.

### 7. Operator Responsibility
- The **store operator** is responsible for:
  - Obtaining required authorizations.
  - Posting clear signage.
  - Complying with Law 18-07.
- **The open-source developer** bears no liability for misuse.

### 8. Changes
Updates will be posted in this file.

### 9. Contact
`ahmadyoussouf669@gmail.com`

---

**© 2026 Guardian Eye — MIT License**
