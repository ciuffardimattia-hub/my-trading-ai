import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai
import requests
import xml.etree.ElementTree as ET
import hashlib

# --- 1. CONFIGURAZIONE & DIZIONARIO LINGUE ---
st.set_page_config(page_title="CyberTrading Global v9.2", layout="wide", page_icon="🌐")

LANGUAGES = {
    "IT": {
        "hero_t": "CYBERTRADING HUB", "hero_s": "L'eccellenza dell'IA applicata al tuo portafoglio.",
        "about_h": "Cos'è CyberTrading Hub?", "about_p": "Un ecosistema intelligente che incrocia dati live e il tuo portafoglio tramite IA.",
        "feat_ia": "IA Tattica", "feat_ia_p": "Analisi predittiva su trend e indicatori tecnici.",
        "feat_cloud": "Cloud Vault", "feat_cloud_p": "Monitora il tuo patrimonio ovunque in sicurezza.",
        "feat_turbo": "Dati Real-Time", "feat_turbo_p": "Connessione diretta ai mercati globali.",
        "btn_enter": "ACCEDI AL TERMINALE", "btn_login": "LOGIN", "btn_reg": "REGISTRATI",
        "btn_back": "← Indietro", "btn_logout": "ESCI", "sidebar_search": "Cerca Titolo",
        "port_inv": "Investito", "port_val": "Valore Live", "port_perf": "Performance",
        "ai_node": "Nodo AI Attivo", "news_title": "Notizie", "chat_title": "AI Advisor",
        "auth_title": "Autenticazione Nodo"
    },
    "EN": {
        "hero_t": "CYBERTRADING HUB", "hero_s": "AI excellence applied to your financial portfolio.",
        "about_h": "What is CyberTrading Hub?", "about_p": "An intelligent ecosystem that crosses live data and your portfolio via AI.",
        "feat_ia": "Tactical AI", "feat_ia_p": "Predictive analysis on trends and technical indicators.",
        "feat_cloud": "Cloud Vault", "feat_cloud_p": "Monitor your wealth anywhere securely.",
        "feat_turbo": "Real-Time Data", "feat_turbo_p": "Direct connection to global markets.",
        "btn_enter": "ENTER TERMINAL", "btn_login": "LOGIN", "btn_reg": "REGISTER",
        "btn_back": "← Back", "btn_logout": "LOGOUT", "sidebar_search": "Search Ticker",
        "port_inv": "Invested", "port_val": "Live Value", "port_perf": "Performance",
        "ai_node": "AI Node Active", "news_title": "News Feed", "chat_title": "AI Advisor",
        "auth_title": "Node Authentication"
    },
    "ES": {
        "hero_t": "CYBERTRADING HUB", "hero_s": "Excelencia de la IA aplicada a su cartera financiera.",
        "about_h": "¿Qué es CyberTrading Hub?", "about_p": "Un ecosistema inteligente que cruza datos en vivo y su cartera a través de IA.",
        "feat_ia": "IA Táctica", "feat_ia_p": "Análisis predictivo de tendencias e indicadores técnicos.",
        "feat_cloud": "Bóveda Cloud", "feat_cloud_p": "Monitoree su patrimonio en cualquier lugar de forma segura.",
        "feat_turbo": "Datos en Tiempo Real", "feat_turbo_p": "Conexión directa con los mercados globales.",
        "btn_enter": "ENTRAR AL TERMINAL", "btn_login": "CONECTAR", "btn_reg": "REGISTRAR",
        "btn_back": "← Volver", "btn_logout": "SALIR", "sidebar_search": "Buscar Ticker",
        "port_inv": "Invertido", "port_val": "Valor en Vivo", "port_perf": "Rendimiento",
        "ai_node": "Nodo IA Activo", "news_title": "Noticias", "chat_title": "Asesor IA",
        "auth_title": "Autenticación de Nodo"
    }
}

