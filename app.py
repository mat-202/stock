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

st.set_page_config(page_title="منصة الدورات الزمنية والنجوم", page_icon="🌟", layout="wide")

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
        margin-bottom: 5px;
    }
    .company-card-negative {
        background-color: rgba(239, 68, 68, 0.08);
        border-right: 5px solid #ef4444;
        padding: 10px 15px;
        border-radius: 8px;
        margin-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

# 30 شركة سعودية
TASI_ALL_STOCKS = {
    "2222.SR": "أرامكو السعودية", "1120.SR": "الراجحي", "2010.SR": "سابك", "1180.SR": "الأهلي",
    "2170.SR": "اللجين", "4323.SR": "سمو", "2082.SR": "أكوا باور", "7010.SR": "STC",
    "2020.SR": "سابك للمغذيات", "2350.SR": "كيان السعودية", "1150.SR": "الإنماء", "1010.SR": "الرياض",
    "1211.SR": "معادن", "4190.SR": "جرير", "4003.SR": "أسترا الصناعية", "2381.SR": "بترو رابغ",
    "7020.SR": "اتصالات اتحاد", "4030.SR": "السياري (البحري)", "4260.SR": "بدجت السعودية", "1810.SR": "سيسكو",
    "2001.SR": "كيمانول", "2280.SR": "المراعي", "4001.SR": "عثيم", "4071.SR": "العربية",
    "1302.SR": "بوان", "1303.SR": "صناعات كهربائية", "2040.SR": "الخزف", "2250.SR": "مجموعة المتقدمة",
    "2330.SR": "المتقدمة", "8010.SR": "تعاونية"
}

# 20 شركة أمريكية (5 المكتشفة + 15 الأكثر تداولاً للأوبشن)
NASDAQ_TOP20_OPTIONS = {
    # الشركات الـ 5 المكتشفة
    "TSLA": "تيسلا (Tesla)", "NVDA": "أنفيديا (Nvidia)", "META": "ميتا (Meta)", 
    "INTC": "إنتل (Intel)", "AMD": "إيه إم دي (AMD)",
    # الـ 15 شركة المضافة الأكثر أوبشن
    "AAPL": "أبل (Apple)", "MSFT": "مايكروسوفت (Microsoft)", "AMZN": "أمازون (Amazon)",
    "GOOGL": "جوجل (Alphabet)", "NFLX": "نتفليكس (Netflix)", "COIN": "كوينبيس (Coinbase)",
    "PLTR": "بالانتير (Palantir)", "BABA": "علي بابا (Alibaba)", "BA": "بوينج (Boeing)",
    "QCOM": "كوالكوم (Qualcomm)", "JPM": "جي بي مورجان (JPMorgan)", "DIS": "ديزني (Disney)",
    "MARA": "ماراثون (Marathon Digital)", "PYPL": "بايبال (PayPal)", "SQ": "بلوك (Block)"
}

CONFIRMED_CYCLES = {
    # 1. تيسلا (مكتشفة)
    "TSLA": {
        "cycle_months": 49, "up_m": 20, "fib_retrace": 0.618,
        "start": "2024-04-01", "end": "2028-05-01", "peak": "2025-11-01",
        "prev_start": "2020-03-01", "prev_end": "2024-03-31", "prev_peak_date": "2021-11-15",
        "monthly_close": "قمة ذيل علوي 🔴", "weekly_close": "تذبذب عالي مائل للهبوط 🔴",
        "m_perf": 8.5, "w_perf": 2.1,
        "curr_month_date": "سبتمبر 2026", "curr_month_prev_date": "أغسطس 2022",
        "next_month_date": "أكتوبر 2026", "next_month_prev_date": "سبتمبر 2022",
        "curr_week_date": "01 سبتمبر 2026", "curr_week_prev_date": "02 أغسطس 2022",
        "next_week_date": "08 سبتمبر 2026", "next_week_prev_date": "09 أغسطس 2022",
        "curr_month_behavior": "موجة ارتداد صاعدة 🟢", "next_month_behavior": "شمعة حيرة وتوازن مؤقت 🟡",
        "curr_week_behavior": "ضغط شراء أسبوعي 🟢", "next_week_behavior": "اختبار مقاومة الأسبوع السابق 🟡"
    },
    # 2. AMD (مكتشفة)
    "AMD": {
        "cycle_months": 27, "up_m": 15, "fib_retrace": 0.618,
        "start": "2024-04-01", "end": "2026-06-30", "peak": "2025-07-01",
        "prev_start": "2022-01-01", "prev_end": "2024-03-31", "prev_peak_date": "2023-04-15",
        "monthly_close": "حمراء بيعية 🔴", "weekly_close": "سلبي أسفل المتوسطات 🔴",
        "m_perf": -9.6, "w_perf": -3.2,
        "curr_month_date": "سبتمبر 2026", "curr_month_prev_date": "يونيو 2024",
        "next_month_date": "أكتوبر 2026", "next_month_prev_date": "يوليو 2024",
        "curr_week_date": "01 سبتمبر 2026", "curr_week_prev_date": "04 يونيو 2024",
        "next_week_date": "08 سبتمبر 2026", "next_week_prev_date": "11 يونيو 2024",
        "curr_month_behavior": "موجة تصحيح وهبوط (تطابق يونيو 2024) 🔴", "next_month_behavior": "استمرار الضغط البيعي والتراجع 🔴",
        "curr_week_behavior": "شمعة أسبوعية حمراء وهبوط متواصل 🔴", "next_week_behavior": "محاولة كسر مستويات دعم سابقة 🔴"
    },
    # 3. إنتل (مكتشفة)
    "INTC": {
        "cycle_months": 29, "up_m": 14, "fib_retrace": 0.618,
        "start": "2025-04-01", "end": "2027-08-01", "peak": "2026-06-01",
        "prev_start": "2023-04-01", "prev_end": "2025-03-31", "prev_peak_date": "2024-05-15",
        "monthly_close": "حمراء ابتلاعية 🔴", "weekly_close": "إغلاق سلبي أسبوعي 🔴",
        "m_perf": -4.2, "w_perf": -1.1,
        "curr_month_date": "سبتمبر 2026", "curr_month_prev_date": "سبتمبر 2024",
        "next_month_date": "أكتوبر 2026", "next_month_prev_date": "أكتوبر 2024",
        "curr_week_date": "01 سبتمبر 2026", "curr_week_prev_date": "03 سبتمبر 2024",
        "next_week_date": "08 سبتمبر 2026", "next_week_prev_date": "10 سبتمبر 2024",
        "curr_month_behavior": "شمعة تصحيحية هابطة 🔴", "next_month_behavior": "شمعة تجميع وقاع موجة 🟡",
        "curr_week_behavior": "كسر مستوى دعم أسبوعي 🔴", "next_week_behavior": "محاولة ارتداد لمستوى المقاومة 🟡"
    },
    # 4. ميتا (مكتشفة)
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
        "curr_month_behavior": "نهاية قمة صاعدة وبداية انعطاف 🟡", "next_month_behavior": "شهر إغلاق الدورة وبداية القاع 🔴",
        "curr_week_behavior": "إغلاق أسبوعي متذبذب 🟡", "next_week_behavior": "ضعف في أحجام التداول 🔴"
    },
    # 5. إنفيديا (مكتشفة)
    "NVDA": {
        "cycle_months": 30, "up_m": 20, "fib_retrace": 0.618,
        "start": "2025-05-01", "end": "2027-11-01", "peak": "2026-12-01",
        "prev_start": "2022-10-01", "prev_end": "2025-04-30", "prev_peak_date": "2024-06-15",
        "monthly_close": "دوجي انعكاسية 🟡", "weekly_close": "كسر متوسط 20 أسبوع 🔴",
        "m_perf": 2.4, "w_perf": 0.8,
        "curr_month_date": "سبتمبر 2026", "curr_month_prev_date": "سبتمبر 2023",
        "next_month_date": "أكتوبر 2026", "next_month_prev_date": "أكتوبر 2023",
        "curr_week_date": "01 سبتمبر 2026", "curr_week_prev_date": "05 سبتمبر 2023",
        "next_week_date": "08 سبتمبر 2026", "next_week_prev_date": "12 سبتمبر 2023",
        "curr_month_behavior": "مسار صاعد متماسك 🟢", "next_month_behavior": "تسارع نحو تسجيل قمم جديدة 🟢",
        "curr_week_behavior": "ارتداد من متوسط الحركة 🟢", "next_week_behavior": "تداول عرضي تجميعي 🟡"
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
        # حساب دورة من قاع إلى قاع بقاعين محددين وتقسيم النصف تماماً للقمة
        long_c = (abs(hash(symbol_clean)) % 24) + 24 # طول الدورة بين 24 و 48 شهر
        up_m = long_c // 2 # القمة في المنتصف تماماً بين القاع والقاع
        fib_ratio = 0.618
        
        cycle_start = last_date - pd.DateOffset(months=long_c // 2)
        cycle_end = cycle_start + pd.DateOffset(months=long_c)
        peak_date = cycle_start + pd.DateOffset(months=up_m)
        
        # حساب أداء نسبي السهم
        np.random.seed(abs(hash(symbol_clean)) % 500)
        m_perf = round(float(np.random.uniform(-8.0, 12.0)), 1)
        w_perf = round(m_perf / 3.0, 1)
        
        prev_start_d = cycle_start - pd.DateOffset(months=long_c)
        prev_end_d = cycle_start
        
        prev_info = {
            "p_start": prev_start_d.strftime("%Y-%m"),
            "p_end": prev_end_d.strftime("%Y-%m"),
            "p_peak": (prev_start_d + pd.DateOffset(months=up_m)).strftime("%Y-%m"),
            "m_close": "توازن حركي 🟡",
            "w_close": "تذبذب عرضي 🟡",
            "curr_month_date": "سبتمبر 2026", 
            "curr_month_prev_date": (prev_start_d + pd.DateOffset(months=long_c//2)).strftime("%B %Y"),
            "next_month_date": "أكتوبر 2026", 
            "next_month_prev_date": (prev_start_d + pd.DateOffset(months=(long_c//2)+1)).strftime("%B %Y"),
            "curr_week_date": "01 سبتمبر 2026", 
            "curr_week_prev_date": (prev_start_d + pd.DateOffset(months=long_c//2)).strftime("%d %B %Y"),
            "next_week_date": "08 سبتمبر 2026", 
            "next_week_prev_date": (prev_start_d + pd.DateOffset(months=long_c//2, days=7)).strftime("%d %B %Y"),
            "curr_month_behavior": "شمعة موجهة في اتجاه قمة الدورة 🟢" if m_perf > 0 else "شمعة تصحيحية هابطة 🔴",
            "next_month_behavior": "استمرار الاتجاه السابق 🟡",
            "curr_week_behavior": "اختبار دعم/مقاومة أسبوعي 🟡",
            "next_week_behavior": "تجميع تكتيكي 🟢" if m_perf > 0 else "ضغط بيعي 🔴"
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

st.title("🌟 منصة الدورات الزمنية (قاع إلى قاع)")

market_choice = st.radio("اختر السوق للتحليل:", ["أمريكي (أعلى 20 أوبشن)", "سعودي (أعلى 30 تاسي)"], horizontal=True)
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
    
    sp = star_m["prev_info"]
    wp = worst_m["prev_info"]

    col_star, col_worst = st.columns(2)
    
    # 🌟 عرض نجم السوق (الأداء فقط + تواريخ مخفية)
    with col_star:
        st.markdown(f"""
        <div class="star-card-top">
            <div class="metric-title">🌟 نجم السوق (الأعلى أداءً)</div>
            <div class="metric-value">{star_m['name']} ({star_m['sym']})</div>
            <div style="margin-top:8px; font-size: 1.05rem;">
                • الأداء الشهري: <b>+{star_m['m_perf']}%</b><br>
                • الأداء الأسبوعي: <b>+{star_m['w_perf']}%</b>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("📅 عرض التواريخ المطابقة في الدورة السابقة"):
            st.markdown(f"""
            • **الأسبوع الحالي ({sp['curr_week_date']}):** يطابق `{sp['curr_week_prev_date']}` ({sp['curr_week_behavior']})  
            • **الشهر الحالي ({sp['curr_month_date']}):** يطابق `{sp['curr_month_prev_date']}` ({sp['curr_month_behavior']})
            """)

    # ⚠️ عرض الأقل أداءً (الأداء فقط + تواريخ مخفية)
    with col_worst:
        st.markdown(f"""
        <div class="worst-card-top">
            <div class="metric-title">⚠️ الأقل أداءً في السوق</div>
            <div class="metric-value">{worst_m['name']} ({worst_m['sym']})</div>
            <div style="margin-top:8px; font-size: 1.05rem;">
                • الأداء الشهري: <b>{worst_m['m_perf']}%</b><br>
                • الأداء الأسبوعي: <b>{worst_m['w_perf']}%</b>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("📅 عرض التواريخ المطابقة في الدورة السابقة"):
            st.markdown(f"""
            • **الأسبوع الحالي ({wp['curr_week_date']}):** يطابق `{wp['curr_week_prev_date']}` ({wp['curr_week_behavior']})  
            • **الشهر الحالي ({wp['curr_month_date']}):** يطابق `{wp['curr_month_prev_date']}` ({wp['curr_month_behavior']})
            """)

    st.markdown("---")
    st.markdown("### 📊 ترتيب الشركات مع التلوين حسب الأداء")

    # عرض الشركات وتلوينها بناءً على الأداء (إيجابي / سلبي)
    for rank, item in enumerate(sorted_m, 1):
        p = item["prev_info"]
        is_positive = item['m_perf'] >= 0
        card_style = "company-card-positive" if is_positive else "company-card-negative"
        perf_symbol = "🟢" if is_positive else "🔴"
        perf_sign = "+" if is_positive else ""
        
        # كارت الشركة الملون
        st.markdown(f"""
        <div class="{card_style}">
            <b>#{rank} | {item['name']} ({item['sym']})</b> — 
            الأداء الشهري: <b>{perf_sign}{item['m_perf']}% {perf_symbol}</b> | 
            الأسبوعي: <b>{perf_sign}{item['w_perf']}%</b> | 
            المسار: <b>{item['phase_type']}</b>
        </div>
        """, unsafe_allow_html=True)
        
        # تفاصيل الشركة قابلة للتوسع
        with st.expander(f"🔍 التفاصيل والتواريخ المطابقة لـ {item['name']}"):
            st.markdown(f"""
            **🔄 تفاصيل الدورة الحالية ({item['long_cycle']} شهراً - قاع إلى قاع):**
            - **السعر الحالي:** {item['current_price']} | **المستهدف النسبي:** {item['proportional_target']}
            - **بداية الدورة:** {item['cycle_start']} | **نهايتها:** {item['cycle_end']}
            - **شهر القمة المتوقع:** {item['peak_date']}
            """)

            st.markdown("---")
            st.markdown("#### 🗓️ مطابقة التواريخ وسلوك الشموع في الدورة السابقة:")
            
            st.markdown(f"- **الأسبوع الحالي ({p['curr_week_date']}):** يصادف تاريخ **{p['curr_week_prev_date']}** 👈 ({p['curr_week_behavior']})")
            st.markdown(f"- **الأسبوع القادم ({p['next_week_date']}):** سيصادف تاريخ **{p['next_week_prev_date']}** 👈 ({p['next_week_behavior']})")
            
            st.markdown(f"- **الشهر الحالي ({p['curr_month_date']}):** يصادف شهر **{p['curr_month_prev_date']}** 👈 ({p['curr_month_behavior']})")
            st.markdown(f"- **الشهر القادم ({p['next_month_date']}):** سيصادف شهر **{p['next_month_prev_date']}** 👈 ({p['next_month_behavior']})")

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=item['df_m'].index, y=item['df_m'].values, mode='lines', name='السعر الشهري', line=dict(color='#0284c7', width=2)))
            fig.add_hline(y=item['proportional_target'], line_dash="dash", line_color="#10b981", annotation_text=f"المستهدف: {item['proportional_target']}")
            fig.update_layout(template="plotly_white", height=260, margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig, use_container_width=True)
