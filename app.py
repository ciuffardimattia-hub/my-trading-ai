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

# --- 1. CONFIGURAZIONE E DIZIONARIO MULTILINGUA (v9.2) ---
st.set_page_config(page_title="CyberTrading Hybrid v9.3", layout="wide", page_icon="🌐")

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
    },
    "ES": {
        "hero_t": "CYBERTRADING HUB",
        "about_h": "¿Qué es CyberTrading Hub?",
        "about_p": "Bienvenido al futuro del análisis financiero. CyberTrading Hub es un ecosistema inteligente diseñado para darle una ventaja competitiva. Usamos IA para cruzar datos en vivo con SU situación financiera específica.",
        "feat_ia": "IA Táctica", "feat_ia_p": "Análisis predictivo de tendencias e indicadores técnicos.",
        "feat_cloud": "Bóveda Cloud", "feat_cloud_p": "Monitoree su patrimonio en cualquier lugar de forma segura.",
        "feat_turbo": "Datos Real-Time", "feat_turbo_p": "Conexión directa con los mercados globales.",
        "btn_enter": "ENTRAR AL HUB", "btn_login": "CONECTAR", "btn_reg": "REGISTRAR",
        "btn_back": "← Volver", "btn_logout": "SALIR", "sidebar_search": "Buscar Ticker",
        "port_perf": "Rendimiento de Cartera", "port_inv": "Invertido", "port_val": "Valor en Vivo",
        "chat_title": "Asesor IA", "news_title": "Noticias"
    }
}

