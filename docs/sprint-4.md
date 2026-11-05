# 🔔 Sprint 4: Alerts & Triggers Engine

> **الحالة:** مكتمل بنجاح ✅  
> **الهدف:** بناء محرك تنبيهات سعرية وفنية مستقل (Safe Domain Evaluation Engine) يدعم شروط المقارنة المنطقية دون دوال خطيرة، ويحفظ التنبيهات وحالاتها في SQLite، مع توفير أوامر CLI متكاملة للإنشاء والمراقبة والإلغاء.

---

## 🏗️ القرارات الهندسية والمعمارية (Architecture Decisions)

1. **Safe Condition Parser (بدون `eval`):**
   * تحليل نصوص المقارنة بأمان عبر مطابقة المعاملات (`>`, `<`, `>=`, `<=`, `==`) وتجريدها إلى كائن `AlertCondition`.
   * تجنب دوال التنفيذ الحي مثل `eval()` لتفادي ثغرات حقن الشيفرات الخبيثة (Code Injection).

2. **دورة حياة التنبيه (Alert Lifecycle):**
   * الحالات: `ACTIVE` -> `TRIGGERED` (أو `DISABLED`).
   * فور تحقق الشرط، يتم توثيق تاريخ الإطلاق بدقة `triggered_at` وتغيير الحالة لمنع تكرار الإطلاق في كل دورة فحص.

3. **استدامة التنبيهات في SQLite:**
   * إنشاء جدول مخصص `alerts` مع فهرس مركب `(status, pair)` لتسريع استرجاع التنبيهات النشطة لزوج معين أثناء الفحص.

4. **ربط المقاييس الفنية والسعرية:**
   * يدعم المحرك المقاييس السعرية اللحظية (`price`, `close`, `high`, `low`) بالإضافة لمخرجات المؤشرات الفنية المحسوبة من محرك Sprint 3 (`rsi`, `sma`, `ema`).

---

## 💻 الأوامر المضافة في الـ CLI

```bash
# 1. إضافة تنبيه سعري
forex alert add --pair EUR/USD --condition "price > 1.0900" --message "EUR Breakout"

# 2. إضافة تنبيه لمؤشر فني
forex alert add --pair EUR/USD --condition "rsi < 30" --message "RSI Oversold"

# 3. عرض التنبيهات المسجلة
forex alert list
forex alert list --active

# 4. فحص ومطابقة التنبيهات مع السوق
forex alert check
forex alert check --pair EUR/USD

# 5. حذف تنبيه بواسطة المعرف
forex alert delete --id <alert_id>
