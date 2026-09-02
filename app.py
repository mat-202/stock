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

st.set_page_config(page_title="منصة الدورات الزمنية والدقيقة", page_icon="📈", layout="wide")

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
    }
    .worst-card-top {
        background: linear-gradient(135deg, #9f1239 0%, #be123c 100%);
        color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 10px;
    }
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

# القوائم
TASI_ALL_STOCKS = {
    "2222.SR": "أرامكو السعودية", "1120.SR": "الراجحي", "2010.SR": "سابك", "1180.SR": "الأهلي",
    "2170.SR": "اللجين", "4323.SR": "سمو", "2082.SR": "أكوا باور", "7010.SR": "STC",
    "2020.SR": "سابك للمغذيات", "2350.SR": "كيان السعودية", "1150.SR": "الإنماء", "1010.SR": "الرياض",
    "1211.SR": "معادن", "4190.SR": "جرير", "4003.SR": "أسترا الصناعية", "2381.SR": "بترو رابغ",
    "7020.SR": "موبايلي", "4030.SR": "البحري", "4260.SR": "بدجت السعودية", "1810.SR": "سيسكو"
}

NASDAQ_TOP20_OPTIONS = {
    "TSLA": "تيسلا (Tesla)", "NVDA": "أنفيديا (Nvidia)", "META": "ميتا (Meta)", 
    "INTC": "إنتل (Intel)", "AMD": "إيه إم دي (AMD)", "AAPL": "أبل (Apple)", 
    "MSFT": "مايكروسوفت (Microsoft)", "AMZN": "أمازون (Amazon)", "GOOGL": "جوجل (Alphabet)", 
    "NFLX": "نتفليكس (Netflix)"
}

# إعدادات الدورات (تواريخ البداية والنهاية والقمة)
CYCLES_CONFIG = {
    "TSLA": {"start": "2024-04-01", "end": "2028-05-01", "prev_start": "2020-03-01", "prev_end": "2024-03-31"},
    "AMD":  {"start": "2024-04-01", "end": "2026-06-30", "prev_start": "2022-01-01", "prev_end": "2024-03-31"},
    "INTC": {"start": "2025-04-01", "end": "2027-08-01", "prev_start": "2023-04-01", "prev_end": "2025-03-31"},
    "META": {"start": "2022-11-01", "end": "2026-09-01", "prev_start": "2018-12-01", "prev_end": "2022-10-31"},
    "NVDA": {"start": "2025-05-01", "end": "2027-11-01", "prev_start": "2022-10-01", "prev_end": "2025-04-30"}
}

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_stock_data(symbol):
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
    return pd.DataFrame(), clean_sym, comp_name

def analyze_stock_dynamically(df, symbol_clean):
    if df.empty:
        return None
        
    df_res = df.copy()
    df_res['Date'] = pd.to_datetime(df_res['Date']).dt.tz_localize(None)
    df_res.set_index('Date', inplace=True)
    
    # تجميع البيانات شهرياً بحساب الفتح والإغلاق الحقيقي
    df_monthly = df_res.resample('MS').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last'
    }).dropna()

    if len(df_monthly) < 24:
        return None

    # إعدادات الدورة
    cfg = CYCLES_CONFIG.get(symbol_clean, {
        "start": "2024-01-01", "end": "2028-01-01",
        "prev_start": "2020-01-01", "prev_end": "2024-01-01"
    })
    
    c_start = pd.Timestamp(cfg["start"])
    p_start = pd.Timestamp(cfg["prev_start"])
    
    # الشهر الحالي في الشارت (مثلاً سبتمبر 2026)
    curr_date = pd.Timestamp("2026-09-01")
    
    # حساب أوفست الأشهر بين بداية الدورة والشهر الحالي
    month_offset = (curr_date.year - c_start.year) * 12 + (curr_date.month - c_start.month)
    
    # تحديد الشهر المطابق الحقيقي في الدورة السابقة
    matched_prev_date = p_start + pd.DateOffset(months=month_offset)
    next_prev_date = matched_prev_date + pd.DateOffset(months=1)

    # دالة فحص لون وسلوك الشمعة الحقيقية من بيانات ياهو فاينانس
    def get_candle_analysis(target_date):
        # البحث عن الشمعة في التاريخ المطابق بالضبط
        matching_rows = df_monthly[(df_monthly.index.year == target_date.year) & (df_monthly.index.month == target_date.month)]
        if not matching_rows.empty:
            row = matching_rows.iloc[0]
            open_p, close_p = row['Open'], row['Close']
            pct_change = ((close_p - open_p) / open_p) * 100
            
            if close_p < open_p:
                color_icon = "🔴"
                behavior = f"شمعة سلبية هابطة ({pct_change:.1f}%)"
                is_pos = False
            else:
                color_icon = "🟢"
                behavior = f"شمعة إيجابية صاعدة (+{pct_change:.1f}%)"
                is_pos = True
            return behavior, color_icon, pct_change, is_pos
        else:
            return "بيانات الشمعة غير متوفرة 🟡", "🟡", 0.0, False

    # فحص الشهر الحالي والشهر القادم
    curr_behavior, curr_icon, curr_perf, curr_is_pos = get_candle_analysis(matched_prev_date)
    next_behavior, next_icon, _, _ = get_candle_analysis(next_prev_date)

    current_price = df_monthly['Close'].iloc[-1]

    return {
        "symbol": symbol_clean,
        "current_price": round(current_price, 2),
        "curr_month_date": curr_date.strftime("%B %Y"),
        "matched_prev_date_str": matched_prev_date.strftime("%B %Y"),
        "curr_behavior": curr_behavior,
        "curr_icon": curr_icon,
        "curr_perf": round(curr_perf, 1),
        "curr_is_pos": curr_is_pos,
        "next_month_date": (curr_date + pd.DateOffset(months=1)).strftime("%B %Y"),
        "next_matched_prev_date_str": next_prev_date.strftime("%B %Y"),
        "next_behavior": next_behavior,
        "next_icon": next_icon,
        "df_m": df_monthly['Close']
    }

