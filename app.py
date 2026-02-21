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
import time

# --- 1. CONFIGURAZIONE & STYLE ---
st.set_page_config(page_title="CyberTrading Hub v9.9.4", layout="wide", page_icon="⚡")

# NASCONDI LOGHI E HEADER STREAMLIT
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .stApp { background-color: #050505; color: #00ff41; }
            .hero-title { font-size: clamp(40px, 8vw, 70px); font-weight: 800; text-align: center; background: -webkit-linear-gradient(#00ff41, #ff00ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-top: 20px; }
            .about-section { background: rgba(10, 10, 10, 0.9); border-left: 5px solid #ff00ff; padding: 25px; margin: 30px auto; max-width: 950px; border-radius: 0 15px 15px 0; }
            div[data-testid="stMetric"] { background: rgba(20, 20, 20, 0.8); border: 1px solid #00ff41; border-radius: 10px; padding: 10px; }
            .stButton>button { background: linear-gradient(45deg, #ff00ff, #00ff41) !important; color: white !important; font-weight: bold; border-radius: 30px; width: 100%; }
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- 2. INIZIALIZZAZIONE IA ---
API_KEY = os.environ.get("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("⚠️ AI Configuration Missing.")

# --- 3. GESTIONE STATO ---
if 'page' not in st.session_state: st.session_state.page = "landing"
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 4. FUNZIONI NEWS & PREZZI ---
@st.cache_data(ttl=300)
def get_market_prices(tickers_list):
    try: return yf.download(tickers_list, period="5d", group_by='ticker', progress=False)
    except: return None

@st.cache_data(ttl=600)
def get_cached_news(symbol):
    news = []
    url = f"https://news.google.com/rss/search?q={symbol}+stock+news&hl=it&gl=IT&ceid=IT:it"
    try:
        r = requests.get(url, timeout=4)
        root = ET.fromstring(r.content)
        for i in root.findall('.//item')[:5]:
            news.append({'t': i.find('title').text, 'l': i.find('link').text})
    except: pass
    return news

# --- 5. LANDING PAGE ---
if st.session_state.page == "landing" and not st.session_state.logged_in:
    st.markdown("<div class='hero-title'>CYBERTRADING HUB</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>L'intelligenza artificiale al servizio del tuo patrimonio.</p>", unsafe_allow_html=True)
    
    st.markdown("<div class='about-section'><h2>Perché scegliere CyberTrading Hub?</h2><p>In un mercato dominato dagli algoritmi, l'investitore retail ha bisogno di strumenti avanzati. Il nostro Hub fonde i dati live con la potenza di Google Gemini per darti un analista privato 24/7.</p></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("ACCEDI AL TERMINALE"):
            st.session_state.page = "auth"
            st.rerun()
    with col2:
        if st.button("GUEST ACCESS (BETA)"):
            st.session_state.logged_in = True
            st.rerun()

# --- 6. AUTH SIMULATA (PER LANCIO) ---
elif st.session_state.page == "auth" and not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center; color: #ff00ff;'>Autenticazione Nodo</h2>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["ACCEDI", "REGISTRATI"])
    
    with t1:
        st.text_input("Email")
        st.text_input("Password", type="password")
        if st.button("ENTRA"):
            st.session_state.logged_in = True
            st.rerun()

    with t2:
        st.text_input("Nuova Email")
        st.text_input("Nuova Password", type="password")
        st.info("Nota: Per il lancio odierno, la registrazione è ad accesso libero istantaneo.")
        if st.button("CREA ACCOUNT"):
            st.session_state.logged_in = True
            st.rerun()
            
    if st.button("← Indietro"):
        st.session_state.page = "landing"
        st.rerun()

# --- 7. DASHBOARD REALE ---
elif st.session_state.logged_in:
    st.sidebar.title("👾 CyberTerminal v9.9.4")
    t_search = st.sidebar.text_input("Cerca Ticker", "BTC").upper()
    t_sym = f"{t_search}-USD" if t_search in ["BTC", "ETH", "SOL", "XRP"] else t_search

    # Top Bar Prezzi
    tickers_map = {"BTC-USD": "Bitcoin", "GC=F": "Oro", "^IXIC": "Nasdaq", "NVDA": "Nvidia"}
    m_data = get_market_prices(list(tickers_map.keys()))
    cols = st.columns(4)
    for i, (sym, name) in enumerate(tickers_map.items()):
        try:
            val = m_data[sym]['Close'].dropna().iloc[-1]
            cols[i].metric(name, f"${val:.2f}")
        except: cols[i].metric(name, "N/A")

    st.divider()

    # Grafico & Analisi
    data = yf.download(t_sym, period="6mo", interval="1d", auto_adjust=True, progress=False)
    if not data.empty:
        df = data.copy()
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df['SMA20'] = ta.sma(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        st.header(f"📈 Analisi Tecnica: {t_sym}")
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Prezzo"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], name="SMA 20", line=dict(color='orange', width=2)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='magenta', width=2)), row=2, col=1)
        fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

        c1, c2 = st.columns([0.4, 0.6])
        with c1:
            st.subheader("📰 News Feed")
            for n in get_cached_news(t_search): st.markdown(f"• [{n['t']}]({n['l']})")
        with c2:
            st.subheader("💬 AI Tactical Advisor")
            if 'msgs' not in st.session_state: st.session_state.msgs = []
            for m in st.session_state.msgs:
                with st.chat_message(m["role"]): st.markdown(m["content"])
            
            if inp := st.chat_input("Chiedi all'IA su questo asset..."):
                st.session_state.msgs.append({"role": "user", "content": inp})
                with st.chat_message("user"): st.markdown(inp)
                with st.chat_message("assistant"):
                    ctx = f"Ticker {t_sym}, Prezzo {df['Close'].iloc[-1]:.2f}, RSI {df['RSI'].iloc[-1]:.1f}, SMA20 {df['SMA20'].iloc[-1]:.1f}."
                    res = model.generate_content(f"Agisci come analista senior. Contesto: {ctx}. Rispondi brevemente in italiano a: {inp}").text
                    st.markdown(res)
                    st.session_state.msgs.append({"role": "assistant", "content": res})

    if st.sidebar.button("LOGOUT"):
        st.session_state.logged_in = False
        st.rerun()

# Disclaimer
st.markdown("<div style='text-align: center; color: #444; font-size: 10px; margin-top: 50px;'>CyberTrading Hub è uno strumento IA. Non è consulenza finanziaria. Investi con testa.</div>", unsafe_allow_html=True)
