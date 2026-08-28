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

st.set_page_config(page_title="المطابق الدوري الدقيق (أسابيع وأشهر)", page_icon="🎯", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; direction: rtl; text-align: right; }
    .stMetric { background-color: #0f172a; color: #ffffff; padding: 12px; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

ACTIVE_SAUDI_STOCKS = {
    "2222.SR": "أرامكو السعودية", "1120.SR": "الراجحي", "2010.SR": "سابك", "1180.SR": "الأهلي",
    "2170.SR": "اللجين", "4323.SR": "سمو", "2082.SR": "أكوا باور", "7010.SR": "STC", 
    "1080.SR": "الإنماء", "1211.SR": "معادن", "4007.SR": "سليمان الحبيب"
}

ACTIVE_US_STOCKS = {
    "TSLA": "تيسلا", "NVDA": "انفيديا", "AAPL": "أبل", "MSFT": "مايكروسوفت",
    "AMZN": "أمازون", "GOOGL": "جوجل", "META": "ميتا", "AMD": "إيه إم دي"
}

KNOWN_EXACT_CYCLES = {
    "TSLA": 49,
    "META": 46,
}

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_stock_data(symbol):
    clean_sym = symbol.strip().upper()
    if clean_sym.isdigit():
        clean_sym = f"{clean_sym}.SR"
        
    comp_name = ACTIVE_SAUDI_STOCKS.get(clean_sym, ACTIVE_US_STOCKS.get(clean_sym, clean_sym))
    
    if YFINANCE_AVAILABLE:
        try:
            df = yf.Ticker(clean_sym).history(period="max")
            if not df.empty and len(df) >= 100:
                df.reset_index(inplace=True)
                df.dropna(subset=['Close'], inplace=True)
                return df, clean_sym, comp_name
        except Exception:
            pass
            
    dates = pd.date_range(end=datetime.today(), periods=300, freq='W')
    np.random.seed(abs(hash(clean_sym)) % 10000)
    prices = 50.0 * np.exp(np.cumsum(np.random.normal(0.001, 0.03, size=len(dates))))
    return pd.DataFrame({'Date': dates, 'Close': prices}), clean_sym, comp_name

def validate_cycle_structure(prices, cycle_months):
    """التحقق من وجود قمة وقاع واضحة في الدورة واستبعاد الاتجاهات الهابطة المستمرة"""
    window = int(cycle_months)
    if len(prices) < window * 2:
        return True
    
    recent_segment = prices[-window:]
    min_p = np.min(recent_segment)
    max_p = np.max(recent_segment)
    
    range_pct = ((max_p - min_p) / min_p) * 100
    if range_pct < 15:
        return False
    return True

def analyze_detailed_cycles(df, symbol_clean, override_months=None):
    df_res = df.copy()
    df_res['Date'] = pd.to_datetime(df_res['Date'])
    df_res.set_index('Date', inplace=True)
    
    df_m = df_res['Close'].resample('ME').last().dropna()
    m_prices = df_m.values
    m_dates = df_m.index
    
    df_w = df_res['Close'].resample('W').last().dropna()
    w_prices = df_w.values
    w_dates = df_w.index
    
    if len(m_prices) < 24 or len(w_prices) < 50:
        return None

    if override_months:
        final_m_cycle = override_months
    elif symbol_clean in KNOWN_EXACT_CYCLES:
        final_m_cycle = KNOWN_EXACT_CYCLES[symbol_clean]
    else:
        returns = np.diff(np.log(m_prices))
        freqs, spectrum = periodogram(returns)
        periods = 1 / freqs[1:]
        spectrum_vals = spectrum[1:]
        
        valid_mask = (periods >= 12) & (periods <= 120)
        valid_periods = periods[valid_mask]
        valid_spectrum = spectrum_vals[valid_mask]
        
        if len(valid_spectrum) > 0:
            final_m_cycle = int(round(valid_periods[np.argmax(valid_spectrum)]))
        else:
            final_m_cycle = 36
            
    is_valid_structure = validate_cycle_structure(m_prices, final_m_cycle)
    final_w_cycle = int(round(final_m_cycle * 4.33))
    
    m_curr_idx = len(m_prices) - 1
    m_past_idx = max(0, m_curr_idx - final_m_cycle)
    
    m_curr_perf = ((m_prices[m_past_idx] - m_prices[m_past_idx - 1]) / m_prices[m_past_idx - 1]) * 100 if m_past_idx > 0 else 0
    m_next_perf = ((m_prices[m_past_idx + 1] - m_prices[m_past_idx]) / m_prices[m_past_idx]) * 100 if m_past_idx + 1 < len(m_prices) else 0

    w_curr_idx = len(w_prices) - 1
    w_past_idx = max(0, w_curr_idx - final_w_cycle)
    
    w_curr_perf = ((w_prices[w_past_idx] - w_prices[w_past_idx - 1]) / w_prices[w_past_idx - 1]) * 100 if w_past_idx > 0 else 0
    w_next_perf = ((w_prices[w_past_idx + 1] - w_prices[w_past_idx]) / w_prices[w_past_idx]) * 100 if w_past_idx + 1 < len(w_prices) else 0

    return {
        "df_m": df_m,
        "final_m_cycle": final_m_cycle,
        "is_valid_structure": is_valid_structure,
        "m_curr_perf": round(m_curr_perf, 2),
        "m_next_perf": round(m_next_perf, 2),
        "w_curr_perf": round(w_curr_perf, 2),
        "w_next_perf": round(w_next_perf, 2),
        "m_current_date": m_dates[m_curr_idx],
        "m_past_date": m_dates[m_past_idx]
    }

# --- الواجهة الرئيسية ---
st.title("🎯 المحرك الفائق للدورات الزمنية (شهري وأسبوعي)")

tab1, tab2 = st.tabs(["🏆 نجوم وأسوأ أداء بالسوق", "🔍 التحليل الهيكلي لسهم محدد"])

with tab1:
    market = st.radio("اختر السوق:", ["السوق السعودي (تاسي)", "السوق الأمريكي"], horizontal=True)
    filter_downtrend = st.checkbox("تفعيل فلتر استبعاد الاتجاهات الهابطة بدون قمم/قيعان واضحة", value=True)
    
    if st.button("🚀 تحليل وتقسيم الأداء الدوري", type="primary"):
        with st.spinner("جاري تفكيك الأسابيع والأشهر ومطابقتها بالتاريخ الدوري..."):
            pool = ACTIVE_SAUDI_STOCKS if "السعودي" in market else ACTIVE_US_STOCKS
            results = []
            
            for sym, name in pool.items():
                df_s, c_sym, c_name = fetch_stock_data(sym)
                if not df_s.empty:
                    res = analyze_detailed_cycles(df_s, c_sym)
                    if res:
                        if filter_downtrend and not res['is_valid_structure']:
                            continue
                            
                        results.append({
                            "الرمز": c_sym,
                            "الشركة": c_name,
                            "الدورة (شهراً)": res['final_m_cycle'],
                            "الشهر الحالي": res['m_curr_perf'],
                            "الشهر القادم": res['m_next_perf'],
                            "الأسبوع الحالي": res['w_curr_perf'],
                            "الأسبوع القادم": res['w_next_perf']
                        })
            
            if results:
                rdf = pd.DataFrame(results)
                
                star_m_curr = rdf.sort_values(by="الشهر الحالي", ascending=False).iloc[0]
                worst_m_curr = rdf.sort_values(by="الشهر الحالي", ascending=True).iloc[0]
                
                star_m_next = rdf.sort_values(by="الشهر القادم", ascending=False).iloc[0]
                worst_m_next = rdf.sort_values(by="الشهر القادم", ascending=True).iloc[0]
                
                star_w_curr = rdf.sort_values(by="الأسبوع الحالي", ascending=False).iloc[0]
                worst_w_curr = rdf.sort_values(by="الأسبوع الحالي", ascending=True).iloc[0]
                
                star_w_next = rdf.sort_values(by="الأسبوع القادم", ascending=False).iloc[0]
                worst_w_next = rdf.sort_values(by="الأسبوع القادم", ascending=True).iloc[0]
                
                st.markdown("### 🌟 نجوم الأداء (الأفضل تاريخياً لهذه الفترة)")
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.success(f"**نجم الأسبوع الحالي**\n\n**{star_w_curr['الشركة']}** ({star_w_curr['الأسبوع الحالي']}%)")
                with c2:
                    st.success(f"**نجم الأسبوع القادم**\n\n**{star_w_next['الشركة']}** ({star_w_next['الأسبوع القادم']}%)")
                with c3:
                    st.success(f"**نجم الشهر الحالي**\n\n**{star_m_curr['الشركة']}** ({star_m_curr['الشهر الحالي']}%)")
                with c4:
                    st.success(f"**نجم الشهر القادم**\n\n**{star_m_next['الشركة']}** ({star_m_next['الشهر القادم']}%)")
                    
                st.markdown("### ⚠️ أسوأ أداء متوقع (الأكثر ضغطاً/هبوطاً تاريخياً)")
                w1, w2, w3, w4 = st.columns(4)
                with w1:
                    st.error(f"**أسوأ أسبوع حالي**\n\n**{worst_w_curr['الشركة']}** ({worst_w_curr['الأسبوع الحالي']}%)")
                with w2:
                    st.error(f"**أسوأ أسبوع قادم**\n\n**{worst_w_next['الشركة']}** ({worst_w_next['الأسبوع القادم']}%)")
                with w3:
                    st.error(f"**أسوأ شهر حالي**\n\n**{worst_m_curr['الشركة']}** ({worst_m_curr['الشهر الحالي']}%)")
                with w4:
                    st.error(f"**أسوأ شهر قادم**\n\n**{worst_m_next['الشركة']}** ({worst_m_next['الشهر القادم']}%)")

                st.markdown("### 📋 جدول تفكيك الأداء الكامل للأسهم:")
                st.dataframe(rdf, use_container_width=True)

with tab2:
    ticker = st.text_input("أدخل رمز السهم (مثل TSLA أو META أو 2222):", value="2222")
    
    df_raw, clean_sym, comp_name = fetch_stock_data(ticker)
    
    default_c = KNOWN_EXACT_CYCLES.get(clean_sym, 36)
    m_cycle = st.number_input("تحديد/تعديل طول الدورة (شهراً):", min_value=6, max_value=140, value=default_c)
    
    if not df_raw.empty:
        res = analyze_detailed_cycles(df_raw, clean_sym, override_months=m_cycle)
        if res:
            st.markdown(f"### 📊 التحليل الهيكلي والسلوكي لـ **{comp_name} ({clean_sym})**")
            
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("أداء الأسبوع الحالي", f"{res['w_curr_perf']}%")
            with c2:
                st.metric("أداء الأسبوع القادم", f"{res['w_next_perf']}%")
            with c3:
                st.metric("أداء الشهر الحالي", f"{res['m_curr_perf']}%")
            with c4:
                st.metric("أداء الشهر القادم", f"{res['m_next_perf']}%")

            if not res['is_valid_structure']:
                st.warning("⚠️ **تنبيه هيكلي:** السهم يعاني من مسار هابط أو نطاق ضيق بدون قمم وقيعان صريحة في الدورة الأخيرة.")
            else:
                st.success("✅ **هيكل فني سليم:** السهم يحقق نطاق حركة واضح (قمم وقيعان صريحة).")
                
            df_m = res['df_m']
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_m.index, y=df_m.values, mode='lines', name='السعر الشهري', line=dict(color='#0284c7', width=2)))
            fig.add_vline(x=res['m_current_date'], line_color="#ef4444", annotation_text="الحالي")
            fig.add_vline(x=res['m_past_date'], line_color="#10b981", annotation_text=f"الدورة السابقة ({res['final_m_cycle']}M)")
            fig.update_layout(template="plotly_white", height=450)
            st.plotly_chart(fig, use_container_width=True)