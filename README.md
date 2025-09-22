# نظام البنك الآمن - Secure Bank System

## نظرة عامة
نظام بنكي آمن مطور بلغة Python باستخدام Flask، يطبق أعلى معايير الأمان والحماية من الهجمات الإلكترونية. المشروع مصمم لمادة البرمجة الآمنة ويلبي جميع المتطلبات الأكاديمية.

## المميزات الأمنية الرئيسية

###  الحماية من الهجمات
- **Anti-XSS**: حماية من هجمات Cross-Site Scripting
- **CSRF Protection**: حماية من هجمات Cross-Site Request Forgery  
- **SQL Injection Prevention**: منع حقن أكواد SQL الضارة
- **Path Traversal Protection**: حماية من اختراق المسارات

###  المصادقة والتفويض
- **Strong Password Policy**: سياسة كلمات مرور قوية
- **Account Lockout**: قفل الحساب بعد 3 محاولات فاشلة
- **Session Management**: إدارة آمنة للجلسات مع انتهاء صلاحية
- **Rate Limiting**: تحديد معدل الطلبات (100 طلب/ساعة افتراضياً، و5 محاولات/دقيقة لمسارات المصادقة، مع استثناء المسؤولين الموثقين)

###  التشفير وحماية البيانات
- **Password Hashing**: تشفير قوي لكلمات المرور (PBKDF2-SHA256)
- **Data Encryption**: تشفير البيانات الحساسة
- **Secure Sessions**: جلسات محمية بـ HTTPOnly و Secure flags
- **Input Sanitization**: تنظيف وتحقق من جميع المدخلات

## متطلبات النظام

### البرامج المطلوبة
- Python 3.8+
- SQLite3
- Redis (اختياري للـ Rate Limiting)

### المكتبات المطلوبة
```
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-WTF==1.1.1
Flask-Login==0.6.3
Flask-Limiter==3.5.0
bcrypt==4.0.1
cryptography==41.0.7
bleach==6.1.0
```

## التثبيت والتشغيل

### 1. إعداد البيئة الافتراضية
```bash
cd D:\venv\secure_bank_system
python -m venv venv
venv\Scripts\activate  # على Windows
```

### 2. تثبيت المتطلبات
```bash
pip install -r requirements.txt
```

### 3. إعداد متغيرات البيئة (اختياري)
```bash
set SECRET_KEY=your-secret-key-here
set ENCRYPTION_KEY=your-encryption-key-here
```

### 4. تشغيل التطبيق
```bash
python app.py
```

### 5. الوصول للتطبيق
افتح المتصفح وانتقل إلى: `http://127.0.0.1:5000`

## هيكل المشروع

```
secure_bank_system/
├── app.py                      # تهيئة التطبيق، CSRF، Rate Limiter، ترويسات الأمان، تسجيل Blueprints
├── config.py                   # إعدادات التطبيق والأمان
├── requirements.txt            # المكتبات المطلوبة
├── README.md                   # هذا الملف
├── instance/
│   └── secure_bank.db          # قاعدة بيانات SQLite للتطوير
├── models/                     # نماذج قاعدة البيانات (SQLAlchemy)
│   ├── __init__.py
│   └── user.py                 # نماذج: User, Account, Transaction, LoginAttempt
├── routes/                     # مسارات التطبيق (Blueprints)
│   ├── __init__.py
│   ├── auth.py                 # مصادقة (تسجيل/دخول/خروج)
│   ├── dashboard.py            # لوحة المستخدم
│   └── admin.py                # لوحة الإدارة والإجراءات الإدارية
├── templates/                  # قوالب HTML (Jinja2)
│   ├── base.html               # القالب الأساسي + meta csrf-token
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   ├── dashboard/
│   │   ├── index.html
│   │   ├── transfer.html
│   │   ├── account_details.html
│   │   └── transactions.html
│   └── admin/
│       ├── dashboard.html
│       ├── users.html
│       ├── user_details.html
│       ├── accounts.html
│       ├── transactions.html
│       ├── security.html
│       ├── system_logs.html
│       └── reports.html
└── static/                     # الملفات الثابتة
    ├── css/
    │   └── style.css
    └── js/
        └── main.js
```

## الاستخدام

### إنشاء حساب جديد
1. انتقل إلى `/auth/register`
2. املأ النموذج بالمعلومات المطلوبة
3. تأكد من أن كلمة المرور تلبي المتطلبات الأمنية

### تسجيل الدخول
1. انتقل إلى `/auth/login`
2. أدخل اسم المستخدم وكلمة المرور
3. سيتم قفل الحساب بعد 3 محاولات فاشلة

### إنشاء حساب بنكي
1. من لوحة التحكم، اضغط "إنشاء حساب جديد"
2. اختر نوع الحساب (جاري أو توفير)
3. سيتم إنشاء رقم حساب فريد تلقائياً

