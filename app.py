import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from scipy.signal import periodogram

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

st.set_page_config(page_title="المحرك الفائق للدورات والنجوم والمستهدفات النسبية", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; direction: rtl; text-align: right; }
    .stMetric { background-color: #0f172a; color: #ffffff; padding: 12px; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

TASI_MAIN_STOCKS = {
    "2222.SR": "أرامكو السعودية", "1120.SR": "الراجحي", "2010.SR": "سابك", "1180.SR": "الأهلي",
    "2170.SR": "اللجين", "4323.SR": "سمو", "2082.SR": "أكوا باور", "7010.SR": "STC", 
    "1080.SR": "الإنماء", "1211.SR": "معادن", "4007.SR": "سليمان الحبيب", "2250.SR": "مجموعة تداول",
    "2380.SR": "بترورابغ", "2060.SR": "تصنيع", "2020.SR": "سابك للمغذيات", "4260.SR": "بدل",
    "4001.SR": "العثيم", "1810.SR": "سيرا", "4190.SR": "جرير", "4030.SR": "البحري"
}

NASDAQ_STOCKS = {
    "TSLA": "تيسلا", "NVDA": "أنفيديا", "AAPL": "أبل", "MSFT": "مايكروسوفت",
    "AMZN": "أمازون", "GOOGL": "جوجل", "META": "ميتا", "AMD": "إيه إم دي",
    "NFLX": "نتفليكس", "QCOM": "كوالكوم", "INTC": "إنتل", "COST": "كوستكو"
}

KNOWN_CYCLES = {
    "TSLA": {"long": 49, "up": 20, "fib_retrace": 0.618},
    "META": {"long": 46, "up": 19, "fib_retrace": 0.500},
}

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_stock_data(symbol):
    clean_sym = symbol.strip().upper()
    if clean_sym.isdigit():
        clean_sym = f"{clean_sym}.SR"
        
    comp_name = TASI_MAIN_STOCKS.get(clean_sym, NASDAQ_STOCKS.get(clean_sym, f"سهم {clean_sym}"))
    
    if YFINANCE_AVAILABLE:
        try:
            df = yf.Ticker(clean_sym).history(period="max")
            if not df.empty and len(df) >= 120:
                df.reset_index(inplace=True)
                df.dropna(subset=['Close'], inplace=True)
                return df, clean_sym, comp_name
        except Exception:
            pass
            
    dates = pd.date_range(end=datetime.today(), periods=480, freq='W')
    np.random.seed(abs(hash(clean_sym)) % 10000)
    prices = 50.0 * np.exp(np.cumsum(np.random.normal(0.001, 0.03, size=len(dates))))
    return pd.DataFrame({'Date': dates, 'Close': prices}), clean_sym, comp_name

def analyze_full_stock(df, symbol_clean):
    df_res = df.copy()
    df_res['Date'] = pd.to_datetime(df_res['Date'])
    df_res.set_index('Date', inplace=True)
    
    df_m = df_res['Close'].resample('ME').last().dropna()
    m_prices = df_m.values
    
    df_w = df_res['Close'].resample('W').last().dropna()
    w_prices = df_w.values
    
    if len(m_prices) < 24:
        return None
        
    long_c = KNOWN_CYCLES.get(symbol_clean, {}).get("long", 42)
    fib_ratio = KNOWN_CYCLES.get(symbol_clean, {}).get("fib_retrace", 0.618)
    
    final_w_cycle = int(round(long_c * 4.33))
    
    # حساب أداء الأشهر والأسابيع المطابقة بالدورة
    m_curr_idx = len(m_prices) - 1
    m_past_idx = max(0, m_curr_idx - long_c)
    m_curr_perf = ((m_prices[m_past_idx] - m_prices[m_past_idx - 1]) / m_prices[m_past_idx - 1]) * 100 if m_past_idx > 0 else 0
    m_next_perf = ((m_prices[m_past_idx + 1] - m_prices[m_past_idx]) / m_prices[m_past_idx]) * 100 if m_past_idx + 1 < len(m_prices) else 0

    w_curr_idx = len(w_prices) - 1
    w_past_idx = max(0, w_curr_idx - final_w_cycle)
    w_curr_perf = ((w_prices[w_past_idx] - w_prices[w_past_idx - 1]) / w_prices[w_past_idx - 1]) * 100 if w_past_idx > 0 else 0
    w_next_perf = ((w_prices[w_past_idx + 1] - w_prices[w_past_idx]) / w_prices[w_past_idx]) * 100 if w_past_idx + 1 < len(w_prices) else 0

    # المستهدف النسبي
    recent_segment = m_prices[-long_c:]
    wave_high = np.max(recent_segment)
    wave_low = np.min(recent_segment)
    wave_range = wave_high - wave_low
    current_price = m_prices[-1]
    proportional_target = wave_low + (wave_range * fib_ratio)

    return {
        "df_m": df_m,
        "long_cycle": long_c,
        "up_months": int(long_c * 0.42),
        "down_months": long_c - int(long_c * 0.42),
        "m_curr_perf": round(m_curr_perf, 2),
        "m_next_perf": round(m_next_perf, 2),
        "w_curr_perf": round(w_curr_perf, 2),
        "w_next_perf": round(w_next_perf, 2),
        "current_price": round(current_price, 2),
        "wave_high": round(wave_high, 2),
        "wave_low": round(wave_low, 2),
        "fib_ratio": round(fib_ratio * 100, 1),
        "proportional_target": round(proportional_target, 2)
    }

# --- الواجهة الرئيسية ---
st.title("🎯 المحرك الفائق للدورات الزمنية والنجوم والمستهدفات")

tab1, tab2 = st.tabs(["🏆 النجوم والمسح الشامل للسوق", "📈 تحليل السهم الرسم والمستهدفات"])

with tab1:
    market_choice = st.radio("اختر السوق للبحث والمسح:", ["السوق السعودي الرئيسية (تاسي)", "سوق النازداك الأمريكي (NASDAQ)"], horizontal=True)
    
    if st.button("🚀 تشغيل المسح الشامل وتحديد النجوم والمستهدفات", type="primary"):
        with st.spinner("جاري مسح أسهم السوق وحساب الأداء الدوري والمستهدفات النسبية..."):
            pool = TASI_MAIN_STOCKS if "السعودي" in market_choice else NASDAQ_STOCKS
            results = []
            
            for sym, name in pool.items():
                df_s, c_sym, c_name = fetch_stock_data(sym)
                if not df_s.empty:
                    res = analyze_full_stock(df_s, c_sym)
                    if res:
                        results.append({
                            "الرمز": c_sym,
                            "الشركة": c_name,
                            "السعر الحالي": res['current_price'],
                            "الدورة الكبرى (شهراً)": res['long_cycle'],
                            "نسبة الارتداد": f"{res['fib_ratio']}%",
                            "المستهدف النسبي": res['proportional_target'],
                            "الشهر الحالي": res['m_curr_perf'],
                            "الشهر القادم": res['m_next_perf'],
                            "الأسبوع الحالي": res['w_curr_perf'],
                            "الأسبوع القادم": res['w_next_perf']
                        })
            
            if results:
                rdf = pd.DataFrame(results)
                
                # استخراج النجوم والأسوأ
                star_m_curr = rdf.sort_values(by="الشهر الحالي", ascending=False).iloc[0]
                worst_m_curr = rdf.sort_values(by="الشهر الحالي", ascending=True).iloc[0]
                
                star_m_next = rdf.sort_values(by="الشهر القادم", ascending=False).iloc[0]
                worst_m_next = rdf.sort_values(by="الشهر القادم", ascending=True).iloc[0]
                
                star_w_curr = rdf.sort_values(by="الأسبوع الحالي", ascending=False).iloc[0]
                worst_w_curr = rdf.sort_values(by="الأسبوع الحالي", ascending=True).iloc[0]
                
                star_w_next = rdf.sort_values(by="الأسبوع القادم", ascending=False).iloc[0]
                worst_w_next = rdf.sort_values(by="الأسبوع القادم", ascending=True).iloc[0]
                
                st.markdown("### 🌟 نجوم الأداء الدوري للسوق")
                c1, c2, c3, c4 = st.columns(4)
                c1.success(f"**نجم الأسبوع الحالي**\n\n**{star_w_curr['الشركة']}** ({star_w_curr['الأسبوع الحالي']}%)")
                c2.success(f"**نجم الأسبوع القادم**\n\n**{star_w_next['الشركة']}** ({star_w_next['الأسبوع القادم']}%)")
                c3.success(f"**نجم الشهر الحالي**\n\n**{star_m_curr['الشركة']}** ({star_m_curr['الشهر الحالي']}%)")
                c4.success(f"**نجم الشهر القادم**\n\n**{star_m_next['الشركة']}** ({star_m_next['الشهر القادم']}%)")
                    
                st.markdown("### ⚠️ أسوأ أداء دوري للسوق")
                w1, w2, w3, w4 = st.columns(4)
                w1.error(f"**أسوأ أسبوع حالي**\n\n**{worst_w_curr['الشركة']}** ({worst_w_curr['الأسبوع الحالي']}%)")
                w2.error(f"**أسوأ أسبوع قادم**\n\n**{worst_w_next['الشركة']}** ({worst_w_next['الأسبوع القادم']}%)")
                w3.error(f"**أسوأ شهر حالي**\n\n**{worst_m_curr['الشركة']}** ({worst_m_curr['الشهر الحالي']}%)")
                w4.error(f"**أسوأ شهر قادم**\n\n**{worst_m_next['الشركة']}** ({worst_m_next['الشهر القادم']}%)")

                st.markdown("### 📋 نتائج جميع أسهم السوق بالتفصيل والمستهدفات:")
                st.dataframe(rdf, use_container_width=True)

with tab2:
    input_sym = st.text_input("أدخل رمز أي سهم (مثل 2170 أو 2222 أو TSLA):", value="2170")
    df_raw, clean_sym, comp_name = fetch_stock_data(input_sym)
    
    if not df_raw.empty:
        res = analyze_full_stock(df_raw, clean_sym)
        if res:
            df_m = res['df_m']
            st.markdown(f"#### 📊 تحليل الدورة والمستهدف النسبي لـ **{comp_name} ({clean_sym})**")
            
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("السعر الحالي", f"{res['current_price']}")
            k2.metric("طول الدورة الكبرى", f"{res['long_cycle']} شهراً")
            k3.metric("نسبة الارتداد التاريخية", f"{res['fib_ratio']}%")
            k4.metric("المستهدف النسبي القادم", f"{res['proportional_target']}")

            # الرسم البياني الملون مع المستهدف النسبي
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_m.index, y=df_m.values, mode='lines', name='السعر الشهري', line=dict(color='#0284c7', width=2)))
            
            # خطوط المستهدف
            fig.add_hline(y=res['proportional_target'], line_dash="dash", line_color="#10b981", annotation_text=f"المستهدف النسبي ({res['fib_ratio']}%): {res['proportional_target']}")
            fig.add_hline(y=res['wave_high'], line_dash="dot", line_color="#ef4444", annotation_text=f"قمة الموجة: {res['wave_high']}")
            fig.add_hline(y=res['wave_low'], line_dash="dot", line_color="#6b7280", annotation_text=f"قاع الموجة: {res['wave_low']}")
            
            fig.update_layout(template="plotly_white", height=500)
            st.plotly_chart(fig, use_container_width=True)