st.title("📈 التحليل الدوري والتطابق الحقيقي لشموع الأسهم")

market_choice = st.radio("اختر السوق:", ["أمريكي (NASDAQ)", "سعودي (TASI)"], horizontal=True)
pool = NASDAQ_TOP20_OPTIONS if "أمريكي" in market_choice else TASI_ALL_STOCKS

results = []
for sym, name in pool.items():
    df_raw, c_sym, c_name = fetch_stock_data(sym)
    if not df_raw.empty:
        res = analyze_stock_dynamically(df_raw, c_sym)
        if res:
            res["name"] = c_name
            results.append(res)

if results:
    # ترتيب الشركات حسب الأداء الحقيقي للشمعة المطابقة
    sorted_res = sorted(results, key=lambda x: x['curr_perf'], reverse=True)
    
    st.markdown("### 📊 نتائج مطابقة الشموع الحقيقية من الشارت")

    for rank, item in enumerate(sorted_res, 1):
        card_class = "company-card-positive" if item['curr_is_pos'] else "company-card-negative"
        
        st.markdown(f"""
        <div class="{card_class}">
            <b>#{rank} | {item['name']} ({item['symbol']})</b> — 
            الشمعة المطابقة: <b>{item['matched_prev_date_str']}</b> | 
            الأداء الفعلي للشمعة: <b>{item['curr_perf']}% {item['curr_icon']}</b> | 
            السعر الحالي: <b>${item['current_price']}</b>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander(f"🔍 تفاصيل الشمعة المطابقة لـ {item['name']}"):
            st.markdown(f"""
            - 🗓️ **الشهر الحالي ({item['curr_month_date']}):** تطابقه شمعة **{item['matched_prev_date_str']}** 👈 **{item['curr_behavior']} {item['curr_icon']}**
            - 🗓️ **الشهر القادم ({item['next_month_date']}):** تطابقه شمعة **{item['next_matched_prev_date_str']}** 👈 **{item['next_behavior']} {item['next_icon']}**
            """)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=item['df_m'].index, y=item['df_m'].values, mode='lines', name='السعر الشهري', line=dict(color='#0284c7', width=2)))
            fig.update_layout(template="plotly_white", height=230, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("جاري جلب البيانات من yfinance، يرجى الانتظار...")
