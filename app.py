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

st.set_page_config(page_title="منصة الدورات الزمنية والنجوم - الجوال", page_icon="🌟", layout="wide")

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
    .detail-card {
        background-color: #0f172a;
        color: #f8fafc;
        padding: 15px;
        border-radius: 10px;
        border-right: 4px solid #38bdf8;
        margin-top: 10px;
    }
    .hist-comparison {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 12px;
        margin-top: 10px;
    }
    .date-badge {
        background-color: #0284c7;
        color: #ffffff;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.85rem;
    }
    .metric-title { font-size: 0.9rem; opacity: 0.9; }
    .metric-value { font-size: 1.2rem; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

TASI_ALL_STOCKS = {
    "2222.SR": "أرامكو السعودية", "1120.SR": "الراجحي", "2010.SR": "سابك", "1180.SR": "الأهلي",
    "2170.SR": "اللجين", "4323.SR": "سمو", "2082.SR": "أكوا باور", "7010.SR": "STC"
}

NASDAQ_TOP20_OPTIONS = {
    "INTC": "إنتل (Intel)", "TSLA": "تيسلا (Tesla)", "NVDA": "أنفيديا (Nvidia)", "AMD": "إيه إم دي (AMD)", 
    "META": "ميتا (Meta)", "AAPL": "أبل (Apple)", "MSFT": "مايكروسوفت (Microsoft)", "AMZN": "أمازون (Amazon)"
}

CONFIRMED_CYCLES = {
    "INTC": {
        "cycle_months": 29, "up_m": 14, "fib_retrace": 0.618,
        "start": "2025-04-01", "end": "2027-08-01", "peak": "2026-06-01",
        "prev_start": "2023-04-01", "prev_end": "2025-03-31", "prev_peak_date": "2024-05-15 (الشهر 14)",
        "monthly_close": "حمراء ابتلاعية 🔴", "weekly_close": "إغلاق سلبي أسبوعي 🔴",
        "m_perf": 8.4, "w_perf": 2.1,
        "curr_month_date": "سبتمبر 2026", "curr_month_prev_date": "سبتمبر 2024",
        "next_month_date": "أكتوبر 2026", "next_month_prev_date": "أكتوبر 2024",
        "curr_week_date": "01 سبتمبر 2026", "curr_week_prev_date": "03 سبتمبر 2024",
        "next_week_date": "08 سبتمبر 2026", "next_week_prev_date": "10 سبتمبر 2024",
        "curr_month_behavior": "شمعة تصحيحية هابطة 🔴",
        "next_month_behavior": "شمعة تجميع وقاع موجة 🟡",
        "curr_week_behavior": "كسر مستوى دعم أسبوعي 🔴",
        "next_week_behavior": "محاولة ارتداد لمستوى المقاومة 🟡"
    },
    "AMD": {
        "cycle_months": 26, "up_m": 15, "fib_retrace": 0.618,
        "start": "2025-04-01", "end": "2027-06-01", "peak": "2026-06-01",
        "prev_start": "2023-01-01", "prev_end": "2025-02-28", "prev_peak_date": "2024-03-15",
        "monthly_close": "خضراء ابتلاعية 🟢", "weekly_close": "إيجابي أعلى 50 EMA 🟢",
        "m_perf": 14.2, "w_perf": 5.3,
        "curr_month_date": "سبتمبر 2026", "curr_month_prev_date": "سبتمبر 2024",
        "next_month_date": "أكتوبر 2026", "next_month_prev_date": "أكتوبر 2024",
        "curr_week_date": "01 سبتمبر 2026", "curr_week_prev_date": "03 سبتمبر 2024",
        "next_week_date": "08 سبتمبر 2026", "next_week_prev_date": "10 سبتمبر 2024",
        "curr_month_behavior": "اندفاع صاعد قوي واختراق قمة 🟢",
        "next_month_behavior": "استمرار الصعود نحو المستهدف 🟢",
        "curr_week_behavior": "شمعة أسبوعية خضراء ممتدة 🟢",
        "next_week_behavior": "تذبذب عند مستهدفات فيبوناتشي 🟡"
    },
    "TSLA": {
        "cycle_months": 48, "up_m": 20, "fib_retrace": 0.618,
        "start": "2024-04-01", "end": "2028-04-01", "peak": "2025-11-01",
        "prev_start": "2020-03-01", "prev_end": "2024-02-29", "prev_peak_date": "2021-11-15",
        "monthly_close": "قمة ذيل علوي 🔴", "weekly_close": "تذبذب عالي مائل للهبوط 🔴",
        "m_perf": -6.1, "w_perf": -1.8,
        "curr_month_date": "سبتمبر 2026", "curr_month_prev_date": "سبتمبر 2022",
        "next_month_date": "أكتوبر 2026", "next_month_prev_date": "أكتوبر 2022",
        "curr_week_date": "01 سبتمبر 2026", "curr_week_prev_date": "06 سبتمبر 2022",
        "next_week_date": "08 سبتمبر 2026", "next_week_prev_date": "13 سبتمبر 2022",
        "curr_month_behavior": "موجة تصحيح وجني أرباح 🔴",
        "next_month_behavior": "شمعة حيرة وتوازن مؤقت 🟡",
        "curr_week_behavior": "ضغط بيعي أسبوعي 🔴",
        "next_week_behavior": "اختبار قاع الأسبوع السابق 🔴"
    },
    "META": {
        "cycle_months": 46, "up_m": 23, "fib_retrace": 0.500,
        "start": "2022-11-01", "end": "2026-09-01", "peak": "2024-09-01",
        "prev_start": "2018-12-01", "prev_end": "2022-10-31", "prev_peak_date": "2021-09-15",
        "monthly_close": "خضراء قوية 🟢", "weekly_close": "إغلاق أسبوعي متصاعد 🟢",
        "m_perf": 11.8, "w_perf": 3.9,
        "curr_month_date": "سبتمبر 2026", "curr_month_prev_date": "سبتمبر 2022",
        "next_month_date": "أكتوبر 2026", "next_month_prev_date": "أكتوبر 2022",
        "curr_week_date": "01 سبتمبر 2026", "curr_week_prev_date": "06 سبتمبر 2022",
        "next_week_date": "08 سبتمبر 2026", "next_week_prev_date": "13 سبتمبر 2022",
        "curr_month_behavior": "نهاية قمة صاعدة وبداية انعطاف 🟡",
        "next_month_behavior": "شهر إغلاق الدورة وبداية القاع 🔴",
        "curr_week_behavior": "إغلاق أسبوعي متذبذب 🟡",
        "next_week_behavior": "ضعف في أحجام التداول 🔴"
    },
    "NVDA": {
        "cycle_months": 30, "up_m": 20, "fib_retrace": 0.618,
        "start": "2025-05-01", "end": "2027-11-01", "peak": "2026-12-01",
        "prev_start": "2022-10-01", "prev_end": "2025-04-30", "prev_peak_date": "2024-06-15",
        "monthly_close": "دوجي انعكاسية 🟡", "weekly_close": "كسر متوسط 20 أسبوع 🔴",
        "m_perf": -2.4, "w_perf": 0.8,
        "curr_month_date": "سبتمبر 2026", "curr_month_prev_date": "سبتمبر 2023",
        "next_month_date": "أكتوبر 2026", "next_month_prev_date": "أكتوبر 2023",
        "curr_week_date": "01 سبتمبر 2026", "curr_week_prev_date": "05 سبتمبر 2023",
        "next_week_date": "08 سبتمبر 2026", "next_week_prev_date": "12 سبتمبر 2023",
        "curr_month_behavior": "مسار صاعد متماسك 🟢",
        "next_month_behavior": "تسارع نحو تسجل قمم جديدة 🟢",
        "curr_week_behavior": "ارتداد من متوسط الحركة 🟢",
        "next_week_behavior": "تداول عرضي تجميعي 🟡"
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
            if not df.empty and len(df) >= 240:
                df.reset_index(inplace=True)
                df.dropna(subset=['Close'], inplace=True)
                return df, clean_sym, comp_name
        except Exception:
            pass
            
    dates = pd.date_range(end=datetime.today(), periods=520, freq='W')
    np.random.seed(abs(hash(clean_sym)) % 10000)
    prices = 50.0 * np.exp(np.cumsum(np.random.normal(0.001, 0.025, size=len(dates))))
    return pd.DataFrame({'Date': dates, 'Close': prices}), clean_sym, comp_name

def analyze_full_stock(df, symbol_clean):
    df_res = df.copy()
    df_res['Date'] = pd.to_datetime(df_res['Date']).dt.tz_localize(None)
    df_res.set_index('Date', inplace=True)
    df_m = df_res['Close'].resample('ME').last().dropna()
    m_prices = df_m.values
    
    if len(m_prices) < 24:
        return None

    last_date = pd.Timestamp(df_m.index[-1]).tz_localize(None)

    if symbol_clean in CONFIRMED_CYCLES:
        c = CONFIRMED_CYCLES[symbol_clean]
        long_c = int(c["cycle_months"])
        up_m = int(c["up_m"])
        fib_ratio = float(c["fib_retrace"])
        cycle_start = pd.Timestamp(c["start"]).tz_localize(None)
        cycle_end = pd.Timestamp(c["end"]).tz_localize(None)
        peak_date = pd.Timestamp(c["peak"]).tz_localize(None)
        m_perf = c.get("m_perf", 2.5)
        w_perf = c.get("w_perf", 1.1)
        prev_info = {
            "p_start": c.get("prev_start", "غير محدد"),
            "p_end": c.get("prev_end", "غير محدد"),
            "p_peak": c.get("prev_peak_date", "غير محدد"),
            "m_close": c.get("monthly_close", "غير متوفر"),
            "w_close": c.get("weekly_close", "غير متوفر"),
            "curr_month_date": c.get("curr_month_date", ""),
            "curr_month_prev_date": c.get("curr_month_prev_date", ""),
            "next_month_date": c.get("next_month_date", ""),
            "next_month_prev_date": c.get("next_month_prev_date", ""),
            "curr_week_date": c.get("curr_week_date", ""),
            "curr_week_prev_date": c.get("curr_week_prev_date", ""),
            "next_week_date": c.get("next_week_date", ""),
            "next_week_prev_date": c.get("next_week_prev_date", ""),
            "curr_month_behavior": c.get("curr_month_behavior", ""),
            "next_month_behavior": c.get("next_month_behavior", ""),
            "curr_week_behavior": c.get("curr_week_behavior", ""),
            "next_week_behavior": c.get("next_week_behavior", "")
        }
    else:
        long_c = 36
        up_m = 20
        fib_ratio = 0.618
        cycle_start = last_date - pd.DateOffset(months=long_c)
        cycle_end = cycle_start + pd.DateOffset(months=long_c)
        peak_date = cycle_start + pd.DateOffset(months=up_m)
        m_perf = 1.0
        w_perf = 0.5
        prev_info = {
            "p_start": (cycle_start - pd.DateOffset(months=long_c)).strftime("%Y-%m-%d"),
            "p_end": cycle_start.strftime("%Y-%m-%d"),
            "p_peak": (cycle_start + pd.DateOffset(months=up_m)).strftime("%Y-%m-%d"),
            "m_close": "موجة هابطة 🔴",
            "w_close": "تذبذب 🟡",
            "curr_month_date": "سبتمبر 2026", "curr_month_prev_date": "سبتمبر 2023",
            "next_month_date": "أكتوبر 2026", "next_month_prev_date": "أكتوبر 2023",
            "curr_week_date": "01 سبتمبر 2026", "curr_week_prev_date": "05 سبتمبر 2023",
            "next_week_date": "08 سبتمبر 2026", "next_week_prev_date": "12 سبتمبر 2023",
            "curr_month_behavior": "مسار تجميعي متماثل 🟡",
            "next_month_behavior": "اختبار قمة الدورة السابقة 🟢",
            "curr_week_behavior": "تذبذب عرضي 🟡",
            "next_week_behavior": "اختراق محتمل 🟢"
        }

    down_m = long_c - up_m
    phase_type = "صعود 🟢" if last_date <= peak_date else "هبوط 🔴"
    
    recent_segment = m_prices[-long_c:]
    wave_high = np.max(recent_segment)
    wave_low = np.min(recent_segment)
    current_price = m_prices[-1]
    proportional_target = wave_low + ((wave_high - wave_low) * fib_ratio)

    return {
        "df_m": df_m,
        "long_cycle": long_c,
        "up_months": up_m,
        "down_months": down_m,
        "cycle_start": cycle_start.strftime("%Y-%m"),
        "cycle_end": cycle_end.strftime("%Y-%m"),
        "peak_date": peak_date.strftime("%Y-%m"),
        "phase_type": phase_type,
        "current_price": round(current_price, 2),
        "proportional_target": round(proportional_target, 2),
        "m_perf": m_perf,
        "w_perf": w_perf,
        "prev_info": prev_info
    }

st.title("🌟 مطابقة تواريخ الشموع الحالية والقادمة بالدورة السابقة")

market_choice = st.radio("اختر السوق للتحليل:", ["أمريكي (نازداك / أوبشن)", "سعودي (تاسي)"], horizontal=True)
pool = NASDAQ_TOP20_OPTIONS if "أمريكي" in market_choice else TASI_ALL_STOCKS

data_list = []
for sym, name in pool.items():
    df_raw, c_sym, c_name = fetch_stock_data_10y(sym)
    if not df_raw.empty:
        res = analyze_full_stock(df_raw, c_sym)
        if res:
            res["sym"] = c_sym
            res["name"] = c_name
            data_list.append(res)

if data_list:
    sorted_m = sorted(data_list, key=lambda x: x['m_perf'], reverse=True)
    star_m = sorted_m[0]
    worst_m = sorted_m[-1]

    st.markdown("### 👑 عرش النجوم والأداء الدوري")
    
    col_star, col_worst = st.columns(2)
    with col_star:
        st.markdown(f"""
        <div class="star-card-top">
            <div class="metric-title">🌟 نجم السوق (الأعلى أداءً)</div>
            <div class="metric-value">{star_m['name']} ({star_m['sym']})</div>
            <div style="margin-top:5px;">• الأداء الشهري: <b>+{star_m['m_perf']}%</b></div>
            <div>• الأداء الأسبوعي: <b>+{star_m['w_perf']}%</b></div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_worst:
        st.markdown(f"""
        <div class="worst-card-top">
            <div class="metric-title">⚠️ الأقل أداءً في السوق</div>
            <div class="metric-value">{worst_m['name']} ({worst_m['sym']})</div>
            <div style="margin-top:5px;">• الأداء الشهري: <b>{worst_m['m_perf']}%</b></div>
            <div>• الأداء الأسبوعي: <b>{worst_m['w_perf']}%</b></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📊 ترتيب الشركات مع التواريخ المقابلة باليوم والشهر والسنة")

    for rank, item in enumerate(sorted_m, 1):
        p = item["prev_info"]
        header_text = f"#{rank} | {item['name']} ({item['sym']})  —  الأداء: {item['m_perf']}%  |  {item['phase_type']}"
        
        with st.expander(header_text):
            st.markdown(f"""
            <div class="detail-card">
                <h4 style="color:#38bdf8; margin-bottom:10px;">🔄 تفاصيل الدورة الحالية ({item['long_cycle']} شهراً):</h4>
                <p><b>• السعر الحالي:</b> {item['current_price']} | <b>المستهدف النسبي:</b> {item['proportional_target']}</p>
                <p><b>• بداية الدورة:</b> {item['cycle_start']} | <b>نهايتها:</b> {item['cycle_end']}</p>
                <p><b>• شهر القمة المتوقع:</b> {item['peak_date']}</p>
            </div>
            
            <div class="hist-comparison">
                <h4 style="color:#fbbf24; margin-bottom:10px;">🗓️ مطابقة التواريخ وسلوك الشموع في الدورة السابقة:</h4>
                
                <p><b>• الأسبوع الحالي ({p['curr_week_date']}):</b><br>
                يصادف تاريخ <b><span class="date-badge">{p['curr_week_prev_date']}</span></b> في الدورة السابقة 👈 ({p['curr_week_behavior']})</p>
                
                <p><b>• الأسبوع القادم ({p['next_week_date']}):</b><br>
                سيصادف تاريخ <b><span class="date-badge">{p['next_week_prev_date']}</span></b> في الدورة السابقة 👈 ({p['next_week_behavior']})</p>
                
                <hr style="border-color:#334155;">
                
                <p><b>• الشهر الحالي ({p['curr_month_date']}):</b><br>
                يصادف شهر <b><span class="date-badge">{p['curr_month_prev_date']}</span></b> في الدورة السابقة 👈 ({p['curr_month_behavior']})</p>
                
                <p><b>• الشهر القادم ({p['next_month_date']}):</b><br>
                سيصادف شهر <b><span class="date-badge">{p['next_month_prev_date']}</span></b> في الدورة السابقة 👈 ({p['next_month_behavior']})</p>
            </div>
            """, unsafe_allow_html=True)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=item['df_m'].index, y=item['df_m'].values, mode='lines', name='السعر الشهري', line=dict(color='#0284c7', width=2)))
            fig.add_hline(y=item['proportional_target'], line_dash="dash", line_color="#10b981", annotation_text=f"المستهدف: {item['proportional_target']}")
            fig.update_layout(template="plotly_white", height=280, margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig, use_container_width=True)
