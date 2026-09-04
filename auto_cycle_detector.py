"""
auto_cycle_detector.py
=======================
اكتشاف تلقائي للدورات الزمنية التاريخية لأي سهم، بدل إدخالها يدويًا.

الفكرة: نجيب الإغلاقات الشهرية على مدى سنوات، نحدد "القيعان الكبرى"
(نقاط الانخفاض الكبيرة)، ونعتبر المسافة بين كل قاعين متتاليين دورة واحدة،
والقمة = أعلى سعر داخل تلك الدورة.

⚠️ هذا اكتشاف إحصائي تقريبي (heuristic) وليس تحليل موجات معتمد أو توصية.
راجع الدورات المكتشفة بصريًا (بالشارت) قبل الاعتماد عليها، وجرّب تعديل
prominence_pct إذا طلعت الدورات كثيرة/قليلة عن المتوقع.
"""

from __future__ import annotations
from datetime import date, timedelta
from typing import List
import numpy as np
from scipy.signal import find_peaks

from cycle_engine import Cycle, TickerCycles
from data_provider import normalize_ticker, fetch_history


def _monthly_closes(ticker: str, years_back: int = 20):
    end = date.today()
    start = end - timedelta(days=365 * years_back)
    df = fetch_history(ticker, start, end)
    if df.empty:
        return None
    monthly = df["Close"].resample("MS").last().dropna()
    return monthly


def detect_cycles(ticker: str, market: str = "nasdaq",
                   min_cycle_months: int = 12,
                   prominence_pct: float = 0.25,
                   years_back: int = 20) -> List[Cycle]:
    """
    min_cycle_months: أقل مسافة مقبولة بين قاعين حتى تُحسب دورتين منفصلتين
                       (يمنع اعتبار كل تذبذب صغير دورة مستقلة).
    prominence_pct: مدى وضوح القاع (كنسبة من كامل مدى السعر بالـ log) —
                     كل ما زاد الرقم، احتاج القاع يكون أعمق حتى يُحتسب.
    """
    norm = normalize_ticker(ticker, market)
    closes = _monthly_closes(norm, years_back)
    if closes is None or len(closes) < min_cycle_months * 2:
        return []

    log_prices = np.log(closes.values)
    price_range = log_prices.max() - log_prices.min()
    if price_range <= 0:
        return []
    prominence = prominence_pct * price_range

    trough_idx, _ = find_peaks(-log_prices, distance=min_cycle_months,
                                prominence=prominence)
    if len(trough_idx) < 2:
        return []

    dates = closes.index
    cycles = []
    for i in range(len(trough_idx) - 1):
        start_i, end_i = trough_idx[i], trough_idx[i + 1]
        segment = closes.iloc[start_i:end_i + 1]
        peak_i_local = int(np.argmax(segment.values))
        peak_date = segment.index[peak_i_local].date()
        cycles.append(Cycle(dates[start_i].date(), dates[end_i].date(), peak_date))
    return cycles


def auto_populate(tc: TickerCycles, min_cycle_months: int = 12,
                   prominence_pct: float = 0.25, years_back: int = 20) -> TickerCycles:
    """يملأ tc.cycles بالدورات المكتشفة تلقائيًا (يستبدل أي دورات موجودة)."""
    tc.cycles = detect_cycles(tc.ticker, tc.market, min_cycle_months,
                               prominence_pct, years_back)
    return tc
