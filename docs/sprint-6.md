# 📈 Sprint 6: Strategy Backtesting

> **الحالة:** مكتمل بنجاح ✅  
> **الهدف:** بناء محاكي اختبار استراتيجيات التداول التاريخية (Backtesting Engine) على بيانات الشموع المخزنة محلياً في SQLite، ونمذجة الصفقات، وحساب الأرباح والخسائر ومقاييس الأداء المالي دون مخاطرة برأس مال حقيقي.

---

## 🏗️ القرارات الهندسية والمعمارية (Architecture Decisions)

1. **نمذجة الصفقات (Domain Modeling):**
   * كائن `Trade`: يمثل كل عملية تداول (`OPEN` -> `CLOSED`)، ويتتبع سعر وتوقيت الدخول والخروج مع حساب الأرباح والخسائر (`PnL`) بدقة باستخدام نوع `Decimal`.
   * كائن `SignalType`: تصنيف الإشارات الفنية إلى `BUY`, `SELL`, و `HOLD`.

2. **منع تحيز النظر للمستقبل (No Lookahead Bias):**
   * دالة `generate_signal` تستقبل مؤشر الشمعة `index` وتقتطع البيانات فقط حتى تلك الشمعة (`candles[:index+1]`)، لضمان اتخاذ القرار بناءً على ما كان معلوماً في تلك اللحظة فقط.

3. **استراتيجية تقاطع المتوسطات (SMA Crossover):**
   * تطبيق كلاسيكي لتقاطع المتوسط السريع والبطيء (Golden Cross / Death Cross).
   * التحقق المسبق من صحة الفترات (`fast_period < slow_period`).

4. **مقاييس الأداء المالي (Performance Metrics):**
   * حساب إجمالي الصفقات (Total Trades).
   * نسبة الصفقات الرابحة (Win Rate %).
   * العائد الإجمالي على رأس المال (ROI %).
   * أقصى هبوط تاريخي للمحفظة (Max Drawdown %).
   * عامل الربحية (Profit Factor = Gross Profit / Gross Loss).

---

## 💻 الأوامر المضافة في الـ CLI

```bash
# تشغيل المحاكاة بالإعدادات الافتراضية (Fast=10 / Slow=30)
forex backtest --pair EUR/USD --interval 1day --limit 100

# تخصيص الفترات ورأس المال وحجم الصفقة
forex backtest --pair EUR/USD --interval 1day --limit 100 --fast 5 --slow 20 --capital 20000 --size 15000