### تحويل الأموال
1. انتقل إلى صفحة التحويل
2. اختر الحساب المرسل
3. أدخل رقم الحساب المستقبل (10 أرقام)
4. أدخل المبلغ والوصف
5. تأكيد التحويل

### ملاحظة حول CSRF في طلبات fetch
- عند استخدام أزرار الإدارة (مثل تعطيل/تفعيل مستخدم/حساب) يتم إرسال طلبات POST عبر fetch.
- لضمان نجاح الطلب مع CSRFProtect:
  - يتم قراءة التوكن من `meta[name="csrf-token"]` في `templates/base.html`.
  - يُرسل في الهيدر `X-CSRFToken` مع `credentials: 'same-origin'` لإرسال الكوكيز.

## المعايير الأمنية المطبقة

### Security Requirements Engineering
- **4 أصول محمية**: بيانات المستخدمين، معلومات الحسابات، بيانات المصادقة، سجلات المعاملات
- **4 تهديدات رئيسية**: SQL Injection, XSS, Brute Force, Session Hijacking
- **4 متطلبات أمنية**: تشفير البيانات، مصادقة قوية، حماية من الحقن، إدارة جلسات آمنة

### Threat Modeling
- **STRIDE Model**: تطبيق شامل لجميع فئات التهديدات
- **DREAD Assessment**: تقييم المخاطر مع درجات عالية للتهديدات الحرجة

### Secure Coding Practices
- **Input Validation**: تحقق شامل من جميع المدخلات
- **Output Encoding**: تشفير المخرجات لمنع XSS
- **Parameterized Queries**: استخدام SQLAlchemy ORM
- **Error Handling**: معالجة آمنة للأخطاء بدون كشف معلومات حساسة

## الحسابات الافتراضية

### حساب المدير
- **اسم المستخدم**: admin
- **كلمة المرور**: Admin123!
- **البريد الإلكتروني**: admin@securebank.com

## الاختبار

### اختبار الأمان
```bash
# اختبار SQL Injection
# جرب إدخال: admin'; DROP TABLE users; --

# اختبار XSS
# جرب إدخال: <script>alert('XSS')</script>

# اختبار Brute Force
# جرب 4 محاولات دخول خاطئة متتالية
```

### اختبار الوظائف
1. إنشاء حساب مستخدم جديد
2. تسجيل الدخول والخروج
3. إنشاء حسابات بنكية متعددة
4. تنفيذ تحويلات مالية
5. عرض سجل المعاملات

## الأمان في الإنتاج

### إعدادات مهمة للإنتاج
```python
# في config.py
DEBUG = False
SESSION_COOKIE_SECURE = True
WTF_CSRF_ENABLED = True
```

### روابط التوثيق
- توثيق شامل (إنجليزي): `docs/Secure_Bank_System_Documentation.md`
- توثيق شامل (عربي): `docs/Secure_Bank_System_Documentation_AR.md`

### متغيرات البيئة المطلوبة
```
SECRET_KEY=strong-random-secret-key
ENCRYPTION_KEY=strong-encryption-key
DATABASE_URL=sqlite:///production.db
RATELIMIT_STORAGE_URL=redis://localhost:6379
```

## المساهمة والتطوير

### إضافة ميزات جديدة
1. إنشاء branch جديد
2. تطبيق معايير الأمان
3. إضافة اختبارات الأمان
4. تحديث التوثيق

### معايير الكود
- استخدام SQLAlchemy ORM دائماً
- تنظيف جميع المدخلات
- إضافة CSRF tokens لجميع النماذج
- تسجيل العمليات الحساسة

## الدعم والمساعدة

### الملفات المرجعية
- `SECURITY_DOCUMENTATION.md`: التوثيق الأمني الشامل
- `config.py`: جميع الإعدادات الأمنية
- `utils/security.py`: أدوات الأمان المساعدة

### المشاكل الشائعة
1. **خطأ في قاعدة البيانات**: تأكد من تشغيل `python app.py` لإنشاء الجداول
2. **مشكلة في Rate Limiting**: تأكد من تشغيل Redis أو استخدم `memory://`
3. **مشكلة في التشفير**: تأكد من تعيين `ENCRYPTION_KEY`

### روابط التوثيق
- [توثيق الأمان (PDF)](docs/Secure_Bank_System_Documentation.pdf)


## الترخيص
هذا المشروع مخصص للأغراض التعليمية لمادة البرمجة الآمنة.


## المطور
- الاسم: Sakhr Mohammed Hussein Hadi Farasha
- البريد: [ABOFARESMF34@gmail.com](mailto:ABOFARESMF34@gmail.com)
- GitHub: [sakhrm410f](https://github.com/sakhrm410f)

---
**تم تطوير هذا المشروع وفقاً لأعلى معايير الأمان والبرمجة الآمنة**
