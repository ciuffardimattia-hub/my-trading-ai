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

# --- 1. CONFIGURAZIONE E DIZIONARIO (v9.3 Hybrid) ---
st.set_page_config(page_title="CyberTrading v9.4", layout="wide", page_icon="🌐")

LANGUAGES = {
    "IT": {
        "hero_t": "CYBERTRADING HUB",
        "about_h": "Cos'è CyberTrading Hub?",
        "about_p": "Benvenuto nel futuro dell'analisi finanziaria. CyberTrading Hub è un ecosistema intelligente progettato per darti un vantaggio competitivo. Utilizziamo l'IA per incrociare i dati live con la TUA specifica situazione patrimoniale.",
        "feat_ia": "IA Tattica", "feat_ia_p": "Analisi predittiva su trend e indicatori tecnici.",
        "feat_cloud": "Cloud Vault", "feat_cloud_p": "Monitora il tuo patrimonio ovunque in sicurezza.",
        "feat_turbo": "Dati Real-Time", "feat_turbo_p": "Connessione diretta ai mercati globali.",
        "btn_enter": "ENTRA NEL HUB", "btn_login": "LOGIN", "btn_reg": "REGISTRATI",
        "btn_back": "← Indietro", "btn_logout": "ESCI", "sidebar_search": "Cerca Titolo",
        "port_perf": "Performance Patrimonio", "port_inv": "Investito", "port_val": "Valore Live",
        "chat_title": "AI Advisor", "news_title": "Data Stream News"
    },
    "EN": {
        "hero_t": "CYBERTRADING HUB",
        "about_h": "What is CyberTrading Hub?",
        "about_p": "Welcome to the future of financial analysis. CyberTrading Hub is an intelligent ecosystem designed to give you a competitive edge. We use AI to cross live data with YOUR specific financial situation.",
        "feat_ia": "Tactical AI", "feat_ia_p": "Predictive analysis on trends and technical indicators.",
        "feat_cloud": "Cloud Vault", "feat_cloud_p": "Monitor your wealth anywhere securely.",
        "feat_turbo": "Real-Time Data", "feat_turbo_p": "Direct connection to global markets.",
        "btn_enter": "ENTER HUB", "btn_login": "LOGIN", "btn_reg": "REGISTER",
        "btn_back": "← Back", "btn_logout": "LOGOUT", "sidebar_search": "Search Ticker",
        "port_perf": "Portfolio Performance", "port_inv": "Invested", "port_val": "Live Value",
        "chat_title": "AI Advisor", "news_title": "News Feed"
    }
}

