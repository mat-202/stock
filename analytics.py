"""
analytics.py
============
- المستهدف النسبي: يسقط نفس نسبة الحركة السعرية التي حصلت في الدورة السابقة
  (من بداية الدورة حتى النقطة المقابلة لليوم الحالي) على بداية الدورة الحالية.
- لوحة المتصدرين: يرتب أسهم السوق المختار حسب الأداء الشهري ليحدد
  "نجم السوق" و"الأقل أداءً".
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Optional, List, Dict

from cycle_engine import TickerCycles
from data_provider import (
    normalize_ticker, fetch_last_price, price_change_pct,
    price_near_date, candle_at_date,
)


@dataclass
class CycleSnapshot:
    ticker: str
    name: str
    current_price: Optional[float]
    target_price: Optional[float]
    cycle_start: date
    cycle_end: date
    expected_peak: Optional[date]


def relative_target_price(tc: TickerCycles, today: date = None) -> Optional[float]:
    """
    المستهدف النسبي = سعر بداية الدورة الحالية × (نسبة حركة الدورة المرجعية
    من بدايتها حتى التاريخ المطابق لليوم الحالي).
    """
    today = today or date.today()
    ticker = normalize_ticker(tc.ticker, tc.market)
    current = tc.current_cycle(today)
    ref = tc.reference_cycle(current)
    if ref is None:
        return None

    ratio = current.elapsed_ratio(min(today, current.end))
    matched_date = ref.date_at_ratio(ratio)

    ref_start_price = price_near_date(ticker, ref.start)
    ref_matched_price = price_near_date(ticker, matched_date)
    current_start_price = price_near_date(ticker, current.start)

    if not all([ref_start_price, ref_matched_price, current_start_price]):
        return None
    growth_ratio = ref_matched_price / ref_start_price
    return round(current_start_price * growth_ratio, 2)


def cycle_snapshot(tc: TickerCycles, today: date = None) -> CycleSnapshot:
    today = today or date.today()
    ticker = normalize_ticker(tc.ticker, tc.market)
    current = tc.current_cycle(today)
    return CycleSnapshot(
        ticker=tc.ticker,
        name=tc.name or tc.ticker,
        current_price=fetch_last_price(ticker),
        target_price=relative_target_price(tc, today),
        cycle_start=current.start,
        cycle_end=current.end,
        expected_peak=current.peak,
    )


def matching_report(tc: TickerCycles, today: date = None) -> Optional[dict]:
    """تقرير مطابقة التاريخ الحالي (وأسبوع/شهر قادم) بالدورة السابقة + سلوك الشمعة."""
    today = today or date.today()
    ticker = normalize_ticker(tc.ticker, tc.market)
    result = tc.matching_date(today)
    if result is None:
        return None
    current, ref, matched_today = result

    from datetime import timedelta
    next_week_today = today + timedelta(days=7)
    ratio_next_week = current.elapsed_ratio(min(next_week_today, current.end))
    matched_next_week = ref.date_at_ratio(ratio_next_week)

    from cycle_engine import add_months
    next_month_date = add_months(today, 1)
    ratio_next_month = current.elapsed_ratio(min(next_month_date, current.end))
    matched_next_month = ref.date_at_ratio(ratio_next_month)

    return {
        "this_week": candle_at_date(ticker, matched_today),
        "next_week": candle_at_date(ticker, matched_next_week),
        "this_month": candle_at_date(ticker, ref.date_at_ratio(current.elapsed_ratio(today))),
        "next_month": candle_at_date(ticker, matched_next_month),
        "matched_today_date": matched_today,
    }


def build_leaderboard(tickers: Dict[str, TickerCycles]) -> List[dict]:
    """يرجع قائمة بأداء كل الأسهم (أسبوعي/شهري) مرتبة تنازليًا حسب الأداء الشهري."""
    rows = []
    for key, tc in tickers.items():
        ticker = normalize_ticker(tc.ticker, tc.market)
        weekly = price_change_pct(ticker, 7)
        monthly = price_change_pct(ticker, 30)
        rows.append({
            "ticker": tc.ticker,
            "name": tc.name or tc.ticker,
            "weekly_pct": weekly,
            "monthly_pct": monthly,
        })
    rows = [r for r in rows if r["monthly_pct"] is not None]
    rows.sort(key=lambda r: r["monthly_pct"], reverse=True)
    return rows
