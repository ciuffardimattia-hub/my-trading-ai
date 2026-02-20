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

# --- 1. CONFIGURAZIONE & STYLE ---
st.set_page_config(page_title="CyberTrading Hub v9.9.1", layout="wide", page_icon="⚡")

LANGUAGES = {
    "IT": {
        "hero_t": "CYBERTRADING HUB", "hero_s": "L'intelligenza artificiale al servizio del tuo patrimonio.",
        "about_h": "Perché scegliere CyberTrading Hub?",
        "about_p": "In un mercato dominato dagli algoritmi, l'investitore retail ha bisogno di strumenti avanzati. Il nostro Hub fonde i dati live con la potenza di Google Gemini per darti un analista privato 24/7.",
        "feat_ia": "Analisi Tattica IA", "feat_ia_p": "Segnali basati su RSI e SMA20.",
        "feat_cloud": "Portfolio Criptato", "feat_cloud_p": "Dati salvati su cloud sicuri.",
        "feat_turbo": "Dati in Tempo Reale", "feat_turbo_p": "Connessione diretta ai mercati mondiali.",
        "btn_enter": "ENTRA NEL TERMINALE", "btn_login": "ACCEDI", "btn_reg": "REGISTRATI",
        "btn_back": "← Indietro", "btn_logout": "ESCI", "sidebar_search": "Cerca Titolo",
        "side_save_op": "Salva Operazione", "side_price": "Prezzo ($)", "side_qty": "Quantità", "side_btn_save": "SALVA", "side_success": "Salvato!",
        "chat_title": "AI Tactical Advisor", "news_title": "Data Stream News", "auth_title": "Autenticazione Nodo"
    },
    "EN": {
        "hero_t": "CYBERTRADING HUB", "hero_s": "AI at the service of your assets.",
        "about_h": "Why choose CyberTrading Hub?",
        "about_p": "Our Hub merges live data with Google Gemini power to give you a 24/7 private analyst.",
        "feat_ia": "AI Tactical Analysis", "feat_ia_p": "Signals based on RSI and SMA20.",
        "feat_cloud": "Encrypted Portfolio", "feat_cloud_p": "Data saved on secure clouds.",
        "feat_turbo": "Real-Time Data", "feat_turbo_p": "Direct connection to global markets.",
        "btn_enter": "ENTER TERMINAL", "btn_login": "LOGIN", "btn_reg": "REGISTER",
        "btn_back": "← Back", "btn_logout": "LOGOUT", "sidebar_search": "Search Ticker",
        "side_save_op": "Save Trade", "side_price": "Price ($)", "side_qty": "Quantity", "side_btn_save": "SAVE", "side_success": "Saved!",
        "chat_title": "AI Tactical Advisor", "news_title": "News Feed", "auth_title": "Node Authentication"
    },
    "ES": {
        "hero_t": "CYBERTRADING HUB", "hero_s": "IA al servicio de su patrimonio.",
        "about_h": "¿Por qué elegir CyberTrading Hub?",
        "about_p": "Nuestro Hub fusiona datos en vivo con la potencia de Google Gemini.",
        "feat_ia": "Análisis Táctico IA", "feat_ia_p": "Señales basadas en RSI y SMA20.",
        "feat_cloud": "Cartera Criptografiada", "feat_cloud_p": "Datos guardados en nubes seguras.",
        "feat_turbo": "Datos en Tiempo Real", "feat_turbo_p": "Conexión directa a mercados globales.",
        "btn_enter": "ENTRAR", "btn_login": "CONECTAR", "btn_reg": "REGISTRAR",
        "btn_back": "← Volver", "btn_logout": "SALIR", "sidebar_search": "Buscar Ticker",
        "side_save_op": "Guardar Op", "side_price": "Precio ($)", "side_qty": "Cant", "side_btn_save": "GUARDAR", "side_success": "¡Guardado!",
        "chat_title": "Asesor IA", "news_title": "Noticias", "auth_title": "Autenticación"
    }
}

