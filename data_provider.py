"""
data_provider.py
=================
كل ما يخص جلب بيانات الأسعار الحية والتاريخية (ناسداك عبر yfinance مباشرة،
والسوق السعودي عبر yfinance أيضًا برمز مثل 2222.SR).

إذا كنت تستخدم مصدر بيانات آخر في موقعك الحالي (API مدفوع مثلاً)، عدّل فقط
الدوال هنا (fetch_history / fetch_last_price) وباقي الكود لن يتأثر.
"""

from __future__ import annotations
from datetime import date, timedelta
from typing import Optional
import pandas as pd
import streamlit as st
import yfinance as yf


def normalize_ticker(ticker: str, market: str) -> str:
    """يضيف لاحقة .SR تلقائيًا لأسهم تاسي إن لم تكن موجودة."""
    ticker = ticker.strip().upper()
    if market == "tasi" and not ticker.endswith(".SR"):
        return f"{ticker}.SR"
    return ticker


@st.cache_data(ttl=300, show_spinner=False)
def fetch_history(ticker: str, start: date, end: date) -> pd.DataFrame:
    """
    يرجع DataFrame فيه Open/High/Low/Close/Volume بين تاريخين.
    مخبّأ (cached) لمدة 5 دقائق لتقليل عدد الطلبات.
    """
    df = yf.download(ticker, start=start, end=end + timedelta(days=1),
                      progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


@st.cache_data(ttl=300, show_spinner=False)
def fetch_last_price(ticker: str) -> Optional[float]:
    """آخر سعر إغلاق متاح."""
    df = fetch_history(ticker, date.today() - timedelta(days=10), date.today())
    if df.empty:
        return None
    return float(df["Close"].iloc[-1])


def price_change_pct(ticker: str, days_back: int) -> Optional[float]:
    """نسبة التغير خلال آخر N يوم تقويمي (تقريبًا أسبوعي/شهري)."""
    end = date.today()
    start = end - timedelta(days=days_back + 10)  # هامش لتفادي العطلات
    df = fetch_history(ticker, start, end)
    if df.empty or len(df) < 2:
        return None
    closes = df["Close"]
    target_date = end - timedelta(days=days_back)
    past_series = closes[closes.index.date <= target_date]
    if past_series.empty:
        past = closes.iloc[0]
    else:
        past = past_series.iloc[-1]
    current = closes.iloc[-1]
    if past == 0:
        return None
    return float((current - past) / past * 100)


def price_near_date(ticker: str, target: date, window_days: int = 6) -> Optional[float]:
    """
    يرجع أقرب سعر إغلاق متاح لتاريخ معيّن (يُستخدم في حساب المستهدف النسبي
    ومطابقة التواريخ بين الدورات).
    """
    df = fetch_history(ticker, target - timedelta(days=window_days),
                        target + timedelta(days=window_days))
    if df.empty:
        return None
    df = df.copy()
    df["diff"] = abs((df.index.date - target))
    closest_idx = df["diff"].apply(lambda td: abs(td.days)).idxmin()
    return float(df.loc[closest_idx, "Close"])


def classify_candle(open_: float, high: float, low: float, close: float) -> str:
    """
    تصنيف مبسّط (استدلالي) لسلوك الشمعة اعتمادًا على شكلها فقط —
    ليس تحليلًا فنيًا معتمدًا، فقط وصف تقريبي لشكل الحركة.
    """
    rng = high - low
    if rng <= 0:
        return "بيانات غير كافية"
    body = close - open_
    body_pct = body / rng

    near_high = (high - close) / rng < 0.15
    near_low = (close - low) / rng < 0.15

    if body_pct > 0.6:
        return "🟢 ضغط شراء قوي"
    if body_pct < -0.6:
        return "🔴 ضغط بيع قوي"
    if abs(body_pct) < 0.15:
        return "🟡 شمعة حيرة وتوازن مؤقت"
    if near_high and body_pct > 0:
        return "🟡 اختبار مقاومة"
    if near_low and body_pct < 0:
        return "🟡 اختبار دعم"
    if body_pct > 0:
        return "🟢 موجة ارتداد صاعدة"
    return "🔴 موجة هابطة"


def candle_at_date(ticker: str, target: date, window_days: int = 6) -> Optional[dict]:
    """يرجع OHLC + التصنيف الاستدلالي لأقرب شمعة لتاريخ معيّن."""
    df = fetch_history(ticker, target - timedelta(days=window_days),
                        target + timedelta(days=window_days))
    if df.empty:
        return None
    df = df.copy()
    df["diff"] = df.index.map(lambda d: abs((d.date() - target).days))
    row = df.loc[df["diff"].idxmin()]
    label = classify_candle(row["Open"], row["High"], row["Low"], row["Close"])
    return {
        "date": row.name.date(),
        "open": float(row["Open"]),
        "high": float(row["High"]),
        "low": float(row["Low"]),
        "close": float(row["Close"]),
        "label": label,
    }