# --- 2. STYLE CYBERPUNK ---
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #00ff41; }
    .hero-title { font-size: 60px; font-weight: 800; text-align: center; background: -webkit-linear-gradient(#00ff41, #ff00ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .about-section { background: rgba(10, 10, 10, 0.8); border-left: 5px solid #ff00ff; padding: 25px; margin: 30px auto; max-width: 900px; border-radius: 15px; }
    div[data-testid="stMetric"] { background: rgba(20, 20, 20, 0.8); border: 1px solid #00ff41; border-radius: 10px; }
    .stButton>button { background: linear-gradient(45deg, #ff00ff, #00ff41) !important; color: white !important; font-weight: bold; border-radius: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. GESTIONE STATO ---
if 'lang' not in st.session_state: st.session_state.lang = "IT"
if 'page' not in st.session_state: st.session_state.page = "landing"
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

L = LANGUAGES[st.session_state.lang]

# --- 4. FUNZIONI CORE ---
def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()
def check_hashes(password, hashed_text): return make_hashes(password) == hashed_text

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300)
def get_market_prices(tickers):
    return yf.download(list(tickers), period="1d", group_by='ticker', progress=False)

def get_ai_chat_response(prompt, context, lang):
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key: return "API Key missing."
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        sys_instr = f"Role: Cyber-Analyst. Data: {context}. Respond in {lang}. Tone: Professional, Cyberpunk."
        response = model.generate_content([sys_instr, prompt])
        return response.text
    except Exception as e: return f"Error: {e}"

# --- 5. LANDING PAGE ---
if st.session_state.page == "landing" and not st.session_state.logged_in:
    # Language Selector in alto
    st.session_state.lang = st.selectbox("🌐 Select Language", ["IT", "EN", "ES"], index=["IT", "EN", "ES"].index(st.session_state.lang))
    
    st.markdown(f"<div class='hero-title'>{L['hero_t']}</div>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #888;'>{L['hero_s']}</p>", unsafe_allow_html=True)
    
    st.markdown(f"<div class='about-section'><h2>{L['about_h']}</h2><p>{L['about_p']}</p></div>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div style='border:1px solid #00ff41; padding:20px; border-radius:10px; text-align:center;'><h3>{L['feat_ia']}</h3><p>{L['feat_ia_p']}</p></div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='border:1px solid #ff00ff; padding:20px; border-radius:10px; text-align:center;'><h3>{L['feat_cloud']}</h3><p>{L['feat_cloud_p']}</p></div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='border:1px solid #00ff41; padding:20px; border-radius:10px; text-align:center;'><h3>{L['feat_turbo']}</h3><p>{L['feat_turbo_p']}</p></div>", unsafe_allow_html=True)
    
    st.write("##")
    if st.button(L['btn_enter']):
        st.session_state.page = "auth"
        st.rerun()

# --- 6. AUTH PAGE ---
elif st.session_state.page == "auth" and not st.session_state.logged_in:
    st.markdown(f"<h2 style='text-align: center;'>{L['auth_title']}</h2>", unsafe_allow_html=True)
    t1, t2 = st.tabs([L['btn_login'], L['btn_reg']])
    with t1:
        e = st.text_input("Email").lower()
        p = st.text_input("Password", type="password")
        if st.button(L['btn_login']):
            df_u = conn.read(worksheet="Utenti", ttl=0)
            u = df_u[df_u["Email"] == e]
            if not u.empty and check_hashes(p, u["Password"].values[0]):
                st.session_state.logged_in = True
                st.session_state.user_email = e
                st.rerun()
            else: st.error("Invalid credentials.")
    if st.button(L['btn_back']):
        st.session_state.page = "landing"
        st.rerun()

# --- 7. DASHBOARD (CUORE) ---
elif st.session_state.logged_in:
    st.sidebar.title(f"👾 {st.session_state.user_email}")
    st.session_state.lang = st.sidebar.selectbox("🌐 Language", ["IT", "EN", "ES"], index=["IT", "EN", "ES"].index(st.session_state.lang))
    
    ticker_search = st.sidebar.text_input(L['sidebar_search'], "NVDA").upper()
    ticker_sym = f"{ticker_search}-USD" if ticker_search in ["BTC", "ETH", "SOL"] else ticker_search
    
    if st.sidebar.button(L['btn_logout']):
        st.session_state.logged_in = False
        st.session_state.page = "landing"
        st.rerun()

    # Prezzi Live in alto
    indices = ["^GSPC", "BTC-USD", "GC=F"]
    m_data = get_market_prices(indices)
    cols = st.columns(3)
    for i, s in enumerate(indices):
        cols[i].metric(s.replace("^GSPC", "S&P 500"), f"{m_data[s]['Close'].iloc[-1]:.2f}")

    st.divider()

    # Portafoglio Globale
    db_p = conn.read(worksheet="Portafoglio", ttl=0)
    miei = db_p[db_p["Email"] == st.session_state.user_email]
    tot_inv = 0
    if not miei.empty:
        st.subheader(f"📊 {L['port_perf']}")
        unique_t = [f"{t}-USD" if t in ["BTC", "ETH", "SOL"] else t for t in miei["Ticker"].unique()]
        p_live = yf.download(unique_t, period="1d", progress=False)['Close'].iloc[-1]
        tot_inv = miei["Totale"].sum()
        val_att = 0
        for _, r in miei.iterrows():
            tk = f"{r['Ticker']}-USD" if r['Ticker'] in ["BTC", "ETH", "SOL"] else r['Ticker']
            pr = p_live[tk] if len(unique_t) > 1 else p_live
            val_att += pr * r["Quantità"]
        c1, c2, c3 = st.columns(3)
        c1.metric(L['port_inv'], f"{tot_inv:.2f} $")
        c2.metric(L['port_val'], f"{val_att:.2f} $", delta=f"{val_att-tot_inv:.2f} $")
        c3.metric(f"{L['port_perf']} %", f"{((val_att/tot_inv)-1)*100:.2f}%")

    # Grafico Titolo
    data = yf.download(ticker_sym, period="1y", auto_adjust=True, progress=False)
    if not data.empty:
        df = data.copy()
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        st.header(f"📈 {ticker_sym}")
        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
        fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        # Chat IA Poliglotta
        st.subheader(f"💬 {L['chat_title']}")
        if 'msgs' not in st.session_state: st.session_state.msgs = []
        for m in st.session_state.msgs:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        if inp := st.chat_input("Ask something..."):
            st.session_state.msgs.append({"role": "user", "content": inp})
            with st.chat_message("user"): st.markdown(inp)
            with st.chat_message("assistant"):
                ctx = f"Ticker {ticker_sym}, Price {df['Close'].iloc[-1]:.2f}, RSI {df['RSI'].iloc[-1]:.1f}, Invested {tot_inv}$"
                res = get_ai_chat_response(inp, ctx, st.session_state.lang)
                st.markdown(res)
                st.session_state.msgs.append({"role": "assistant", "content": res})
