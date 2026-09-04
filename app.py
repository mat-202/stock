"""
app.py
======
لوحة التحكم الرئيسية (Streamlit). شغّلها محليًا بـ:
    streamlit run app.py
أو ارفعها على Streamlit Community Cloud (مجاني) وتربطها بمستودع GitHub.
"""

from datetime import date
import streamlit as st

from config import MARKETS
from analytics import cycle_snapshot, matching_report, build_leaderboard
from cycle_engine import month_str

st.set_page_config(page_title="لوحة تحليل الدورات الزمنية", page_icon="🔄", layout="wide")
st.markdown('<div dir="rtl">', unsafe_allow_html=True)

TODAY = date.today()

# -----------------------------------------------------------
# اختيار السوق
# -----------------------------------------------------------
st.title("🔄 لوحة تحليل الدورات الزمنية")

market_key = st.radio(
    "اختر السوق للتحليل:",
    options=list(MARKETS.keys()),
    format_func=lambda k: MARKETS[k]["label"],
    horizontal=True,
)
stocks = MARKETS[market_key]["stocks"]
stocks_with_data = {k: v for k, v in stocks.items() if v.cycles}

if not stocks_with_data:
    st.warning("لا توجد أسهم فيها بيانات دورات مسجّلة لهذا السوق بعد. "
               "أضفها من ملف config.py")
    st.stop()

# -----------------------------------------------------------
# 👑 عرش النجوم والأداء
# -----------------------------------------------------------
st.header("👑 عرش النجوم والأداء الدوري")

with st.spinner("جاري حساب أداء الأسهم..."):
    leaderboard = build_leaderboard(stocks_with_data)

if not leaderboard:
    st.info("تعذّر جلب بيانات الأداء حاليًا (تحقق من الاتصال أو رموز الأسهم).")
else:
    best, worst = leaderboard[0], leaderboard[-1]
    col1, col2 = st.columns(2)

    with col1:
        st.success(
            f"🌟 **نجم السوق (الأعلى أداءً)**\n\n"
            f"### {best['name']} ({best['ticker']})\n"
            f"- الأداء الشهري: **{best['monthly_pct']:+.1f}%**\n"
            f"- الأداء الأسبوعي: **{best['weekly_pct']:+.1f}%**"
            if best['weekly_pct'] is not None else
            f"🌟 **نجم السوق**\n\n### {best['name']} ({best['ticker']})\n"
            f"- الأداء الشهري: **{best['monthly_pct']:+.1f}%**"
        )

    with col2:
        st.error(
            f"⚠️ **الأقل أداءً في السوق**\n\n"
            f"### {worst['name']} ({worst['ticker']})\n"
            f"- الأداء الشهري: **{worst['monthly_pct']:+.1f}%**\n"
            f"- الأداء الأسبوعي: **{worst['weekly_pct']:+.1f}%**"
            if worst['weekly_pct'] is not None else
            f"⚠️ **الأقل أداءً**\n\n### {worst['name']} ({worst['ticker']})\n"
            f"- الأداء الشهري: **{worst['monthly_pct']:+.1f}%**"
        )

    with st.expander("عرض ترتيب كل الأسهم"):
        st.table([
            {"السهم": r["name"], "الرمز": r["ticker"],
             "أسبوعي %": r["weekly_pct"], "شهري %": r["monthly_pct"]}
            for r in leaderboard
        ])

st.divider()

# -----------------------------------------------------------
# تفاصيل سهم محدد: السعر، المستهدف، الدورة، ومطابقة التواريخ
# -----------------------------------------------------------
st.header("📊 تفاصيل الدورة لسهم محدد")

selected_key = st.selectbox(
    "اختر السهم:",
    options=list(stocks_with_data.keys()),
    format_func=lambda k: f"{stocks_with_data[k].name} ({stocks_with_data[k].ticker})",
)
tc = stocks_with_data[selected_key]

with st.spinner("جاري حساب بيانات الدورة..."):
    snap = cycle_snapshot(tc, TODAY)

c1, c2, c3, c4 = st.columns(4)
c1.metric("السعر الحالي", f"{snap.current_price:.2f}" if snap.current_price else "—")
c2.metric("المستهدف النسبي", f"{snap.target_price:.2f}" if snap.target_price else "—")
c3.metric("بداية الدورة", month_str(snap.cycle_start))
c4.metric("نهاية الدورة", month_str(snap.cycle_end))

if snap.expected_peak:
    st.info(f"📈 شهر القمة المتوقع لهذه الدورة: **{month_str(snap.expected_peak)}**")

avg_len = tc.avg_length()
cons = tc.consistency()
st.caption(
    f"متوسط طول الدورة: {avg_len:.1f} شهر"
    + (f" | ثبات موقع القمة (انحراف معياري): {cons:.3f}" if cons is not None else "")
)

st.subheader("📅 مطابقة التواريخ وسلوك الشموع في الدورة السابقة")

with st.spinner("جاري مطابقة التواريخ..."):
    report = matching_report(tc, TODAY)

if report is None:
    st.info("لا توجد دورة سابقة كافية للمطابقة (تحتاج دورتين مسجّلتين على الأقل).")
else:
    labels = {
        "this_week": "الأسبوع الحالي",
        "next_week": "الأسبوع القادم",
        "this_month": "الشهر الحالي",
        "next_month": "الشهر القادم",
    }
    for key, label in labels.items():
        candle = report.get(key)
        if candle:
            st.write(
                f"**{label}** ↔ يطابق تاريخ **{candle['date'].strftime('%Y-%m-%d')}** "
                f"من الدورة السابقة → {candle['label']}"
            )
        else:
            st.write(f"**{label}**: تعذّر جلب بيانات الشمعة المطابقة.")

st.divider()
st.caption(
    "⚠️ هذه أداة تحليل إحصائي لأنماط تاريخية فقط وليست توصية استثمارية. "
    "الأسواق لا تلتزم بدورات ثابتة 100%، والنتائج احتمالية."
)
st.markdown('</div>', unsafe_allow_html=True)
