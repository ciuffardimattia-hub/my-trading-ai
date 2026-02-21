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

# --- 1. CONFIGURAZIONE & DIZIONARIO LINGUE ---
st.set_page_config(page_title="Market-Core Terminal", layout="wide", page_icon="⚡")

LANGUAGES = {
    "IT": {
        "hero_t": "MARKET-CORE", "hero_s": "L'intelligenza artificiale al servizio del tuo patrimonio.",
        "about_h": "Perché scegliere Market-Core?",
        "about_p": "In un mercato dominato dagli algoritmi, l'investitore retail ha bisogno di strumenti avanzati. Il nostro Hub fonde i dati live con la potenza di Google Gemini.",
        "feat_ia": "Analisi Tattica IA", "feat_ia_p": "Segnali basati su RSI e SMA20.",
        "feat_cloud": "Portfolio Criptato", "feat_cloud_p": "Dati salvati su cloud sicuri (Beta).",
        "feat_turbo": "Dati Tempo Reale", "feat_turbo_p": "Connessione diretta ai mercati.",
        "btn_enter": "INIZIALIZZA NODO DI ACCESSO", "sidebar_search": "Cerca Titolo",
        "chat_title": "AI Tactical Advisor", "news_title": "Data Stream News",
        "side_save": "Salva Operazione", "side_info": "Configura i tuoi parametri di acquisto.",
        "disclaimer": "⚠️ Market-Core è uno strumento IA. Non costituisce consulenza finanziaria."
    },
    "EN": {
        "hero_t": "MARKET-CORE", "hero_s": "AI at the service of your assets.",
        "about_h": "Why choose Market-Core?",
        "about_p": "In a market dominated by algorithms, retail investors need advanced tools. Our Hub merges live data with Google Gemini power.",
        "feat_ia": "AI Tactical Analysis", "feat_ia_p": "Signals based on RSI and SMA20.",
        "feat_cloud": "Encrypted Portfolio", "feat_cloud_p": "Data saved on secure clouds (Beta).",
        "feat_turbo": "Real-Time Data", "feat_turbo_p": "Direct connection to markets.",
        "btn_enter": "INITIALIZE ACCESS NODE", "sidebar_search": "Search Ticker",
        "chat_title": "AI Tactical Advisor", "news_title": "Data Stream News",
        "side_save": "Save Trade", "side_info": "Configure your purchase parameters.",
        "disclaimer": "⚠️ Market-Core is an AI tool. Not financial advice."
    },
    "ES": {
        "hero_t": "MARKET-CORE", "hero_s": "IA al servicio de su patrimonio.",
        "about_h": "¿Por qué elegir Market-Core?",
        "about_p": "Nuestro Hub fusiona datos en vivo con la potencia de Google Gemini.",
        "feat_ia": "Análisis IA", "feat_ia_p": "Señales basadas en RSI y SMA20.",
        "feat_cloud": "Cartera Cripto", "feat_cloud_p": "Datos en nubes seguras (Beta).",
        "feat_turbo": "Datos Reales", "feat_turbo_p": "Conexión directa a mercados.",
        "btn_enter": "INICIALIZAR NODO", "sidebar_search": "Buscar Ticker",
        "chat_title": "Asesor IA", "news_title": "Noticias",
        "side_save": "Guardar Op", "side_info": "Configura tus parámetros.",
        "disclaimer": "⚠️ Market-Core es IA. No es asesoramiento financiero."
    }
}