# --- 2. STYLE CYBERPUNK ---
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #00ff41; }
    .hero-title { font-size: 65px; font-weight: 800; text-align: center; background: -webkit-linear-gradient(#00ff41, #ff00ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-top: 30px; }
    .about-section { background: rgba(10, 10, 10, 0.8); border-left: 5px solid #ff00ff; padding: 25px; margin: 30px auto; max-width: 900px; border-radius: 0 15px 15px 0; }
    div[data-testid="stMetric"] { background: rgba(20, 20, 20, 0.8); border: 1px solid #00ff41; border-radius: 10px; padding: 15px; }
    .stButton>button { background: linear-gradient(45deg, #ff00ff, #00ff41) !important; color: white !important; font-weight: bold; border-radius: 30px; padding: 10px 25px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. GESTIONE STATO ---
if 'lang' not in st.session_state: st.session_state.lang = "IT"
if 'page' not in st.session_state: st.session_state.page = "landing"
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

L = LANGUAGES[st.session_state.lang]

# --- 4. FUNZIONI CORE (Hash, Cache, DB, AI) ---
def make_hashes(p): return hashlib.sha256(str.encode(p)).hexdigest()
def check_hashes(p, h): return make_hashes(p) == h

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300)
def get_market_prices(tickers):
    return yf.download(list(tickers), period="1d", group_by='ticker', progress=False)

@st.cache_data(ttl=600)
def get_cached_news(symbol):
    news = []
    q = symbol.replace("-USD", "")
    url = f"https://news.google.com/rss/search?q={q}+stock+news+when:7d&hl=it&gl=IT&ceid=IT:it"
    try:
        r = requests.get(url, timeout=3)
        root = ET.fromstring(r.content)
        for i in root.findall('.//item')[:5]: news.append({'t': i.find('title').text, 'l': i.find('link').text})
    except: pass
    return news

def get_ai_chat_response(prompt, context, lang):
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key: return "API Key Error."
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        sys_i = f"Role: Cyber-Analyst v9.3. Data: {context}. Respond in {lang}. Tone: Professional Cyberpunk."
        res = model.generate_content([sys_i, prompt])
        return res.text
    except Exception as e: return f"Error IA: {e}"

# --- 5. SCHERMATA LANDING (v9.1 DESIGN) ---
if st.session_state.page == "landing" and not st.session_state.logged_in:
    # Selettore Lingua in alto a destra
    st.session_state.lang = st.selectbox("🌐 Select Language", ["IT", "EN", "ES"], index=["IT", "EN", "ES"].index(st.session_state.lang))
    
    st.markdown(f"<div class='hero-title'>{L['hero_t']}</div>", unsafe_allow_html=True)
    
    # Sezione Narrativa (v9.1)
    st.markdown(f"""
    <div class='about-section'>
        <h2 style='color: #00ff41;'>{L['about_h']}</h2>
        <p style='color: #eee; font-size: 1.1rem;'>{L['about_p']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature Cards (v9.1)
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div style='border:1px solid #00ff41; padding:20px; border-radius:10px; text-align:center;'><h3>{L['feat_ia']}</h3><p>{L['feat_ia_p']}</p></div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='border:1px solid #ff00ff; padding:20px; border-radius:10px; text-align:center;'><h3>{L['feat_cloud']}</h3><p>{L['feat_cloud_p']}</p></div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='border:1px solid #00ff41; padding:20px; border-radius:10px; text-align:center;'><h3>{L['feat_turbo']}</h3><p>{L['feat_turbo_p']}</p></div>", unsafe_allow_html=True)
    
    st.write("##")
    if st.button(L['btn_enter']):
        st.session_state.page = "auth"
        st.rerun()

# --- 6. SCHERMATA AUTH (v9.0 DESIGN) ---
elif st.session_state.page == "auth" and not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center; color: #ff00ff;'>🔐 Authorization Terminal</h2>", unsafe_allow_html=True)
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
            else: st.error("Access Denied.")
    if st.button(L['btn_back']):
        st.session_state.page = "landing"
        st.rerun()

# --- 7. SCHERMATA DASHBOARD (v9.0 INTERATTIVA) ---
elif st.session_state.logged_in:
    # Sidebar
    st.sidebar.title(f"👾 Hub: {st.session_state.user_email}")
    st.session_state.lang = st.sidebar.selectbox("🌐 Language", ["IT", "EN", "ES"], index=["IT", "EN", "ES"].index(st.session_state.lang))
    
    t_search = st.sidebar.text_input(L['sidebar_search'], "BTC").upper()
    t_sym = f"{t_search}-USD" if t_search in ["BTC", "ETH", "SOL"] else t_search
    
    if st.sidebar.button(L['btn_logout']):
        st.session_state.logged_in = False
        st.session_state.page = "landing"
        st.rerun()

    # Dashboard Interactiva v9.0
    indices = ["^GSPC", "BTC-USD", "GC=F"]
    m_data = get_market_prices(indices)
    c_m1, c_m2, c_m3 = st.columns(3)
    c_m1.metric("S&P 500", f"{m_data['^GSPC']['Close'].iloc[-1]:.2f}")
    c_m2.metric("Bitcoin", f"{m_data['BTC-USD']['Close'].iloc[-1]:.2f}")
    c_m3.metric("Gold", f"{m_data['GC=F']['Close'].iloc[-1]:.2f}")
    
    st.divider()

    # Patrimonio v9.0
    db_p = conn.read(worksheet="Portafoglio", ttl=0)
    miei = db_p[db_p["Email"] == st.session_state.user_email]
    tot_inv = 0
    if not miei.empty:
        st.subheader(f"📊 {L['port_perf']}")
        u_tickers = [f"{t}-USD" if t in ["BTC", "ETH", "SOL"] else t for t in miei["Ticker"].unique()]
        p_live = yf.download(u_tickers, period="1d", progress=False)['Close'].iloc[-1]
        tot_inv = miei["Totale"].sum()
        val_att = 0
        for _, r in miei.iterrows():
            tk = f"{r['Ticker']}-USD" if r['Ticker'] in ["BTC", "ETH", "SOL"] else r['Ticker']
            pr = p_live[tk] if len(u_tickers) > 1 else p_live
            val_att += pr * r["Quantità"]
        c1, c2, c3 = st.columns(3)
        c1.metric(L['port_inv'], f"{tot_inv:.2f} $")
        c2.metric(L['port_val'], f"{val_att:.2f} $", delta=f"{val_att-tot_inv:.2f} $")
        c3.metric(f"Total ROI %", f"{((val_att/tot_inv)-1)*100:.2f}%")

    # Grafico v9.0
    data = yf.download(t_sym, period="1y", auto_adjust=True, progress=False)
    if not data.empty:
        df = data.copy()
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        st.header(f"📈 {t_sym} Analytical Feed")
        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
        fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        # News & Chat v9.0
        cn, cc = st.columns([0.4, 0.6])
        with cn:
            st.subheader(f"📰 {L['news_title']}")
            news = get_cached_news(t_search)
            for n in news: st.markdown(f"[{n['t']}]({n['l']})")
        with cc:
            st.subheader(f"💬 {L['chat_title']}")
            if 'msgs' not in st.session_state: st.session_state.msgs = []
            for m in st.session_state.msgs:
                with st.chat_message(m["role"]): st.markdown(m["content"])
            if inp := st.chat_input("Tactical question..."):
                st.session_state.msgs.append({"role": "user", "content": inp})
                with st.chat_message("user"): st.markdown(inp)
                with st.chat_message("assistant"):
                    ctx = f"Ticker {t_sym}, Price {df['Close'].iloc[-1]:.2f}, RSI {df['RSI'].iloc[-1]:.1f}, Invested {tot_inv}$"
                    res = get_ai_chat_response(inp, ctx, st.session_state.lang)
                    st.markdown(res)
                    st.session_state.msgs.append({"role": "assistant", "content": res})
