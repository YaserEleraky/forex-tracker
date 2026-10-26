from enum import Enum


class Interval(str, Enum):
    """
    الأطر الزمنية القياسية المتوافقة مع مزودي البيانات المالية.
    وراثة str تسمح بمقارنتها وتمريرها مباشرة كنصوص في الـ API وقواعد البيانات.
    """

    M1 = "1min"
    M5 = "5min"
    M15 = "15min"
    M30 = "30min"
    H1 = "1h"
    H4 = "4h"
    D1 = "1day"
    W1 = "1week"
    M = "1month"

    @classmethod
    def from_str(cls, value: str) -> "Interval":
        """
        تحويل النص المدخل إلى كائن Interval مع دعم اختصارات شائعة.
        """
        val_clean = value.strip().lower()

        # خريطة لترجمة الاختصارات الشائعة من المستخدم
        aliases = {
            "1m": cls.M1,
            "1min": cls.M1,
            "5m": cls.M5,
            "5min": cls.M5,
            "15m": cls.M15,
            "15min": cls.M15,
            "30m": cls.M30,
            "30min": cls.M30,
            "1h": cls.H1,
            "4h": cls.H4,
            "1d": cls.D1,
            "1day": cls.D1,
            "day": cls.D1,
            "1w": cls.W1,
            "1week": cls.W1,
            "1mo": cls.M,
            "1month": cls.M,
        }

        if val_clean in aliases:
            return aliases[val_clean]

        valid_values = [e.value for e in cls]
        raise ValueError(
            f"الإطار الزمني '{value}' غير مدعوم. الأطر المدعومة: {', '.join(valid_values)}"
        )