# --- 2. CSS CUSTOM ---
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #00ff41; font-family: 'Courier New', monospace; }
    .hero-title { font-size: 80px; font-weight: 900; text-align: center; background: linear-gradient(90deg, #00ff41, #ff00ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .about-section { background: rgba(10, 10, 10, 0.9); border-left: 5px solid #ff00ff; padding: 25px; margin: 20px auto; max-width: 900px; border-radius: 0 15px 15px 0; }
    .feat-card { border: 1px solid #333; padding: 20px; border-radius: 15px; text-align: center; background: rgba(20,20,20,0.5); min-height: 150px; }
    .stButton>button { background: transparent !important; color: #00ff41 !important; border: 2px solid #00ff41 !important; width: 100%; font-weight: bold; }
    .stButton>button:hover { background: #00ff41 !important; color: black !important; box-shadow: 0 0 15px #00ff41; }
    #MainMenu, footer, header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. STATO E LOGICA ---
if 'lang' not in st.session_state: st.session_state.lang = "IT"
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
L = LANGUAGES[st.session_state.lang]

API_KEY = os.environ.get("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

# --- 4. FUNZIONI DATI (FIX NAN) ---
@st.cache_data(ttl=300)
def get_market_prices(tickers_list):
    try: return yf.download(tickers_list, period="5d", group_by='ticker', progress=False)
    except: return None

# --- 5. LANDING PAGE ---
if not st.session_state.logged_in:
    # Selettore Lingua in alto
    c1, c2, c3 = st.columns([4, 1, 4])
    with c2:
        st.session_state.lang = st.selectbox("🌐", ["IT", "EN", "ES"], index=["IT", "EN", "ES"].index(st.session_state.lang))
    
    st.markdown(f"<div class='hero-title'>{L['hero_t']}</div>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #888; font-size:20px;'>{L['hero_s']}</p>", unsafe_allow_html=True)
    
    st.markdown(f"<div class='about-section'><h2>{L['about_h']}</h2><p>{L['about_p']}</p></div>", unsafe_allow_html=True)
    
    # LE 3 PAGINETTE (BOX)
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        st.markdown(f"<div class='feat-card'><h3>{L['feat_ia']}</h3><p>{L['feat_ia_p']}</p></div>", unsafe_allow_html=True)
    with col_f2:
        st.markdown(f"<div class='feat-card' style='border-color:#ff00ff;'><h3>{L['feat_cloud']}</h3><p>{L['feat_cloud_p']}</p></div>", unsafe_allow_html=True)
    with col_f3:
        st.markdown(f"<div class='feat-card'><h3>{L['feat_turbo']}</h3><p>{L['feat_turbo_p']}</p></div>", unsafe_allow_html=True)
    
    st.write("##")
    if st.button(L['btn_enter']):
        st.session_state.logged_in = True
        st.rerun()

# --- 6. TERMINALE ---
else:
    # Sidebar con Lingua e Info
    st.sidebar.markdown(f"<h2 style='color:#ff00ff;'>{L['hero_t']}</h2>", unsafe_allow_html=True)
    st.session_state.lang = st.sidebar.selectbox("🌐", ["IT", "EN", "ES"], index=["IT", "EN", "ES"].index(st.session_state.lang))
    
    t_input = st.sidebar.text_input(L['sidebar_search'], "BTC").upper()
    t_sym = f"{t_input}-USD" if t_input in ["BTC", "ETH", "SOL"] else t_input

    # Finestra rapida impostazioni (Sidebar)
    with st.sidebar.expander(f"ℹ️ {L['side_save']}"):
        st.write(L['side_info'])
        st.number_input("Prezzo di carico ($)", min_value=0.0)
        st.button("SALVA (DEMO)")

    # Ticker Bar (FIX NAN)
    trending = {"BTC-USD": "BTC", "NVDA": "NVDA", "GC=F": "ORO", "TSLA": "TSLA", "ETH-USD": "ETH"}
    m_prices = get_market_prices(list(trending.keys()))
    t_cols = st.columns(5)
    for i, (sym, name) in enumerate(trending.items()):
        try:
            # Prende l'ultimo valore non nullo (così risolve il problema delle borse chiuse)
            p = m_prices[sym]['Close'].dropna().iloc[-1]
            t_cols[i].metric(name, f"${p:.2f}")
        except: t_cols[i].metric(name, "N/A")

    st.divider()

    # Dashboard Principale
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
        fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        c1, c2 = st.columns([0.4, 0.6])
        with c1:
            st.subheader(f"📰 {L['news_title']}")
            st.write(f"Feed live per {t_input}...")
        with c2:
            st.subheader(f"💬 {L['chat_title']}")
            if prompt := st.chat_input("Comando IA..."):
                res = model.generate_content(f"Analizza brevemente {t_sym} in {st.session_state.lang}").text
                st.write(res)

    if st.sidebar.button("LOGOUT"):
        st.session_state.logged_in = False
        st.rerun()

st.markdown(f"<div style='text-align:center; color:#444; font-size:10px;'>{L['disclaimer']}</div>", unsafe_allow_html=True)