# --- 2. STYLE CYBERPUNK ---
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #00ff41; }
    .hero-title { font-size: 60px; font-weight: 800; text-align: center; background: -webkit-linear-gradient(#00ff41, #ff00ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .about-section { background: rgba(10, 10, 10, 0.8); border-left: 5px solid #ff00ff; padding: 25px; margin: 30px auto; max-width: 900px; border-radius: 0 15px 15px 0; }
    div[data-testid="stMetric"] { background: rgba(20, 20, 20, 0.8); border: 1px solid #00ff41; border-radius: 10px; padding: 15px; }
    .stButton>button { background: linear-gradient(45deg, #ff00ff, #00ff41) !important; color: white !important; font-weight: bold; border-radius: 30px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. GESTIONE STATO ---
if 'lang' not in st.session_state: st.session_state.lang = "IT"
if 'page' not in st.session_state: st.session_state.page = "landing"
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

L = LANGUAGES[st.session_state.lang]

# --- 4. FUNZIONI CORE (FIXED) ---
def make_hashes(p): return hashlib.sha256(str.encode(p)).hexdigest()
def check_hashes(p, h): return make_hashes(p) == h

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300)
def get_market_prices(tickers):
    try:
        # FIX: Usiamo 5 giorni per evitare NaN se il mercato è appena chiuso
        df = yf.download(list(tickers), period="5d", interval="1d", group_by='ticker', progress=False)
        return df
    except: return None

def get_ai_chat_response(prompt, context, lang):
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key: return "API Key Error."
        genai.configure(api_key=api_key)
        # FIX: Utilizzo nome modello diretto per evitare 404 v1beta
        model = genai.GenerativeModel("gemini-1.5-flash")
        sys_i = f"Role: Cyber-Analyst. Data: {context}. Respond in {lang}. Tone: Professional Cyberpunk."
        res = model.generate_content([sys_i, prompt])
        return res.text
    except Exception as e: return f"Error IA: {str(e)}"

# --- 5. LANDING PAGE (v9.1 DESIGN) ---
if st.session_state.page == "landing" and not st.session_state.logged_in:
    st.session_state.lang = st.selectbox("🌐 Select Language", ["IT", "EN"], index=["IT", "EN"].index(st.session_state.lang))
    st.markdown(f"<div class='hero-title'>{L['hero_t']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='about-section'><h2>{L['about_h']}</h2><p>{L['about_p']}</p></div>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div style='border:1px solid #00ff41; padding:20px; border-radius:10px; text-align:center;'><h3>{L['feat_ia']}</h3><p>{L['feat_ia_p']}</p></div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='border:1px solid #ff00ff; padding:20px; border-radius:10px; text-align:center;'><h3>{L['feat_cloud']}</h3><p>{L['feat_cloud_p']}</p></div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='border:1px solid #00ff41; padding:20px; border-radius:10px; text-align:center;'><h3>{L['feat_turbo']}</h3><p>{L['feat_turbo_p']}</p></div>", unsafe_allow_html=True)
    
    if st.button(L['btn_enter']):
        st.session_state.page = "auth"
        st.rerun()

# --- 6. AUTH (v9.0) ---
elif st.session_state.page == "auth" and not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>🔐 Accesso</h2>", unsafe_allow_html=True)
    t1, t2 = st.tabs([L['btn_login'], L['btn_reg']])
    with t1:
        e = st.text_input("Email").lower()
        p = st.text_input("Password", type="password")
        if st.button(L['btn_login']):
            df_u = conn.read(worksheet="Utenti", ttl=0)
            u = df_u[df_u["Email"] == e]
            if not u.empty and check_hashes(p, u["Password"].values[0]):
                st.session_state.logged_in, st.session_state.user_email = True, e
                st.rerun()
    if st.button(L['btn_back']):
        st.session_state.page = "landing"
        st.rerun()

# --- 7. DASHBOARD (FIXED METRICS) ---
elif st.session_state.logged_in:
    st.sidebar.title(f"👾 {st.session_state.user_email}")
    t_search = st.sidebar.text_input(L['sidebar_search'], "BTC").upper()
    t_sym = f"{t_search}-USD" if t_search in ["BTC", "ETH", "SOL"] else t_search
    
    # FIX NAN: Gestione indici con fallback
    m_data = get_market_prices(["^GSPC", "BTC-USD", "GC=F"])
    c_m = st.columns(3)
    for i, s in enumerate(["^GSPC", "BTC-USD", "GC=F"]):
        try:
            # Prendiamo l'ultimo valore non nullo disponibile
            last_val = m_data[s]['Close'].dropna().iloc[-1]
            c_m[i].metric(s.replace("^GSPC", "S&P 500"), f"{last_val:.2f}")
        except: c_m[i].metric(s, "N/A")

    st.divider()

    # Patrimonio
    db_p = conn.read(worksheet="Portafoglio", ttl=0)
    miei = db_p[db_p["Email"] == st.session_state.user_email]
    tot_inv = 0
    if not miei.empty:
        st.subheader(f"📊 {L['port_perf']}")
        u_t = [f"{t}-USD" if t in ["BTC", "ETH", "SOL"] else t for t in miei["Ticker"].unique()]
        p_l = yf.download(u_t, period="5d", progress=False)['Close']
        tot_inv = miei["Totale"].sum()
        val_att = 0
        for _, r in miei.iterrows():
            tk = f"{r['Ticker']}-USD" if r['Ticker'] in ["BTC", "ETH", "SOL"] else r['Ticker']
            pr = p_l[tk].dropna().iloc[-1] if len(u_t) > 1 else p_l.dropna().iloc[-1]
            val_att += pr * r["Quantità"]
        c1, c2, c3 = st.columns(3)
        c1.metric(L['port_inv'], f"{tot_inv:.2f} $")
        c2.metric(L['port_val'], f"{val_att:.2f} $", delta=f"{val_att-tot_inv:.2f} $")
        c3.metric("ROI %", f"{((val_att/tot_inv)-1)*100:.2f}%")

    # Grafico e Chat (v9.0 style)
    data = yf.download(t_sym, period="1y", auto_adjust=True, progress=False)
    if not data.empty:
        df = data.copy()
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        st.header(f"📈 {t_sym}")
        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
        fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        cn, cc = st.columns([0.4, 0.6])
        with cc:
            st.subheader(f"💬 {L['chat_title']}")
            if 'msgs' not in st.session_state: st.session_state.msgs = []
            for m in st.session_state.msgs:
                with st.chat_message(m["role"]): st.markdown(m["content"])
            if inp := st.chat_input("Ask..."):
                st.session_state.msgs.append({"role": "user", "content": inp})
                with st.chat_message("user"): st.markdown(inp)
                with st.chat_message("assistant"):
                    ctx = f"Ticker {t_sym}, Price {df['Close'].iloc[-1]:.2f}, RSI {df['RSI'].iloc[-1]:.1f}, Portfolio {tot_inv}$"
                    res = get_ai_chat_response(inp, ctx, st.session_state.lang)
                    st.markdown(res)
                    st.session_state.msgs.append({"role": "assistant", "content": res})

    if st.sidebar.button(L['btn_logout']):
        st.session_state.logged_in, st.session_state.page = False, "landing"
        st.rerun()
