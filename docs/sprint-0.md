# 🏛️ Sprint 0: Foundation Layer

## 🎯 الهدف المعماري (Sprint Goal)
تأسيس البنية التحتية الصلبة للمشروع (Core Infrastructure) وتطبيق مبادئ الكود النظيف والتصميم المعماري المتين، دون استباق للأحداث مع الالتزام الصارم بمبدأ **YAGNI (You Aren't Gonna Need It)**.

---

## 🏗️ الأنماط المعمارية المطبقة (Design Patterns)

| النمط | المكون المعني | الغرض الهندسي |
| :--- | :--- | :--- |
| **Singleton Pattern** | `core/config.py` | ضمان نقطة وصول موحدة لإعدادات التطبيق ومنع قراءة ملف `config.json` المتكررة من القرص. |
| **Exception Hierarchy** | `core/exceptions.py` | شجرة أخطاء موحدة ترث من كلاس أساسي (`ForexError`) لتمكين التقاط الأخطاء المخصصة بدقة. |
| **Handler Chain** | `core/logger.py` | نظام تسجيل مركزي يوجه المخرجات إلى الطرفية (Console) وملف السجلات (`logs/app.log`) بالتوازي. |
| **Decorator Pattern** | `utils/decorators.py` | أداة تشخيصية (`@timer`) لحساب زمن استجابة الدوال دون تلويث منطقها الداخلي. |
| **Repository / ABC** | `storage/base.py` | واجهة تجريدية عامة لطبقة التخزين تعتمد على `Storage(ABC)` وتلزم أي محرك تخزين بتطبيق دورة حياة الاتصال. |
| **Command Pattern** | `cli/parser.py` & `cli/commands.py` | فصل قراءة وتحليل المدخلات عن تنفيذ الأوامر، مع تسجيل أمر النظام الطرفي `forex`. |

---

## 📦 المكونات التي تم بناؤها

### 1. إدارة الإعدادات (`core/config.py`)
- تحميل الإعدادات من `config.json`.
- دعم التجاوز عبر متغيرات البيئة (`Environment Variables`).
- تأمين الكائن عبر نمط الـ Singleton.

### 2. شجرة الاستثناءات (`core/exceptions.py`)
- `ForexError`: الاستثناء الأساسي للنظام.
- `ConfigError`: أخطاء ملفات وقيم الإعدادات.
- `StorageError`: أخطاء قاعدة البيانات والتخزين.
- `ValidationError`: أخطاء التحقق من البيانات والمدخلات.
- `NetworkError`: مشاكل الاتصال والشبكة.
- `APIError`: أخطاء الخوادم الخارجية ومزودي البيانات.

### 3. نظام السجلات والقياس (`core/logger.py` & `utils/decorators.py`)
- تهيئة موحدة مع صيغة طابع زمني دقيقة ومستوى التسجيل (`INFO`, `ERROR`, `WARNING`).
- ديكوريتور قياس الأداء `@timer`.

### 4. تجريد التخزين والتنفيذ بالذاكرة (`storage/base.py` & `storage/memory_storage.py`)
- عقد تجريدي يتضمن: `connect()`, `disconnect()`, `is_connected()`.
- محرك تخزين في الذاكرة (`MemoryStorage`) لأغراض الاختبارات السريعة.

### 5. واجهة سطر الأوامر الأساسية (`cli/`)
- إعداد `argparse` لدعم الأوامر الفرعية (Subcommands).
- الأوامر المنجزة: `forex version`, `forex status`.

---

## 🧪 الاختبارات وضمان الجودة (`tests/test_foundation.py`)
- اختبار تماثل نسخة الـ Singleton لمدير الإعدادات.
- اختبار دورة حياة اتصال التخزين في الذاكرة.
- اختبار قياس زمن الديكوريتور وعدم تعديله لمخرجات الدوال الأصلية.