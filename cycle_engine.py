"""
cycle_engine.py
================
المحرك الأساسي لحساب الدورات الزمنية: طول الدورة، موقع القمة، التوقعات،
وربط أي تاريخ بتاريخه "المطابق" في دورة أخرى (لمطابقة سلوك الشموع).

هذا الملف لا يتصل بالإنترنت ولا يعرف شيء عن الأسعار — فقط رياضيات التواريخ.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List
import calendar
import statistics


# -----------------------------------------------------------
# أدوات مساعدة للتواريخ
# -----------------------------------------------------------
def add_months(d: date, months: int) -> date:
    total = d.month - 1 + months
    year = d.year + total // 12
    month = total % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def diff_months(d1: date, d2: date) -> int:
    return (d2.year - d1.year) * 12 + (d2.month - d1.month)


def month_str(d: date) -> str:
    return d.strftime("%Y-%m")


def parse_ym(s: str) -> date:
    """يحوّل '2024-04' إلى تاريخ أول يوم بذلك الشهر."""
    return datetime.strptime(s, "%Y-%m").date()


# -----------------------------------------------------------
# دورة واحدة
# -----------------------------------------------------------
@dataclass
class Cycle:
    start: date
    end: date
    peak: Optional[date] = None

    @property
    def length_months(self) -> int:
        return diff_months(self.start, self.end) + 1

    @property
    def length_days(self) -> int:
        return (self.end - self.start).days + 1

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

    def contains(self, d: date) -> bool:
        return self.start <= d <= self.end

    def elapsed_ratio(self, d: date) -> float:
        """نسبة ما مضى من الدورة عند تاريخ d (0 = البداية، 1 = النهاية)."""
        total = (self.end - self.start).days
        if total <= 0:
            return 0.0
        passed = (d - self.start).days
        return max(0.0, min(1.0, passed / total))

    def date_at_ratio(self, ratio: float) -> date:
        """يرجع التاريخ المقابل لنسبة زمنية معيّنة داخل هذه الدورة."""
        total_days = (self.end - self.start).days
        offset = round(total_days * ratio)
        return self.start + __import__("datetime").timedelta(days=offset)


# -----------------------------------------------------------
# مجموعة دورات لسهم واحد
# -----------------------------------------------------------
@dataclass
class TickerCycles:
    ticker: str
    name: str = ""
    market: str = "nasdaq"  # "nasdaq" أو "tasi"
    cycles: List[Cycle] = field(default_factory=list)

    def add_cycle(self, start: str, end: str, peak: Optional[str] = None):
        s, e = parse_ym(start), parse_ym(end)
        p = parse_ym(peak) if peak else None
        self.cycles.append(Cycle(s, e, p))
        self.cycles.sort(key=lambda c: c.start)

    # ---------- إحصائيات ----------
    def avg_length(self) -> float:
        return statistics.mean(c.length_months for c in self.cycles)

    def avg_peak_ratio(self) -> Optional[float]:
        r = [c.peak_ratio for c in self.cycles if c.peak_ratio is not None]
        return statistics.mean(r) if r else None

    def consistency(self) -> Optional[float]:
        r = [c.peak_ratio for c in self.cycles if c.peak_ratio is not None]
        return statistics.pstdev(r) if len(r) >= 2 else None

    # ---------- التوقع ----------
    def predict_next_cycles(self, n: int = 1) -> List[Cycle]:
        if not self.cycles:
            return []
        avg_len = round(self.avg_length())
        avg_ratio = self.avg_peak_ratio()
        preds = []
        last_end = self.cycles[-1].end
        for _ in range(n):
            next_start = add_months(last_end, 1)
            next_end = add_months(next_start, avg_len - 1)
            next_peak = None
            if avg_ratio is not None:
                offset = round(avg_ratio * avg_len) - 1
                next_peak = add_months(next_start, offset)
            preds.append(Cycle(next_start, next_end, next_peak))
            last_end = next_end
        return preds

    def current_cycle(self, today: date) -> Cycle:
        """
        يرجع الدورة الفعلية إذا كان اليوم يقع داخل واحدة من الدورات المسجّلة،
        وإلا يرجع أقرب دورة متوقعة (مستقبلية أو حتى لو ما زالت التواريخ لم تُسجَّل بعد).
        """
        for c in self.cycles:
            if c.contains(today):
                return c
        # اليوم بعد آخر دورة مسجّلة → أحسب الدورات المتوقعة حتى نغطي اليوم
        preds = self.predict_next_cycles(1)
        while preds and preds[-1].end < today:
            preds = self.predict_next_cycles(len(preds) + 1)
        for c in preds:
            if c.contains(today) or c.end >= today:
                return c
        return preds[-1] if preds else self.cycles[-1]

    def reference_cycle(self, current: Cycle) -> Optional[Cycle]:
        """الدورة السابقة لدورة معيّنة (تُستخدم كمرجع للمطابقة والتوقع)."""
        earlier = [c for c in self.cycles if c.end < current.start]
        if earlier:
            return earlier[-1]
        # قد تكون current نفسها من ضمن cycles ولها سابقة أيضًا
        idx = self.cycles.index(current) if current in self.cycles else None
        if idx is not None and idx > 0:
            return self.cycles[idx - 1]
        return None

    def matching_date(self, today: date) -> Optional[tuple[Cycle, Cycle, date]]:
        """
        يطابق تاريخ اليوم بتاريخه المقابل في الدورة السابقة (نفس النسبة الزمنية).
        يرجع: (الدورة الحالية, الدورة المرجعية, التاريخ المطابق) أو None.
        """
        current = self.current_cycle(today)
        ref = self.reference_cycle(current)
        if ref is None:
            return None
        ratio = current.elapsed_ratio(today)
        matched = ref.date_at_ratio(ratio)
        return current, ref, matched
