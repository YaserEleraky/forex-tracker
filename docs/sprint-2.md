# 🌐 Sprint 2: Multi-Pairs, Timeframes & Bulk Historical Data

> **الحالة:** مكتمل بنجاح ✅  
> **الهدف:** تمكين النظام من تتبع أزواج عملات متعددة بالتوازي، دعم الأطر الزمنية المختلفة، الحفظ الجماعي فائق السرعة عبر SQLite، وإدارة حدود استهلاك الـ API عبر الـ Rate Limiting.

---

## 🏗️ القرارات الهندسية والمعمارية (Architecture Decisions)

1. **Domain Value Objects (`CurrencyPair` & `Interval`):**
   * عزل التحقق من صيغ أزواج العملات وتوحيدها قبل الوصول إلى طبقة الشبكة أو قاعدة البيانات.
   * استخدام `Interval Enum` مدعوماً بـ aliases لاحتواء الاختصارات الشائعة للمستخدمين (مثل `1h`, `1d`).

2. **الترقية لمعالجة الفترات الزمنية المتعددة (Schema Migration):**
   * تعديل الفهرس المركب في SQLite ليصبح `UNIQUE(pair, interval, timestamp)` لمنع تداخل شمعات الأطر المختلفة لنفس التوقيت.
   * دعم الترحيل الآلي للجدول عبر `ALTER TABLE` لمنع انهيار قواعد البيانات القديمة.

3. **الحفظ الدفعي السريع (Bulk Ingestion):**
   * اعتماد `cursor.executemany()` في دالة `save_candles_bulk()` لتنفيذ عمليات الحفظ في عملية كتابة واحدة (Single Disk Transaction).

4. **إدارة معدل الاستدعاء (Throttling / Rate Limiting):**
   * تطبيق تأخير زمني محسوب بين طلبات الأزواج المتتالية داخل طبقة الخدمة لحماية التطبيق من خطأ `HTTP 429 Too Many Requests`.

---

## 💻 الأوامر المحدثة والمضافة في الـ CLI

```bash
# 1. جلب بيانات بإطار زمني محدد
forex fetch --pairs EUR/USD --interval 1h --limit 5

# 2. جلب وتخزين دفعة عملات متعددة
forex fetch --pairs EUR/USD,GBP/USD,USD/JPY --interval 1day --limit 2

# 3. عرض جدول مقارنة فوري لعدة أزواج
forex watchlist --pairs EUR/USD,GBP/USD,USD/JPY

# 4. استعراض الشموع المحفوظة حسب الإطار الزمني
forex list --pair EUR/USD --interval 1h --limit 10
