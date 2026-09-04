"""
config.py
=========
هنا تضيف الأسهم وبيانات دوراتها. هذا هو المكان الوحيد اللي تحتاج تعدّله
لإضافة سهم جديد أو تحديث تواريخ دورة.

لكل سهم:
    tc = TickerCycles(ticker="الرمز", name="الاسم بالعربي", market="nasdaq" أو "tasi")
    tc.add_cycle(start="YYYY-MM", end="YYYY-MM", peak="YYYY-MM")   # للدورات المكتملة
    # كرر add_cycle لكل دورة تاريخية معروفة (كل ما زادت الدورات، زادت دقة التوقع)
"""

from cycle_engine import TickerCycles

# -----------------------------------------------------------
# سوق ناسداك / أوبشن
# -----------------------------------------------------------
NASDAQ_STOCKS: dict[str, TickerCycles] = {}

tsla = TickerCycles(ticker="TSLA", name="تسلا", market="nasdaq")
tsla.add_cycle(start="2020-03", end="2024-03", peak="2021-10")
NASDAQ_STOCKS["TSLA"] = tsla

amd = TickerCycles(ticker="AMD", name="إيه إم دي", market="nasdaq")
# عدّل بالتواريخ الحقيقية من دفترك، مثال:
# amd.add_cycle(start="2023-01", end="2025-02")
# amd.add_cycle(start="2025-04", end="2027-06")
NASDAQ_STOCKS["AMD"] = amd

meta = TickerCycles(ticker="META", name="ميتا", market="nasdaq")
# meta.add_cycle(start="2021-12", end="2023-01")
# meta.add_cycle(start="2022-11", end="2024-09")
NASDAQ_STOCKS["META"] = meta

# أضف السهم الرابع من دفترك هنا بنفس الطريقة
# stock4 = TickerCycles(ticker="XXXX", name="الاسم", market="nasdaq")
# stock4.add_cycle(start="2021-12", end="2024-02")
# NASDAQ_STOCKS["XXXX"] = stock4


# -----------------------------------------------------------
# السوق السعودي (تاسي) — الرمز يُكتب بدون .SR، الكود يضيفه تلقائيًا
# -----------------------------------------------------------
TASI_STOCKS: dict[str, TickerCycles] = {}

aramco = TickerCycles(ticker="2222", name="أرامكو السعودية", market="tasi")
# aramco.add_cycle(start="2020-06", end="2022-08")
# aramco.add_cycle(start="2022-09", end="2024-11")
TASI_STOCKS["2222"] = aramco

# أضف بقية أسهم تاسي بنفس الطريقة
# rajhi = TickerCycles(ticker="1120", name="مصرف الراجحي", market="tasi")
# TASI_STOCKS["1120"] = rajhi


MARKETS = {
    "nasdaq": {"label": "أمريكي (ناسداك / أوبشن)", "stocks": NASDAQ_STOCKS},
    "tasi": {"label": "سعودي (تاسي)", "stocks": TASI_STOCKS},
}
