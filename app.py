import streamlit as st
import google.generativeai as genai
import os
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import xml.etree.ElementTree as ET

# --- 1. CONFIGURAZIONE & LINGUE ---
st.set_page_config(page_title="Market-Core Terminal", layout="wide", page_icon="⚡")

LANGUAGES = {
    "IT": {
        "hero_t": "MARKET-CORE", "hero_s": "Sistemi di Analisi Quantitativa IA.",
        "about_h": "Perché Market-Core?",
        "about_p": "Il nostro Hub fonde i dati live con la potenza di Google Gemini per darti un analista privato 24/7.",
        "feat_ia": "Analisi Tattica IA", "feat_ia_p": "Segnali basati su RSI e SMA20.",
        "feat_cloud": "Portfolio Criptato", "feat_cloud_p": "Dati salvati su cloud sicuri (Beta).",
        "feat_turbo": "Dati Tempo Reale", "feat_turbo_p": "Connessione diretta ai mercati mondiali.",
        "btn_enter": "INIZIALIZZA NODO DI ACCESSO", "main_search": "INSERISCI TICKER DA ANALIZZARE",
        "chat_title": "AI Tactical Advisor", "news_title": "Data Stream News",
        "side_info": "ℹ️ Info Strumenti", "side_desc": "Usa il Terminale per scansionare asset in tempo reale.",
        "disclaimer": "⚠️ Disclaimer: Market-Core è uno strumento IA. Non è consulenza finanziaria."
    },
    "EN": {
        "hero_t": "MARKET-CORE", "hero_s": "AI Quantitative Analysis Systems.",
        "about_h": "Why Market-Core?",
        "about_p": "Our Hub merges live data with Google Gemini to give you a 24/7 private analyst.",
        "feat_ia": "AI Tactical Analysis", "feat_ia_p": "Signals based on RSI and SMA20.",
        "feat_cloud": "Encrypted Portfolio", "feat_cloud_p": "Data saved on secure clouds (Beta).",
        "feat_turbo": "Real-Time Data", "feat_turbo_p": "Direct connection to markets.",
        "btn_enter": "INITIALIZE ACCESS NODE", "main_search": "ENTER TICKER TO ANALYZE",
        "chat_title": "AI Tactical Advisor", "news_title": "Data Stream News",
        "side_info": "ℹ️ Tool Info", "side_desc": "Use the Terminal to scan assets in real-time.",
        "disclaimer": "⚠️ Disclaimer: Market-Core is an AI tool. Not financial advice."
    }
}