st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #00ff41; }
    .hero-title { font-size: clamp(40px, 8vw, 70px); font-weight: 800; text-align: center; background: -webkit-linear-gradient(#00ff41, #ff00ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-top: 20px; }
    .about-section { background: rgba(10, 10, 10, 0.9); border-left: 5px solid #ff00ff; padding: 25px; margin: 30px auto; max-width: 950px; border-radius: 0 15px 15px 0; }
    div[data-testid="stMetric"] { background: rgba(20, 20, 20, 0.8); border: 1px solid #00ff41; border-radius: 10px; padding: 10px; box-shadow: 0 0 5px rgba(0,255,65,0.2); }
    .stButton>button { background: linear-gradient(45deg, #ff00ff, #00ff41) !important; color: white !important; font-weight: bold; border-radius: 30px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GESTIONE STATO ---
if 'lang' not in st.session_state: st.session_state.lang = "IT"
if 'page' not in st.session_state: st.session_state.page = "landing"
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
L = LANGUAGES[st.session_state.lang]

# --- 3. FUNZIONI CORE ---
def make_hashes(p): return hashlib.sha256(str.encode(p)).hexdigest()
def check_hashes(p, h): return make_hashes(p) == h
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300)
def get_market_prices(tickers_list):
    try:
        # Scarichiamo 5 giorni per essere sicuri di avere dati anche se è domenica
        df = yf.download(tickers_list, period="5d", group_by='ticker', progress=False)
        return df
    except: return None

@st.cache_data(ttl=600)
def get_cached_news(symbol):
    news = []
    q = symbol.replace("-USD", "")
    url = f"https://news.google.com/rss/search?q={q}+stock+news+when:7d&hl=it&gl=IT&ceid=IT:it"
    try:
        r = requests.get(url, timeout=4)
        root = ET.fromstring(r.content)
        for i in root.findall('.//item')[:5]:
            news.append({'t': i.find('title').text, 'l': i.find('link').text})
    except: pass
    return news

def get_ai_chat_response(prompt, context, lang):
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key: return "API Key Error."
        genai.configure(api_key=api_key)
        model_list = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        selected_model = "models/gemini-1.5-flash"
        if "models/gemini-1.5-flash" not in model_list: selected_model = model_list[0]
        model = genai.GenerativeModel(selected_model)
        
        sys_i = f"Role: Senior Financial Analyst v9.9.1. Context: {context}. Respond in {lang}. Use technical financial jargon."
        res = model.generate_content([sys_i, prompt])
        return res.text
    except Exception as e: return f"AI Error: {str(e)}"

# --- 4. LANDING PAGE ---
if st.session_state.page == "landing" and not st.session_state.logged_in:
    st.session_state.lang = st.selectbox("🌐", ["IT", "EN", "ES"], index=["IT", "EN", "ES"].index(st.session_state.lang))
    st.markdown(f"<div class='hero-title'>{L['hero_t']}</div>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #888;'>{L['hero_s']}</p>", unsafe_allow_html=True)
    st.markdown(f"<div class='about-section'><h2>{L['about_h']}</h2><p>{L['about_p']}</p></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div style='border:1px solid #00ff41; padding:20px; border-radius:15px; text-align:center;'><h3>{L['feat_ia']}</h3><p>{L['feat_ia_p']}</p></div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='border:1px solid #ff00ff; padding:20px; border-radius:15px; text-align:center;'><h3>{L['feat_cloud']}</h3><p>{L['feat_cloud_p']}</p></div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='border:1px solid #00ff41; padding:20px; border-radius:15px; text-align:center;'><h3>{L['feat_turbo']}</h3><p>{L['feat_turbo_p']}</p></div>", unsafe_allow_html=True)
    st.write("##")
    if st.button(L['btn_enter']): st.session_state.page = "auth"; st.rerun()

# --- 5. AUTH ---
elif st.session_state.page == "auth" and not st.session_state.logged_in:
    st.markdown(f"<h2 style='text-align: center; color: #ff00ff;'>{L['auth_title']}</h2>", unsafe_allow_html=True)
    t1, t2 = st.tabs([L['btn_login'], L['btn_reg']])
    with t1:
        e = st.text_input("Email").lower()
        p = st.text_input("Password", type="password")
        if st.button(L['btn_login']):
            df_u = conn.read(worksheet="Utenti", ttl=0)
            u = df_u[df_u["Email"] == e]
            if not u.empty and check_hashes(p, u["Password"].values[0]):
                st.session_state.logged_in, st.session_state.user_email = True, e; st.rerun()
    if st.button(L['btn_back']): st.session_state.page = "landing"; st.rerun()

# --- 6. DASHBOARD ---
elif st.session_state.logged_in:
    # Sidebar
    st.sidebar.title(f"👾 Hub: {st.session_state.user_email}")
    st.session_state.lang = st.sidebar.selectbox("🌐", ["IT", "EN", "ES"], index=["IT", "EN", "ES"].index(st.session_state.lang))
    t_search = st.sidebar.text_input(L['sidebar_search'], "BTC").upper()
    t_sym = f"{t_search}-USD" if t_search in ["BTC", "ETH", "SOL"] else t_search
    
    # Input Portafoglio
    db_p = conn.read(worksheet="Portafoglio", ttl=0)
    with st.sidebar.container(border=True):
        st.subheader(f"💾 {L['side_save_op']}")
        p_acq = st.sidebar.number_input(L['side_price'], min_value=0.0)
        q_acq = st.sidebar.number_input(L['side_qty'], min_value=0.0)
        if st.sidebar.button(L['side_btn_save']):
            nuova_op = pd.DataFrame([{"Email": st.session_state.user_email, "Ticker": t_search, "Prezzo": p_acq, "Quantità": q_acq, "Totale": p_acq * q_acq, "Data": str(pd.Timestamp.now().date())}])
            conn.update(worksheet="Portafoglio", data=pd.concat([db_p, nuova_op], ignore_index=True))
            st.sidebar.success(L['side_success']); st.rerun()
            
    if st.sidebar.button(L['btn_logout']): st.session_state.logged_in = False; st.rerun()

    # --- TOP MARKET BAR (FIXED & EXPANDED) ---
    # Definiamo i ticker richiesti e i nomi visuali
    tickers_map = {
        "BTC-USD": "Bitcoin",
        "GC=F": "Gold",
        "^IXIC": "Nasdaq",
        "^GSPC": "S&P 500",
        "NVDA": "Nvidia",
        "TSLA": "Tesla"
    }
    
    # Scarico dati sicuri
    m_data = get_market_prices(list(tickers_map.keys()))
    
    # Creiamo 6 colonne per i 6 ticker
    cols = st.columns(6)
    
    for i, (sym, name) in enumerate(tickers_map.items()):
        try:
            # FIX NAN: Prendo l'ultimo valore non nullo disponibile (.dropna().iloc[-1])
            if m_data is not None and not m_data.empty:
                # Gestione struttura dati yfinance (MultiIndex vs SingleIndex)
                if isinstance(m_data.columns, pd.MultiIndex):
                    val = m_data[sym]['Close'].dropna().iloc[-1]
                else:
                    # Fallback se c'è un solo ticker (raro qui, ma sicuro)
                    val = m_data['Close'].dropna().iloc[-1]
                cols[i].metric(name, f"{val:.2f}")
            else:
                cols[i].metric(name, "Loading...")
        except:
            cols[i].metric(name, "N/A")

    st.divider()

    # Calcolo Patrimonio Invisibile (per IA)
    miei = db_p[db_p["Email"] == st.session_state.user_email]
    tot_inv = miei["Totale"].sum() if not miei.empty else 0

    # Grafico & Chat
    data = yf.download(t_sym, period="1y", interval="1d", auto_adjust=True, progress=False)
    if not data.empty:
        df = data.copy()
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df['SMA20'] = ta.sma(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        st.header(f"📈 {t_sym} Analytical Feed")
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], name="SMA 20", line=dict(color='orange', width=2)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='magenta', width=2)), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="cyan", row=2, col=1)
        fig.update_layout(template="plotly_dark", height=550, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

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
            if inp := st.chat_input("Command AI..."):
                st.session_state.msgs.append({"role": "user", "content": inp})
                with st.chat_message("user"): st.markdown(inp)
                with st.chat_message("assistant"):
                    ctx = f"Ticker {t_sym}, Price {df['Close'].iloc[-1]:.2f}, RSI {df['RSI'].iloc[-1]:.1f}, SMA20 {df['SMA20'].iloc[-1]:.1f}, Portfolio_Invested_Total {tot_inv}$"
                    res = get_ai_chat_response(inp, ctx, st.session_state.lang)
                    st.markdown(res)
                    st.session_state.msgs.append({"role": "assistant", "content": res})
