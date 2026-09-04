"""
===========================================================
أداة تحليل وتوقع الدورات الزمنية لأسهم ناسداك
Stock Cycle Analyzer & Predictor
===========================================================

الفكرة:
--------
كل سهم يمر بدورات زمنية متكررة (تقريبًا) بنفس عدد الأشهر،
والقمة (Top) تظهر عادة في نفس "رقم الشهر" تقريبًا داخل كل دورة.

مثال (تسلا TSLA):
- الدورة 1: بدأت مارس 2020 → انتهت مارس 2024   (طول الدورة = 49 شهر)
- القمة كانت في الشهر رقم 20 من الدورة (أكتوبر 2021)
- الدورة 2 (المتوقعة): تبدأ أبريل 2024 → تنتهي أبريل 2028
- القمة المتوقعة في نفس رقم الشهر (20) = نوفمبر 2025

هذا الكود يقوم بهذا الحساب تلقائيًا لأي عدد من الأسهم والدورات،
ويحسب متوسط طول الدورة ومتوسط موقع القمة، ثم يتوقع الدورة القادمة.

⚠️ ملاحظة مهمة:
هذا أداة تحليل إحصائي/بصري لأنماط تاريخية فقط، وليست توصية
استثمارية. الأسواق المالية لا تلتزم بدورات ثابتة 100%، والنتائج
احتمالية وليست مؤكدة. استخدمها كأداة بحث إضافية فقط.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import Optional, List
import calendar
import statistics


# -----------------------------------------------------------
# دوال مساعدة للتعامل مع التواريخ على مستوى الشهر
# -----------------------------------------------------------
def add_months(d: date, months: int) -> date:
    """يرجع تاريخ جديد بعد إضافة عدد من الأشهر لتاريخ d (باليوم 1)."""
    total_month_index = d.month - 1 + months
    year = d.year + total_month_index // 12
    month = total_month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def diff_months(d1: date, d2: date) -> int:
    """عدد الأشهر الكاملة بين تاريخين (d2 - d1)."""
    return (d2.year - d1.year) * 12 + (d2.month - d1.month)


def month_str(d: date) -> str:
    return d.strftime("%Y-%m")


# -----------------------------------------------------------
# تمثيل دورة واحدة
# -----------------------------------------------------------
@dataclass
class Cycle:
    start: date
    end: date
    peak: Optional[date] = None

    @property
    def length_months(self) -> int:
        # عد شامل: من شهر البداية إلى شهر النهاية (شاملة الطرفين)
        return diff_months(self.start, self.end) + 1

    @property
    def peak_month_number(self) -> Optional[int]:
        if self.peak is None:
            return None
        return diff_months(self.start, self.peak) + 1

    @property
    def peak_ratio(self) -> Optional[float]:
        if self.peak is None:
            return None
        return self.peak_month_number / self.length_months


# -----------------------------------------------------------
# نموذج تحليل الدورات لسهم واحد
# -----------------------------------------------------------
@dataclass
class TickerCycles:
    ticker: str
    cycles: List[Cycle] = field(default_factory=list)

    def add_cycle(self, start: str, end: str, peak: Optional[str] = None,
                  fmt: str = "%Y-%m"):
        """أضف دورة جديدة. صيغة التاريخ الافتراضية: YYYY-MM (مثال: 2020-03)"""
        s = _parse(start, fmt)
        e = _parse(end, fmt)
        p = _parse(peak, fmt) if peak else None
        self.cycles.append(Cycle(s, e, p))

    # ---------- إحصائيات ----------
    def avg_length(self) -> float:
        return statistics.mean(c.length_months for c in self.cycles)

    def avg_peak_ratio(self) -> Optional[float]:
        ratios = [c.peak_ratio for c in self.cycles if c.peak_ratio is not None]
        return statistics.mean(ratios) if ratios else None

    def consistency(self) -> Optional[float]:
        """انحراف معياري لموقع القمة (كلما قل = الدورة أكثر ثباتًا)."""
        ratios = [c.peak_ratio for c in self.cycles if c.peak_ratio is not None]
        if len(ratios) < 2:
            return None
        return statistics.pstdev(ratios)

    # ---------- التوقع ----------
    def predict_next_cycles(self, n: int = 1) -> List[Cycle]:
        """يتوقع n دورة قادمة اعتمادًا على متوسط الطول وموقع القمة."""
        if not self.cycles:
            return []
        avg_len = round(self.avg_length())
        avg_ratio = self.avg_peak_ratio()

        predictions = []
        last_end = self.cycles[-1].end
        for _ in range(n):
            next_start = add_months(last_end, 1)
            next_end = add_months(next_start, avg_len - 1)
            next_peak = None
            if avg_ratio is not None:
                peak_offset = round(avg_ratio * avg_len) - 1
                next_peak = add_months(next_start, peak_offset)
            predictions.append(Cycle(next_start, next_end, next_peak))
            last_end = next_end
        return predictions

    # ---------- تقرير نصي ----------
    def report(self, predict: int = 1):
        print(f"\n{'='*55}")
        print(f"السهم: {self.ticker}")
        print(f"{'='*55}")

        for i, c in enumerate(self.cycles, 1):
            peak_txt = (f"  | القمة: {month_str(c.peak)} (الشهر رقم {c.peak_month_number})"
                        if c.peak else "")
            print(f"الدورة {i}: {month_str(c.start)} → {month_str(c.end)} "
                  f"(الطول: {c.length_months} شهر){peak_txt}")

        avg_len = self.avg_length()
        avg_ratio = self.avg_peak_ratio()
        cons = self.consistency()

        print(f"\n-- متوسط طول الدورة: {avg_len:.1f} شهر")
        if avg_ratio is not None:
            print(f"-- متوسط موقع القمة: الشهر رقم {avg_ratio * avg_len:.1f} "
                  f"من الدورة (نسبة {avg_ratio*100:.1f}%)")
        if cons is not None:
            print(f"-- درجة ثبات القمة (انحراف معياري للنسبة): {cons:.3f} "
                  f"{'(ثبات جيد)' if cons < 0.05 else '(تفاوت ملحوظ)'}")

        preds = self.predict_next_cycles(predict)
        for i, p in enumerate(preds, 1):
            peak_txt = f" | القمة المتوقعة: {month_str(p.peak)}" if p.peak else ""
            print(f"\n>>> توقع الدورة القادمة #{i}: "
                  f"{month_str(p.start)} → {month_str(p.end)}{peak_txt}")


def _parse(s: str, fmt: str) -> date:
    from datetime import datetime
    return datetime.strptime(s, fmt).date()


# -----------------------------------------------------------
# مثال تطبيقي: تسلا (بيانات مؤكدة من رسالتك)
# -----------------------------------------------------------
if __name__ == "__main__":
    tsla = TickerCycles("TSLA")
    tsla.add_cycle(start="2020-03", end="2024-03", peak="2021-10")  # الشهر رقم 20
    tsla.report(predict=2)

    # -----------------------------------------------------------
    # قالب فارغ لباقي الأسهم — عدّل التواريخ حسب بياناتك الفعلية
    # صيغة التاريخ: "YYYY-MM"  (مثال: "2023-01")
    # -----------------------------------------------------------

    amd = TickerCycles("AMD")
    # مثال بالشكل فقط — استبدل بالتواريخ الحقيقية من دفترك
    # amd.add_cycle(start="2023-01", end="2025-02")   # الدورة السابقة
    # amd.add_cycle(start="2025-04", end="2027-06")   # الدورة الحالية
    # amd.report(predict=1)

    meta = TickerCycles("META")
    # meta.add_cycle(start="2021-12", end="2023-01")
    # meta.add_cycle(start="2022-11", end="2024-09")
    # meta.report(predict=1)

    fourth = TickerCycles("STOCK4")
    # fourth.add_cycle(start="2021-12", end="2024-02")
    # fourth.add_cycle(start="2022-05", end="2024-07")
    # fourth.report(predict=1)

    print("\n\nعدّل بيانات AMD وMETA والسهم الرابع في الكود ثم شغّله من جديد "
          "لعرض توقعاتها.")