# --- 2. CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #00ff41; font-family: 'Courier New', monospace; }
    .hero-title { font-size: 80px; font-weight: 900; text-align: center; background: linear-gradient(90deg, #00ff41, #ff00ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .about-section { background: rgba(10, 10, 10, 0.9); border-left: 5px solid #ff00ff; padding: 25px; margin: 20px auto; max-width: 900px; border-radius: 0 15px 15px 0; }
    .feat-card { border: 1px solid #333; padding: 20px; border-radius: 15px; text-align: center; background: rgba(20,20,20,0.5); min-height: 160px; }
    .stButton>button { background: transparent !important; color: #00ff41 !important; border: 2px solid #00ff41 !important; width: 100%; font-weight: bold; }
    .stButton>button:hover { background: #00ff41 !important; color: black !important; }
    #MainMenu, footer, header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGICA ---
if 'lang' not in st.session_state: st.session_state.lang = "IT"
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
L = LANGUAGES[st.session_state.lang]

# Fix Gemini Model (404 Error fix)
API_KEY = os.environ.get("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-pro') # Più stabile su Render

@st.cache_data(ttl=300)
def get_market_prices(tickers_list):
    try: return yf.download(tickers_list, period="5d", group_by='ticker', progress=False)
    except: return None

# --- 4. LANDING PAGE ---
if not st.session_state.logged_in:
    c1, c2, c3 = st.columns([4, 1, 4])
    with c2: st.session_state.lang = st.selectbox("🌐", ["IT", "EN"], index=["IT", "EN"].index(st.session_state.lang))
    
    st.markdown(f"<div class='hero-title'>{L['hero_t']}</div>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #888; font-size:20px;'>{L['hero_s']}</p>", unsafe_allow_html=True)
    
    st.markdown(f"<div class='about-section'><h2>{L['about_h']}</h2><p>{L['about_p']}</p></div>", unsafe_allow_html=True)
    
    col_f1, col_f2, col_f3 = st.columns(3)
    col_f1.markdown(f"<div class='feat-card'><h3>{L['feat_ia']}</h3><p>{L['feat_ia_p']}</p></div>", unsafe_allow_html=True)
    col_f2.markdown(f"<div class='feat-card' style='border-color:#ff00ff;'><h3>{L['feat_cloud']}</h3><p>{L['feat_cloud_p']}</p></div>", unsafe_allow_html=True)
    col_f3.markdown(f"<div class='feat-card'><h3>{L['feat_turbo']}</h3><p>{L['feat_turbo_p']}</p></div>", unsafe_allow_html=True)
    
    st.write("##")
    if st.button(L['btn_enter']):
        st.session_state.logged_in = True
        st.rerun()

# --- 5. TERMINALE OPERATIVO ---
else:
    # Sidebar
    st.sidebar.markdown(f"<h2 style='color:#ff00ff;'>{L['hero_t']}</h2>", unsafe_allow_html=True)
    st.session_state.lang = st.sidebar.selectbox("🌐", ["IT", "EN"], index=["IT", "EN"].index(st.session_state.lang))
    with st.sidebar.expander(L['side_info']): st.write(L['side_desc'])
    
    # Ticker Selection al centro (Ripristinata)
    st.markdown(f"### 🔍 {L['main_search']}")
    t_input = st.text_input("", "NVDA").upper()
    t_sym = f"{t_input}-USD" if t_input in ["BTC", "ETH", "SOL"] else t_input

    # Ticker Bar (No NAN)
    trending = {"BTC-USD": "BTC", "NVDA": "NVDA", "GC=F": "GOLD", "TSLA": "TSLA", "AAPL": "APPLE"}
    m_prices = get_market_prices(list(trending.keys()))
    t_cols = st.columns(5)
    for i, (sym, name) in enumerate(trending.items()):
        try:
            p = m_prices[sym]['Close'].dropna().iloc[-1]
            t_cols[i].metric(name, f"${p:.2f}")
        except: t_cols[i].metric(name, "N/A")

    st.divider()

    # Grafico & AI
    data = yf.download(t_sym, period="1y", interval="1d", auto_adjust=True, progress=False)
    if not data.empty:
        df = data.copy()
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df['SMA20'] = ta.sma(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], name="SMA 20", line=dict(color='orange')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='magenta')), row=2, col=1)
        fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, use_container_width=True)

        c1, c2 = st.columns([0.4, 0.6])
        with c1:
            st.subheader(f"📰 {L['news_title']}")
            st.info(f"Scansione news per {t_input}...")
        with c2:
            st.subheader(f"💬 {L['chat_title']}")
            if 'msgs' not in st.session_state: st.session_state.msgs = []
            for m in st.session_state.msgs:
                with st.chat_message(m["role"]): st.markdown(m["content"])
            
            if inp := st.chat_input("Comando IA..."):
                st.session_state.msgs.append({"role": "user", "content": inp})
                with st.chat_message("user"): st.markdown(inp)
                with st.chat_message("assistant"):
                    ctx = f"Asset {t_sym}, Prezzo {df['Close'].iloc[-1]:.2f}, RSI {df['RSI'].iloc[-1]:.1f}"
                    try:
                        res = model.generate_content(f"Analista Senior. Dati: {ctx}. Rispondi in {st.session_state.lang} a: {inp}").text
                        st.markdown(res)
                        st.session_state.msgs.append({"role": "assistant", "content": res})
                    except Exception as e:
                        st.error(f"AI Error: {e}")

    if st.sidebar.button("LOGOUT"):
        st.session_state.logged_in = False
        st.rerun()

st.markdown(f"<div style='text-align:center; color:#444; font-size:10px; margin-top:50px;'>{L['disclaimer']}</div>", unsafe_allow_html=True)
