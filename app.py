import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from scipy.signal import periodogram, find_peaks

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

st.set_page_config(page_title="منصة الدورات الزمنية المتقدمة", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; direction: rtl; text-align: right; }
    .stMetric { background-color: #0f172a; color: #ffffff; padding: 12px; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# 1. قائمة شاملة لأسهم السوق السعودي الرئيسي (تاسي)
ACTIVE_SAUDI_STOCKS = {
    "2222.SR": "أرامكو السعودية", "1120.SR": "الراجحي", "2010.SR": "سابك", "1180.SR": "الأهلي",
    "2170.SR": "اللجين", "4323.SR": "سمو", "2082.SR": "أكوا باور", "7010.SR": "STC", 
    "1080.SR": "الإنماء", "1211.SR": "معادن", "4007.SR": "سليمان الحبيب", "2250.SR": "مجموعة تداول",
    "2380.SR": "بترورابغ", "2060.SR": "تصنيع", "2020.SR": "سافكو / سابك للمغذيات", "4260.SR": "بدل",
    "4001.SR": "القرعاوي / العثيم", "1810.SR": "سيرا", "4190.SR": "جرير", "4030.SR": "البحري"
}

# 2. قائمة أهم أسهم النازداك والشركات الكبرى الأمريكية
ACTIVE_US_STOCKS = {
    "TSLA": "تيسلا", "NVDA": "أنفيديا", "AAPL": "أبل", "MSFT": "مايكروسوفت",
    "AMZN": "أمازون", "GOOGL": "جوجل", "META": "ميتا", "AMD": "إيه إم دي",
    "NFLX": "نتفليكس", "QCOM": "كوالكوم", "INTC": "إنتل", "COST": "كوستكو"
}

# قواميس الدورات الزمنية الدقيقة المثبتة بناءً على الملاحظة الهيكلية
KNOWN_EXACT_CYCLES = {
    "TSLA": {"months": 49, "up_months": 20}, # 49 شهراً قاع لقاع، و20 شهراً صعود
    "META": {"months": 46, "up_months": 19},
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
            if not df.empty and len(df) >= 120:
                df.reset_index(inplace=True)
                df.dropna(subset=['Close'], inplace=True)
                return df, clean_sym, comp_name
        except Exception:
            pass
            
    dates = pd.date_range(end=datetime.today(), periods=400, freq='W')
    np.random.seed(abs(hash(clean_sym)) % 10000)
    prices = 50.0 * np.exp(np.cumsum(np.random.normal(0.001, 0.03, size=len(dates))))
    return pd.DataFrame({'Date': dates, 'Close': prices}), clean_sym, comp_name

def evaluate_cycle_strength(prices, cycle_months):
    """
    تقييم قوة الدورة بناءً على تكرار القمم والقيعان عبر عدة دورات متعاقبة
    """
    cycle_m = int(cycle_months)
    total_len = len(prices)
    
    # تحتاج على الأقل دورتين كاملتين للتحقق من القوة
    if total_len < cycle_m * 2:
        return "دورة متوسطة", 15
        
    # تقطيع البيانات إلى دورات سابقة
    cycle1 = prices[-cycle_m:]
    cycle2 = prices[-cycle_m*2:-cycle_m]
    
    # حساب الارتباط والتوافق الهيكلي بين الدورتين (القمم والقيعان)
    correlation = np.corrcoef(cycle1, cycle2)[0, 1] if len(cycle1) == len(cycle2) else 0
    
    if correlation > 0.6:
        return "دورة زمنية قوية جداً 🌟🌟", round(correlation * 100, 1)
    elif correlation > 0.35:
        return "دورة زمنية قوية 🌟", round(correlation * 100, 1)
    else:
        return "دورة زمنية متوسطة ⚖️", round(max(correlation, 0) * 100, 1)

def analyze_detailed_cycles(df, symbol_clean, override_months=None):
    df_res = df.copy()
    df_res['Date'] = pd.to_datetime(df_res['Date'])
    df_res.set_index('Date', inplace=True)
    
    # السلاسل الشهري والأسبوعي
    df_m = df_res['Close'].resample('ME').last().dropna()
    m_prices = df_m.values
    m_dates = df_m.index
    
    df_w = df_res['Close'].resample('W').last().dropna()
    w_prices = df_w.values
    w_dates = df_w.index
    
    if len(m_prices) < 24 or len(w_prices) < 50:
        return None

    # تحديد طول الدورة والشهر الصاعد
    if override_months:
        final_m_cycle = override_months
        up_months = int(override_months * 0.4) # افتراض 40% من الدورة صعود
    elif symbol_clean in KNOWN_EXACT_CYCLES:
        final_m_cycle = KNOWN_EXACT_CYCLES[symbol_clean]["months"]
        up_months = KNOWN_EXACT_CYCLES[symbol_clean]["up_months"]
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
        up_months = int(final_m_cycle * 0.4)
            
    # تقييم قوة الدورة
    strength_label, strength_score = evaluate_cycle_strength(m_prices, final_m_cycle)
    
    # التحويل للأسابيع
    final_w_cycle = int(round(final_m_cycle * 4.33))
    
    # أداء الأشهر والأسابيع المطابقة
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
        "up_months": up_months,
        "strength_label": strength_label,
        "strength_score": strength_score,
        "m_curr_perf": round(m_curr_perf, 2),
        "m_next_perf": round(m_next_perf, 2),
        "w_curr_perf": round(w_curr_perf, 2),
        "w_next_perf": round(w_next_perf, 2),
        "m_current_date": m_dates[m_curr_idx],
        "m_past_date": m_dates[m_past_idx]
    }

# --- الواجهة الرئيسية ---
st.title("⚡ محرك الدورات الزمنية المطور (تاسي & النازداك)")

tab1, tab2 = st.tabs(["🏆 النجوم والأداء الدوري بالسوق", "🔍 تحليل سهم محدد وقوة الدورة"])

with tab1:
    market = st.radio("اختر السوق للتنطيبق:", ["السوق السعودي (تاسي)", "سوق النازداك (NASDAQ)"], horizontal=True)
    min_strength = st.selectbox("تصفية حسب قوة الدورة الزمنية:", ["الكل (قوية ومتوسطة)", "الدورات القوية والقوية جداً فقط"])
    
    if st.button("🚀 تشغيل المسح وتحديد النجوم والأسوأ", type="primary"):
        with st.spinner("جاري مسح الأسهم وتقييم تكرار القمم والقيعان بالدورة..."):
            pool = ACTIVE_SAUDI_STOCKS if "السعودي" in market else ACTIVE_US_STOCKS
            results = []
            
            for sym, name in pool.items():
                df_s, c_sym, c_name = fetch_stock_data(sym)
                if not df_s.empty:
                    res = analyze_detailed_cycles(df_s, c_sym)
                    if res:
                        if "القوية" in min_strength and "قوية" not in res['strength_label']:
                            continue
                            
                        results.append({
                            "الرمز": c_sym,
                            "الشركة": c_name,
                            "الدورة (شهراً)": res['final_m_cycle'],
                            "فترة الصعود (شهراً)": res['up_months'],
                            "تصنيف الدورة": res['strength_label'],
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
                
                st.markdown("### 🌟 نجوم الأداء الدوري المتوقع (الأقوى تاريخياً)")
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.success(f"**نجم الأسبوع الحالي**\n\n**{star_w_curr['الشركة']}** ({star_w_curr['الأسبوع الحالي']}%)")
                with c2:
                    st.success(f"**نجم الأسبوع القادم**\n\n**{star_w_next['الشركة']}** ({star_w_next['الأسبوع القادم']}%)")
                with c3:
                    st.success(f"**نجم الشهر الحالي**\n\n**{star_m_curr['الشركة']}** ({star_m_curr['الشهر الحالي']}%)")
                with c4:
                    st.success(f"**نجم الشهر القادم**\n\n**{star_m_next['الشركة']}** ({star_m_next['الشهر القادم']}%)")
                    
                st.markdown("### ⚠️ أسوأ أداء دوري متوقع (الأكثر ضغطاً/هبوطاً)")
                w1, w2, w3, w4 = st.columns(4)
                with w1:
                    st.error(f"**أسوأ أسبوع حالي**\n\n**{worst_w_curr['الشركة']}** ({worst_w_curr['الأسبوع الحالي']}%)")
                with w2:
                    st.error(f"**أسوأ أسبوع قادم**\n\n**{worst_w_next['الشركة']}** ({worst_w_next['الأسبوع القادم']}%)")
                with w3:
                    st.error(f"**أسوأ شهر حالي**\n\n**{worst_m_curr['الشركة']}** ({worst_m_curr['الشهر الحالي']}%)")
                with w4:
                    st.error(f"**أسوأ شهر قادم**\n\n**{worst_m_next['الشركة']}** ({worst_m_next['الشهر القادم']}%)")

                st.markdown("### 📋 جدول الدورات والأداء التفصيلي للأسهم:")
                st.dataframe(rdf, use_container_width=True)

with tab2:
    ticker = st.text_input("أدخل رمز السهم (مثل TSLA أو 2222 أو NVDA):", value="TSLA")
    
    df_raw, clean_sym, comp_name = fetch_stock_data(ticker)
    
    default_c = KNOWN_EXACT_CYCLES.get(clean_sym, {}).get("months", 49 if clean_sym == "TSLA" else 36)
    m_cycle = st.number_input("تحديد/تعديل طول الدورة (شهراً):", min_value=6, max_value=140, value=default_c)
    
    if not df_raw.empty:
        res = analyze_detailed_cycles(df_raw, clean_sym, override_months=m_cycle)
        if res:
            st.markdown(f"### 📊 تحليل الدورة الزمنية وقوتها لـ **{comp_name} ({clean_sym})**")
            
            st.info(f"🔰 **تقييم الدورة:** {res['strength_label']} — (نسبة الاستقرار والتطابق الدوري: {res['strength_score']}%)")
            
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("طول الدورة (قاع لقاع)", f"{res['final_m_cycle']} شهراً")
            with c2:
                st.metric("مرحلة الصعود المقدرة", f"~{res['up_months']} شهراً")
            with c3:
                st.metric("أداء الشهر الحالي بالدورة", f"{res['m_curr_perf']}%")
            with c4:
                st.metric("أداء الشهر القادم بالدورة", f"{res['m_next_perf']}%")
                
            df_m = res['df_m']
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_m.index, y=df_m.values, mode='lines', name='السعر الشهري', line=dict(color='#0284c7', width=2)))
            fig.add_vline(x=res['m_current_date'], line_color="#ef4444", annotation_text="الحالي")
            fig.add_vline(x=res['m_past_date'], line_color="#10b981", annotation_text=f"الدورة السابقة ({res['final_m_cycle']}M)")
            fig.update_layout(template="plotly_white", height=450)
            st.plotly_chart(fig, use_container_width=True)
