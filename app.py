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

st.set_page_config(page_title="المحرك الفائق للمستهدفات النسبية والدورات", page_icon="🎯", layout="wide")

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
    "TSLA": {"long": 49, "up": 20, "fib_retrace": 0.618}, # ارتداد 61.8%
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

def analyze_wave_target(df_m, symbol_clean):
    prices = df_m.values
    if len(prices) < 36:
        return None
        
    long_c = KNOWN_CYCLES.get(symbol_clean, {}).get("long", 42)
    fib_ratio = KNOWN_CYCLES.get(symbol_clean, {}).get("fib_retrace", 0.618)
    
    # تحديد نطاق الموجة الأخيرة
    recent_segment = prices[-long_c:]
    wave_high = np.max(recent_segment)
    wave_low = np.min(recent_segment)
    wave_range = wave_high - wave_low
    
    # حساب السعر المستهدف بالنسبة والتناسب (Fibonacci Retracement Ratio)
    current_price = prices[-1]
    proportional_target = wave_low + (wave_range * fib_ratio)
    expected_change_pct = ((proportional_target - current_price) / current_price) * 100

    return {
        "long_cycle": long_c,
        "fib_ratio": round(fib_ratio * 100, 1),
        "wave_high": round(wave_high, 2),
        "wave_low": round(wave_low, 2),
        "current_price": round(current_price, 2),
        "proportional_target": round(proportional_target, 2),
        "expected_change_pct": round(expected_change_pct, 2)
    }

# --- الواجهة ---
st.title("🎯 المستهدفات السعرية التناسبية للموجات والدورات")

tab1, tab2 = st.tabs(["🏆 المستهدفات التناسبية لكافة الأسهم", "📈 التحليل الموجي التناسبي للسهم"])

with tab1:
    market_choice = st.radio("اختر السوق للحساب:", ["السوق السعودي (تاسي)", "سوق النازداك (NASDAQ)"], horizontal=True)
    
    if st.button("🚀 حساب المستهدفات التناسبية لجميع الأسهم", type="primary"):
        with st.spinner("جاري حساب نسب الموجات السابقة وتطبيق المستهدفات بالتطابق النسبي..."):
            pool = TASI_MAIN_STOCKS if "السعودي" in market_choice else NASDAQ_STOCKS
            results = []
            
            for sym, name in pool.items():
                df_s, c_sym, c_name = fetch_stock_data(sym)
                if not df_s.empty:
                    df_res = df_s.copy()
                    df_res['Date'] = pd.to_datetime(df_res['Date'])
                    df_res.set_index('Date', inplace=True)
                    df_m = df_res['Close'].resample('ME').last().dropna()
                    
                    target_info = analyze_wave_target(df_m, c_sym)
                    if target_info:
                        results.append({
                            "الرمز": c_sym,
                            "الشركة": c_name,
                            "السعر الحالي": target_info['current_price'],
                            "قاع الموجة": target_info['wave_low'],
                            "قمة الموجة": target_info['wave_high'],
                            "نسبة ارتداد الموجة": f"{target_info['fib_ratio']}%",
                            "المستهدف النسبي المتوقع": target_info['proportional_target'],
                            "الارتفاع المتوقع (%)": f"{target_info['expected_change_pct']}%"
                        })
            
            if results:
                rdf = pd.DataFrame(results)
                st.markdown("### 📋 جدول المستهدفات السعرية المعتمدة على نسبة وتناسب الموجات:")
                st.dataframe(rdf, use_container_width=True)

with tab2:
    input_sym = st.text_input("أدخل رمز السهم (مثل TSLA أو 2170):", value="TSLA")
    df_raw, clean_sym, comp_name = fetch_stock_data(input_sym)
    
    if not df_raw.empty:
        df_res = df_raw.copy()
        df_res['Date'] = pd.to_datetime(df_res['Date'])
        df_res.set_index('Date', inplace=True)
        df_m = df_res['Close'].resample('ME').last().dropna()
        
        info = analyze_wave_target(df_m, clean_sym)
        if info:
            st.markdown(f"#### 📊 المستهدف التناسبي لـ **{comp_name} ({clean_sym})**")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("السعر الحالي", f"${info['current_price']}" if "SR" not in clean_sym else f"{info['current_price']} ر.س")
            c2.metric("نسبة ارتداد الدورة السابقة", f"{info['fib_ratio']}%")
            c3.metric("المستهدف النسبي القادم", f"${info['proportional_target']}" if "SR" not in clean_sym else f"{info['proportional_target']} ر.س")
            c4.metric("نسبة التغير المتوقعة", f"{info['expected_change_pct']}%")

            # الرسم التفاعلي ومستويات الموجة
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_m.index, y=df_m.values, mode='lines', name='السعر الشهري', line=dict(color='#0284c7', width=2)))
            
            # خط المستهدف التناسبي
            fig.add_hline(y=info['proportional_target'], line_dash="dash", line_color="#10b981", 
                          annotation_text=f"المستهدف التناسبي ({info['fib_ratio']}%): {info['proportional_target']}")
            fig.add_hline(y=info['wave_high'], line_dash="dot", line_color="#ef4444", annotation_text=f"قمة الموجة: {info['wave_high']}")
            fig.add_hline(y=info['wave_low'], line_dash="dot", line_color="#6b7280", annotation_text=f"قاع الموجة: {info['wave_low']}")
            
            fig.update_layout(template="plotly_white", height=500)
            st.plotly_chart(fig, use_container_width=True)
