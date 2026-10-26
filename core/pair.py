from __future__ import annotations
from dataclasses import dataclass
import re
from core.exceptions import ValidationError


@dataclass(frozen=True)
class CurrencyPair:
    """
    كائن غير قابل للتعديل يمثل زوج العملات ويفككه لعملة الأساس وعملة التسعير.
    """

    base: str
    quote: str

    def __post_init__(self) -> None:
        # التحقق من أن الرموز مكونة من 3 أحرف أبجدية ISO قياسية
        if not (self.base.isalpha() and len(self.base) == 3):
            raise ValidationError(f"رمز عملة الأساس غير صالح: {self.base}")
        if not (self.quote.isalpha() and len(self.quote) == 3):
            raise ValidationError(f"رمز عملة التسعير غير صالح: {self.quote}")
        if self.base == self.quote:
            raise ValidationError(
                "لا يمكن لعملة الأساس وعملة التسعير أن تكونا نفس العملة"
            )

    @property
    def symbol(self) -> str:
        """الصيغة الموحدة للزوج المستخدمة في العرض والـ API: EUR/USD."""
        return f"{self.base}/{self.quote}"

    @property
    def raw_symbol(self) -> str:
        """الصيغة المدمجة للزوج بدون فواصل: EURUSD."""
        return f"{self.base}{self.quote}"

    def __str__(self) -> str:
        return self.symbol

    @classmethod
    def from_string(cls, value: str) -> "CurrencyPair":
        """
        تحليل وتوحيد أي مدخل نصي إلى كائن CurrencyPair.
        يدعم: 'EUR/USD', 'EUR-USD', 'EUR_USD', 'EURUSD', 'eur/usd'.
        """
        if not value or not isinstance(value, str):
            raise ValidationError("يجب إدخال نص يمثل زوج العملات.")

        # تنظيف النص وإزالة المسافات
        cleaned = value.strip().upper()

        # حالة وجود فاصل: /, -, _
        split_match = re.split(r"[/_\-\s]+", cleaned)
        if len(split_match) == 2:
            base, quote = split_match[0], split_match[1]
            return cls(base=base, quote=quote)

        # حالة الرمز المدمج بدون فواصل (مثل EURUSD بطول 6 أحرف)
        if len(cleaned) == 6 and cleaned.isalpha():
            return cls(base=cleaned[:3], quote=cleaned[3:])

        raise ValidationError(
            f"صيغة زوج العملات '{value}' غير صحيحة. أمثلة مقبولة: EUR/USD أو EURUSD"
        )
