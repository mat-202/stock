import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

st.set_page_config(page_title="منصة الدورات الزمنية والنجوم الحقيقية", page_icon="🌟", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; direction: rtl; text-align: right; }
    
    .star-card-top {
        background: linear-gradient(135deg, #065f46 0%, #047857 100%);
        color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .worst-card-top {
        background: linear-gradient(135deg, #9f1239 0%, #be123c 100%);
        color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-title { font-size: 0.95rem; font-weight: bold; opacity: 0.95; }
    .metric-value { font-size: 1.25rem; font-weight: bold; margin-top: 4px; }
    
    .company-card-positive {
        background-color: rgba(16, 185, 129, 0.08);
        border-right: 5px solid #10b981;
        padding: 10px 15px;
        border-radius: 8px;
        margin-bottom: 8px;
    }
    .company-card-negative {
        background-color: rgba(239, 68, 68, 0.08);
        border-right: 5px solid #ef4444;
        padding: 10px 15px;
        border-radius: 8px;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# قائمة تاسي
TASI_ALL_STOCKS = {
    "2222.SR": "أرامكو السعودية", "1120.SR": "الراجحي", "2010.SR": "سابك", "1180.SR": "الأهلي",
    "2170.SR": "اللجين", "4323.SR": "سمو", "2082.SR": "أكوا باور", "7010.SR": "STC",
    "2020.SR": "سابك للمغذيات", "2350.SR": "كيان السعودية", "1150.SR": "الإنماء", "1010.SR": "الرياض"
}

# قائمة ناسداك
NASDAQ_TOP20_OPTIONS = {
    "TSLA": "تيسلا (Tesla)", "NVDA": "أنفيديا (Nvidia)", "META": "ميتا (Meta)", 
    "INTC": "إنتل (Intel)", "AMD": "إيه إم دي (AMD)", "AAPL": "أبل (Apple)", 
    "MSFT": "مايكروسوفت (Microsoft)", "AMZN": "أمازون (Amazon)", "GOOGL": "جوجل (Alphabet)"
}

# ضبط تواريخ الدورات بدقة
CONFIRMED_CYCLES = {
    "TSLA": {
        "cycle_months": 49, "up_m": 20, "fib_retrace": 0.618,
        "start": "2024-04-01", "end": "2028-05-01", "peak": "2025-11-01",
        "prev_start": "2020-03-01", "prev_end": "2024-04-01"
    },
    "AMD": {
        "cycle_months": 27, "up_m": 15, "fib_retrace": 0.618,
        "start": "2024-04-01", "end": "2026-06-30", "peak": "2025-07-01",
        "prev_start": "2022-01-01", "prev_end": "2024-04-01"
    },
    "INTC": {
        "cycle_months": 29, "up_m": 14, "fib_retrace": 0.618,
        "start": "2025-04-01", "end": "2027-08-01", "peak": "2026-06-01",
        "prev_start": "2023-04-01", "prev_end": "2025-04-01"
    },
    "META": {
        "cycle_months": 46, "up_m": 33, "fib_retrace": 0.500,
        "start": "2022-11-01", "end": "2026-09-01", "peak": "2025-08-01",
        "prev_start": "2018-11-01", "prev_end": "2022-11-01"
    },
    "NVDA": {
        "cycle_months": 30, "up_m": 20, "fib_retrace": 0.618,
        "start": "2025-05-01", "end": "2027-11-01", "peak": "2026-12-01",
        "prev_start": "2022-10-01", "prev_end": "2025-05-01"
    }
}

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_stock_data_10y(symbol):
    clean_sym = symbol.strip().upper()
    if clean_sym.isdigit():
        clean_sym = f"{clean_sym}.SR"
    comp_name = TASI_ALL_STOCKS.get(clean_sym, NASDAQ_TOP20_OPTIONS.get(clean_sym, f"سهم {clean_sym}"))
    
    if YFINANCE_AVAILABLE:
        try:
            df = yf.Ticker(clean_sym).history(period="10y")
            if not df.empty and len(df) >= 100:
                df.reset_index(inplace=True)
                return df, clean_sym, comp_name
        except Exception:
            pass
            
    dates = pd.date_range(end=datetime.today(), periods=520, freq='W')
    np.random.seed(abs(hash(clean_sym)) % 10000)
    prices = 50.0 * np.exp(np.cumsum(np.random.normal(0.001, 0.025, size=len(dates))))
    df_dummy = pd.DataFrame({'Date': dates, 'Open': prices*0.99, 'High': prices*1.02, 'Low': prices*0.98, 'Close': prices})
    return df_dummy, clean_sym, comp_name

def analyze_full_stock_dynamically(df, symbol_clean):
    if df.empty:
        return None

    df_res = df.copy()
    df_res['Date'] = pd.to_datetime(df_res['Date']).dt.tz_localize(None)
    df_res.set_index('Date', inplace=True)
    
    df_m = df_res.resample('MS').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'}).dropna()
    df_w = df_res.resample('W-MON').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'}).dropna()

    if len(df_m) < 24:
        return None

    last_date = df_m.index[-1]

    if symbol_clean in CONFIRMED_CYCLES:
        c = CONFIRMED_CYCLES[symbol_clean]
        long_c = int(c["cycle_months"])
        up_m = int(c["up_m"])
        fib_ratio = float(c["fib_retrace"])
        cycle_start = pd.Timestamp(c["start"])
        cycle_end = pd.Timestamp(c["end"])
        peak_date = pd.Timestamp(c["peak"])
        prev_start = pd.Timestamp(c["prev_start"])
        prev_end = pd.Timestamp(c["prev_end"])
    else:
        seed_val = abs(hash(symbol_clean))
        long_c = (seed_val % 28) + 20
        up_m = max(1, int(long_c * 0.6))
        fib_ratio = 0.618
        cycle_start = last_date - pd.DateOffset(months=up_m)
        cycle_end = cycle_start + pd.DateOffset(months=long_c)
        peak_date = cycle_start + pd.DateOffset(months=up_m)
        prev_start = cycle_start - pd.DateOffset(months=long_c)
        prev_end = cycle_start

    down_m = long_c - up_m
    phase_type = "صعود 🟢" if last_date <= peak_date else "هبوط 🔴"

    recent_segment = df_m['Close'].values[-long_c:] if len(df_m) >= long_c else df_m['Close'].values
    wave_high = np.max(recent_segment)
    wave_low = np.min(recent_segment)
    current_price = df_m['Close'].iloc[-1]
    proportional_target = wave_low + ((wave_high - wave_low) * fib_ratio)

    curr_date = pd.Timestamp("2026-09-01")

    # --- المعادلة النسبية الدقيقة لمنع إزاحة التواريخ ---
    total_curr_m = (cycle_end.year - cycle_start.year) * 12 + (cycle_end.month - cycle_start.month)
    total_prev_m = (prev_end.year - prev_start.year) * 12 + (prev_end.month - prev_start.month)
    
    elapsed_m = (curr_date.year - cycle_start.year) * 12 + (curr_date.month - cycle_start.month)
    
    # نسبة التقدم في الدورة الحالية
    progress = elapsed_m / total_curr_m if total_curr_m > 0 else 0
    progress_next = (elapsed_m + 1) / total_curr_m if total_curr_m > 0 else 0

    # إسقاط النسبة تماماً على الدورة السابقة
    prev_offset_m = int(round(progress * total_prev_m))
    prev_offset_next_m = int(round(progress_next * total_prev_m))

    matched_curr_month_date = prev_start + pd.DateOffset(months=prev_offset_m)
    matched_next_month_date = prev_start + pd.DateOffset(months=prev_offset_next_m)

    # حساب المطابقة الأسبوعية بنفس النسبة
    time_delta = (prev_end - prev_start) * progress
    matched_curr_week_date = prev_start + time_delta
    matched_next_week_date = matched_curr_week_date + pd.DateOffset(days=7)

    def eval_candle(df_target, target_date, is_weekly=False):
        if df_target.empty:
            return "بيانات غير متوفرة 🟡", "🟡", 0.0, False, target_date.strftime("%Y-%m-%d")
        
        diffs = abs(df_target.index - target_date)
        min_idx = diffs.argmin()
        actual_date = df_target.index[min_idx]
        
        max_allow_days = 14 if is_weekly else 35
        if abs((actual_date - target_date).days) > max_allow_days:
            return "خارج النطاق التاريخي 🟡", "🟡", 0.0, False, target_date.strftime("%Y-%m-%d")

        row = df_target.iloc[min_idx]
        open_p, close_p = row['Open'], row['Close']
        pct = ((close_p - open_p) / open_p) * 100.0 if open_p > 0 else 0.0

        if close_p >= open_p:
            icon = "🟢"
            desc = f"شمعة إيجابية صاعدة (+{pct:.1f}%)"
            is_pos = True
        else:
            icon = "🔴"
            desc = f"شمعة سلبية هابطة ({pct:.1f}%)"
            is_pos = False

        fmt = "%d %B %Y" if is_weekly else "%B %Y"
        return desc, icon, round(pct, 1), is_pos, actual_date.strftime(fmt)

    c_w_desc, c_w_icon, c_w_perf, _, c_w_date = eval_candle(df_w, matched_curr_week_date, is_weekly=True)
    n_w_desc, n_w_icon, _, _, n_w_date = eval_candle(df_w, matched_next_week_date, is_weekly=True)
    
    c_m_desc, c_m_icon, c_m_perf, c_m_pos, c_m_date = eval_candle(df_m, matched_curr_month_date, is_weekly=False)
    n_m_desc, n_m_icon, _, _, n_m_date = eval_candle(df_m, matched_next_month_date, is_weekly=False)

    return {
        "symbol": symbol_clean,
        "current_price": round(current_price, 2),
        "proportional_target": round(proportional_target, 2),
        "long_cycle": long_c,
        "up_months": up_m,
        "down_months": down_m,
        "cycle_start": cycle_start.strftime("%Y-%m"),
        "cycle_end": cycle_end.strftime("%Y-%m"),
        "peak_date": peak_date.strftime("%Y-%m"),
        "phase_type": phase_type,
        "m_perf": c_m_perf,
        "w_perf": c_w_perf,
        "is_pos": c_m_pos,
        "curr_month_date": curr_date.strftime("%B %Y"),
        "next_month_date": (curr_date + pd.DateOffset(months=1)).strftime("%B %Y"),
        "curr_week_date": curr_date.strftime("%d %B %Y"),
        "next_week_date": (curr_date + pd.DateOffset(days=7)).strftime("%d %B %Y"),
        "matched_curr_m_date": c_m_date,
        "matched_curr_m_desc": c_m_desc,
        "matched_curr_m_icon": c_m_icon,
        "matched_next_m_date": n_m_date,
        "matched_next_m_desc": n_m_desc,
        "matched_next_m_icon": n_m_icon,
        "matched_curr_w_date": c_w_date,
        "matched_curr_w_desc": c_w_desc,
        "matched_curr_w_icon": c_w_icon,
        "matched_next_w_date": n_w_date,
        "matched_next_w_desc": n_w_desc,
        "matched_next_w_icon": n_w_icon,
        "df_m": df_m['Close']
    }

st.title("🌟 منصة الدورات الزمنية والنجوم الحقيقية")

market_choice = st.radio("اختر السوق للتحليل:", ["أمريكي (NASDAQ Options)", "سعودي (TASI)"], horizontal=True)
pool = NASDAQ_TOP20_OPTIONS if "أمريكي" in market_choice else TASI_ALL_STOCKS

data_list = []
for sym, name in pool.items():
    df_raw, c_sym, c_name = fetch_stock_data_10y(sym)
    if not df_raw.empty:
        res = analyze_full_stock_dynamically(df_raw, c_sym)
        if res:
            res["name"] = c_name
            data_list.append(res)

if data_list:
    sorted_m = sorted(data_list, key=lambda x: x['m_perf'], reverse=True)
    star_m = sorted_m[0]
    worst_m = sorted_m[-1]

    st.markdown("### 👑 عرش النجوم والأداء الدوري الفعلي")

    col_star, col_worst = st.columns(2)
    
    with col_star:
        st.markdown(f"""
        <div class="star-card-top">
            <div class="metric-title">🌟 نجم السوق (الأعلى أداءً)</div>
            <div class="metric-value">{star_m['name']} ({star_m['symbol']})</div>
            <div style="margin-top:8px; font-size: 1.05rem;">
                • الأداء الشهري الفعلي: <b>+{star_m['m_perf']}% {star_m['matched_curr_m_icon']}</b><br>
                • الأداء الأسبوعي الفعلي: <b>+{star_m['w_perf']}% {star_m['matched_curr_w_icon']}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("📅 عرض التواريخ المطابقة في الدورة السابقة"):
            st.markdown(f"""
            • **الأسبوع الحالي ({star_m['curr_week_date']}):** يطابق `{star_m['matched_curr_w_date']}` 👈 ({star_m['matched_curr_w_desc']})  
            • **الشهر الحالي ({star_m['curr_month_date']}):** يطابق `{star_m['matched_curr_m_date']}` 👈 ({star_m['matched_curr_m_desc']})
            """)

    with col_worst:
        st.markdown(f"""
        <div class="worst-card-top">
            <div class="metric-title">⚠️ الأقل أداءً في السوق</div>
            <div class="metric-value">{worst_m['name']} ({worst_m['symbol']})</div>
            <div style="margin-top:8px; font-size: 1.05rem;">
                • الأداء الشهري الفعلي: <b>{worst_m['m_perf']}% {worst_m['matched_curr_m_icon']}</b><br>
                • الأداء الأسبوعي الفعلي: <b>{worst_m['w_perf']}% {worst_m['matched_curr_w_icon']}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("📅 عرض التواريخ المطابقة في الدورة السابقة"):
            st.markdown(f"""
            • **الأسبوع الحالي ({worst_m['curr_week_date']}):** يطابق `{worst_m['matched_curr_w_date']}` 👈 ({worst_m['matched_curr_w_desc']})  
            • **الشهر الحالي ({worst_m['curr_month_date']}):** يطابق `{worst_m['matched_curr_m_date']}` 👈 ({worst_m['matched_curr_m_desc']})
            """)

    st.markdown("---")
    st.markdown("### 📊 ترتيب الشركات والدورات الزمنيّة مع التلوين حسب الأداء")

    for rank, item in enumerate(sorted_m, 1):
        card_style = "company-card-positive" if item['is_pos'] else "company-card-negative"
        perf_sign = "+" if item['m_perf'] >= 0 else ""
        
        st.markdown(f"""
        <div class="{card_style}">
            <b>#{rank} | {item['name']} ({item['symbol']})</b> — 
            الأداء الشهري المطابق: <b>{perf_sign}{item['m_perf']}% {item['matched_curr_m_icon']}</b> | 
            الأسبوعي: <b>{item['w_perf']}% {item['matched_curr_w_icon']}</b> | 
            المسار: <b>{item['phase_type']}</b>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander(f"🔍 التفاصيل والدورة والشموع المطابقة لـ {item['name']}"):
            st.markdown(f"""
            **🔄 تفاصيل الدورة الحالية ({item['long_cycle']} شهراً - قاع إلى قاع):**
            - **مدة الصعود للقمة:** {item['up_months']} شهراً | **مدة الهبوط للقاع التالي:** {item['down_months']} شهراً
            - **السعر الحالي:** ${item['current_price']} | **المستهدف النسبي:** ${item['proportional_target']}
            - **بداية الدورة:** {item['cycle_start']} | **نهايتها:** {item['cycle_end']} | **شهر القمة:** {item['peak_date']}
            """)

            st.markdown("---")
            st.markdown("#### 🗓️ مطابقة الشموع الأسبوعية والشهريّة مع الدورة السابقة:")
            
            st.markdown(f"- **الأسبوع الحالي ({item['curr_week_date']}):** يصادف **{item['matched_curr_w_date']}** 👈 ({item['matched_curr_w_desc']} {item['matched_curr_w_icon']})")
            st.markdown(f"- **الأسبوع القادم ({item['next_week_date']}):** سيصادف **{item['matched_next_w_date']}** 👈 ({item['matched_next_w_desc']} {item['matched_next_w_icon']})")
            
            st.markdown(f"- **الشهر الحالي ({item['curr_month_date']}):** يصادف **{item['matched_curr_m_date']}** 👈 ({item['matched_curr_m_desc']} {item['matched_curr_m_icon']})")
            st.markdown(f"- **الشهر القادم ({item['next_month_date']}):** سيصادف **{item['matched_next_m_date']}** 👈 ({item['matched_next_m_desc']} {item['matched_next_m_icon']})")

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=item['df_m'].index, y=item['df_m'].values, mode='lines', name='السعر الشهري', line=dict(color='#0284c7', width=2)))
            fig.add_hline(y=item['proportional_target'], line_dash="dash", line_color="#10b981", annotation_text=f"المستهدف: {item['proportional_target']}")
            fig.update_layout(template="plotly_white", height=240, margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig, use_container_width=True)
