# ⚡ Sprint 1: PRICE (Vertical Slice MVP)

## 🎯 الهدف المعماري (Sprint Goal)
بناء أول شريحة رأسية وظيفية كاملة (End-to-End Vertical Slice) تتيح للمستخدم جلب السعر الفوري لزوج العملات (`EUR/USD`)، وحفظ الشموع في قاعدة بيانات SQLite محلية، واستعراضها عبر أوامر سطر الأوامر.

---

## 🏗️ الأنماط المعمارية المطبقة (Design Patterns)

| النمط | المكون المعني | الغرض الهندسي |
| :--- | :--- | :--- |
| **Immutable Value Object** | `core/candle.py` | تمثيل الشمعة السعرية ككائن غير قابل للتعديل بعد إنشائه (`frozen=True`) مع دقة `Decimal`. |
| **Gateway / HTTP Wrapper** | `api/client.py` | عزل مكتبة `requests` وتطبيق مهلة انتظار موحدة (`Timeout`) وتوحيد ترجمة أخطاء الشبكة. |
| **Adapter Pattern** | `api/sources/twelvedata.py` | ترجمة لغة وخصائص TwelveData API وتحويل الردود الخام إلى كائنات `Candle`. |
| **Persistence / Repository** | `storage/sqlite_storage.py` | تخزين دائم في SQLite مع الحفاظ على الدقة المالية عبر نصوص `TEXT` وفهارس مركبة لمنع التكرار. |
| **Orchestration Service Layer**| `services/forex_service.py` | التنسيق بين مزود البيانات والتخزين الدائم وفصل واجهة العرض تماماً عن منطق النظام. |

---

## 📦 المكونات التي تم بناؤها

### 1. كائن الشمعة المالي (`core/candle.py`)
- استخدام `Decimal` بدلاً من `float` لتفادي أخطاء التقريب المالي الثنائي.
- التحقق الذاتي في `__post_init__` من العلاقات المنطقية للأسعار ($High \ge Low$ و $High \ge Open/Close$).
- مصنع البيانات `Candle.from_dict` يدعم صيغ ISO 8601 القياسية (`T` والمسافات).
- دالة التحويل لقاموس `Candle.to_dict` لتسهيل الحفظ.

### 2. طبقة الشبكة ومحول البيانات (`api/`)
- `HttpClient`: عميل GET عام بمعالجة تلقائية لأخطاء المهلة والاتصال.
- `TwelveDataSource`: فحص أخطاء الردود وحسابات مفاتيح الـ API ودعم وضع الـ `demo`.

### 3. التخزين الدائم في SQLite (`storage/sqlite_storage.py`)
- إنشاء جدول `candles` تلقائياً مع فهرس مركب: `UNIQUE(pair, timestamp) ON CONFLICT REPLACE`.
- دوال التخزين المعتمدة على `to_dict` و `from_dict`:
  - `save_candle(candle)`
  - `get_candles(pair, limit)`

### 4. طبقة التنسيق والخدمة (`services/forex_service.py`)
- `get_current_price(pair)`: إرجاع أحدث سعر إغلاق فوري.
- `fetch_and_store(pair, limit)`: جلب الشموع وحفظها تلقائياً بالدفعات.
- `get_history(pair, limit)`: استرجاع الشموع المخزنة محلياً.

### 5. أوامر الـ CLI الجديدة (`cli/commands.py` & `cli/parser.py`)
- `forex price --pair EUR/USD`: عرض السعر اللحظي المباشر.
- `forex fetch --pair EUR/USD --limit 5`: جلب وتخزين الشموع.
- `forex list --pair EUR/USD --limit 10`: عرض الشموع المخزنة في جدول منسق.

---

## 💡 دروس هندسية مستفادة (Key Architectural Lessons)
1. **معالجة صيغ التواريخ القياسية:** الالتزام بـ ISO 8601 وقبول حرف `T` الفاصل بين التاريخ والوقت.
2. **ضبط حزم التثبيت في `pyproject.toml`:** تضمين المجلدات الجديدة (`api*` و `services*`) في إعدادات الحزمة لضمان تعرف بايثون عليها.
3. **عزل الاختبارات بالمحاكاة (Mocking):** اختبار `ForexService` عبر محاكاة الـ API وقاعدة بيانات `:memory:` لتشغيل الاختبارات دون إنترنت وسرعة فائقة.

---

## 🧪 الاختبارات المؤتمتة (`tests/test_price_mvp.py`)
- اختبارات القيود المالية والـ Validation للشمعة.
- اختبارات عمليات الحفظ والاسترجاع في SQLite بالذاكرة.
- اختبارات التنسيق الكامل داخل طبقة الخدمة `ForexService`.