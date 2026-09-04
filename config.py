"""
config.py
=========
هنا تضيف الأسهم. لكل سهم خيارين:

1) تدخل دوراته يدويًا (من ملاحظاتك) عبر add_cycle — هذا الأدق دائمًا:
    tc.add_cycle(start="YYYY-MM", end="YYYY-MM", peak="YYYY-MM")

2) أو تتركه بدون add_cycle → التطبيق يكتشف دوراته تلقائيًا من السعر
   التاريخي الحقيقي (عبر auto_cycle_detector.py). الاكتشاف التلقائي
   اجتهاد إحصائي (heuristic) — راجعه بصريًا قبل الاعتماد عليه.
"""

from cycle_engine import TickerCycles

# -----------------------------------------------------------
# سوق ناسداك / أوبشن
# -----------------------------------------------------------
NASDAQ_STOCKS: dict[str, TickerCycles] = {}

# --- من دفترك (بيانات دورات مؤكدة يدويًا) ---
tsla = TickerCycles(ticker="TSLA", name="تسلا", market="nasdaq")
tsla.add_cycle(start="2020-03", end="2024-03", peak="2021-10")
NASDAQ_STOCKS["TSLA"] = tsla

# ⚠️ AMD مصنّفة "مشكوك فيها" (Doubtful) وليست "حلال" حسب فحص Musaffa
# (أبريل 2026) — تأكد بنفسك عبر Musaffa/Zoya/Islamicly قبل التداول عليها.
amd = TickerCycles(ticker="AMD", name="إيه إم دي", market="nasdaq")
# amd.add_cycle(start="2023-01", end="2025-02")
# amd.add_cycle(start="2025-04", end="2027-06")
NASDAQ_STOCKS["AMD"] = amd

# ⚠️ META مصنّفة "مشكوك فيها" (Doubtful) أيضًا حسب نفس الفحص — تأكد بنفسك.
meta = TickerCycles(ticker="META", name="ميتا", market="nasdaq")
# meta.add_cycle(start="2021-12", end="2023-01")
# meta.add_cycle(start="2022-11", end="2024-09")
NASDAQ_STOCKS["META"] = meta

# --- أكبر 20 شركة مصنّفة "حلال" حسب فحص Musaffa (أبريل 2026) ---
# مرتّبة تقريبًا حسب القيمة السوقية. بدون add_cycle → تُكتشف الدورات تلقائيًا.
_HALAL_SCREENED = [
    ("AAPL", "آبل"),
    ("NVDA", "إنفيديا"),
    ("AVGO", "برودكوم"),
    ("ASML", "إيه إس إم إل"),
    ("QCOM", "كوالكوم"),
    ("AMAT", "أبلايد ماتيريلز"),
    ("CSCO", "سيسكو"),
    ("TXN", "تكساس إنسترومنتس"),
    ("ISRG", "إنتيوتيف سيرجيكال"),
    ("MU", "ميكرون"),
    ("LRCX", "لام ريسيرش"),
    ("ADI", "أنالوج ديفايسز"),
    ("REGN", "ريجينيرون"),
    ("KLAC", "كي إل إيه"),
    ("PANW", "بالو ألتو نتوركس"),
    ("SBUX", "ستاربكس"),
    ("SNPS", "سينوبسيس"),
    ("CRWD", "كراودسترايك"),
    ("GILD", "غيلياد ساينسز"),
]
for _ticker, _name in _HALAL_SCREENED:
    NASDAQ_STOCKS[_ticker] = TickerCycles(ticker=_ticker, name=_name, market="nasdaq")

# أضف السهم الرابع من دفترك هنا (إذا حاب تدخله يدويًا):
# stock4 = TickerCycles(ticker="XXXX", name="الاسم", market="nasdaq")
# stock4.add_cycle(start="2021-12", end="2024-02")
# NASDAQ_STOCKS["XXXX"] = stock4


# -----------------------------------------------------------
# السوق السعودي (تاسي) — الرمز يُكتب بدون .SR، الكود يضيفه تلقائيًا
# -----------------------------------------------------------
TASI_STOCKS: dict[str, TickerCycles] = {}

aramco = TickerCycles(ticker="2222", name="أرامكو السعودية", market="tasi")
# aramco.add_cycle(start="2020-06", end="2022-08")
TASI_STOCKS["2222"] = aramco

# أضف بقية أسهم تاسي بنفس الطريقة (بدون add_cycle = اكتشاف تلقائي)
# rajhi = TickerCycles(ticker="1120", name="مصرف الراجحي", market="tasi")
# TASI_STOCKS["1120"] = rajhi


MARKETS = {
    "nasdaq": {"label": "أمريكي (ناسداك / أوبشن)", "stocks": NASDAQ_STOCKS},
    "tasi": {"label": "سعودي (تاسي)", "stocks": TASI_STOCKS},
}
