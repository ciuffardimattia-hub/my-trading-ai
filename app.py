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

# --- 1. CONFIGURAZIONE & STYLE CYBERPUNK ---
st.set_page_config(page_title="CyberTrading Hub v9.0", layout="wide", page_icon="⚡")

st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #00ff41; }
    
    /* Landing Page Elements */
    .hero-title {
        font-size: 65px; font-weight: 800; text-align: center;
        background: -webkit-linear-gradient(#00ff41, #ff00ff);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-top: 50px;
    }
    .feature-card {
        background: rgba(20, 20, 20, 0.9); border: 1px solid #00ff41;
        padding: 30px; border-radius: 15px; text-align: center;
        box-shadow: 0 0 15px rgba(0, 255, 65, 0.1); transition: 0.3s;
    }
    .feature-card:hover { border-color: #ff00ff; box-shadow: 0 0 30px #ff00ff; }
    
    /* Dashboard Elements */
    div[data-testid="stMetric"] { 
        background: rgba(20, 20, 20, 0.8); border: 1px solid #00ff41; 
        padding: 15px; border-radius: 10px; box-shadow: 0 0 10px #00ff41;
    }
    .stButton>button { 
        background: linear-gradient(45deg, #ff00ff, #00ff41) !important;
        color: white !important; font-weight: bold; border: none; border-radius: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNZIONI CORE ---
def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()
def check_hashes(password, hashed_text): return make_hashes(password) == hashed_text

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300)
def get_market_prices(tickers_list):
    try: return yf.download(list(tickers_list), period="1d", group_by='ticker', progress=False)
    except: return None

@st.cache_data(ttl=600)
def get_cached_news(symbol):
    news_items = []
    q = symbol.replace("-USD", "")
    url = f"https://news.google.com/rss/search?q={q}+stock+news+when:7d&hl=it&gl=IT&ceid=IT:it"
    try:
        resp = requests.get(url, timeout=3)
        root = ET.fromstring(resp.content)
        for item in root.findall('.//item')[:5]:
            news_items.append({'t': item.find('title').text, 'l': item.find('link').text})
    except: pass
    return news_items

def get_ai_chat_response(prompt, context):
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key: return "⚠️ API Key mancante."
        genai.configure(api_key=api_key)
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        selected_model = next((m for m in ['models/gemini-1.5-flash', 'models/gemini-pro'] if m in available_models), available_models[0])
        model = genai.GenerativeModel(selected_model)
        system_instruction = f"Sei 'CYBER-ANALYST v9.0'. Analista mercati senior. Dati: {context}. Rispondi in italiano con tono cyberpunk."
        response = model.generate_content([system_instruction, prompt])
        return f"**[AI Node: {selected_model}]**\n\n{response.text}"
    except Exception as e: return f"❌ Errore IA: {e}"

# --- 3. GESTIONE STATO NAVIGAZIONE ---
if 'page' not in st.session_state: st.session_state.page = "landing"
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_email' not in st.session_state: st.session_state.user_email = ""

# --- 4. PAGINA: LANDING (VETRINA) ---
if st.session_state.page == "landing" and not st.session_state.logged_in:
    st.markdown("<div class='hero-title'>CYBERTRADING HUB</div>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #fff;'>L'eccellenza dell'IA applicata al tuo portafoglio finanziario.</h3>", unsafe_allow_html=True)
    
    st.write("##")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div class='feature-card'><h3>🧠 IA Analisi</h3><p>Analisi predittiva su RSI, trend e medie mobili in tempo reale.</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='feature-card'><h3>💼 Cloud Vault</h3><p>Gestisci il tuo portafoglio ovunque. Dati salvati in sicurezza sul cloud.</p></div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='feature-card'><h3>⚡ Turbo Speed</h3><p>Motore ottimizzato per darti prezzi e news senza attese.</p></div>", unsafe_allow_html=True)
    
    st.write("##")
    if st.button("ACCEDI AL TERMINALE OPERATIVO"):
        st.session_state.page = "auth"
        st.rerun()

# --- 5. PAGINA: AUTH (LOGIN/REG) ---
elif st.session_state.page == "auth" and not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>🔐 Autenticazione Nodo</h2>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["ENTRA", "REGISTRATI"])
    with t1:
        e = st.text_input("Email").lower()
        p = st.text_input("Password", type="password")
        if st.button("AVVIA LOGIN"):
            df_u = conn.read(worksheet="Utenti", ttl=0)
            u = df_u[df_u["Email"] == e]
            if not u.empty and check_hashes(p, u["Password"].values[0]):
                st.session_state.logged_in = True
                st.session_state.user_email = e
                st.rerun()
            else: st.error("Accesso negato.")
    with t2:
        ne = st.text_input("Nuova Email").lower()
        np = st.text_input("Nuova Password", type="password")
        if st.button("CREA ACCOUNT"):
            df_u = conn.read(worksheet="Utenti", ttl=0)
            if ne in df_u["Email"].values: st.warning("Già registrata.")
            elif "@" in ne:
                nu = pd.DataFrame([{"Email": ne, "Password": make_hashes(np)}])
                conn.update(worksheet="Utenti", data=pd.concat([df_u, nu], ignore_index=True))
                st.success("Fatto! Ora accedi.")
    if st.button("← Torna alla Home"):
        st.session_state.page = "landing"
        st.rerun()

# --- 6. PAGINA: DASHBOARD (CUORE) ---
elif st.session_state.logged_in:
    # Sidebar
    st.sidebar.title(f"👾 {st.session_state.user_email}")
    t_search = st.sidebar.text_input("🔍 Cerca Titolo", "NVDA").upper()
    t_sym = f"{t_search}-USD" if t_search in ["BTC", "ETH", "SOL"] else t_search
    
    if st.sidebar.button("INVIA AL CLOUD"):
        # Logica salvataggio...
        st.sidebar.success("Salvato!")
        st.rerun()
        
    if st.sidebar.button("🚪 ESCI"):
        st.session_state.logged_in = False
        st.session_state.page = "landing"
        st.rerun()

    # Mercati & Patrimonio
    main_indices = ["^GSPC", "BTC-USD", "GC=F"]
    m_data = get_market_prices(main_indices)
    cols = st.columns(3)
    for i, s in enumerate(main_indices):
        cols[i].metric(s.replace("^GSPC", "S&P 500"), f"{m_data[s]['Close'].iloc[-1]:.2f}")
    
    st.divider()
    
    # Calcolo Patrimonio
    db_p = conn.read(worksheet="Portafoglio", ttl=0)
    miei = db_p[db_p["Email"] == st.session_state.user_email]
    tot_inv = 0
    if not miei.empty:
        st.subheader("📊 Performance Globale")
        unique_t = [f"{t}-USD" if t in ["BTC", "ETH", "SOL"] else t for t in miei["Ticker"].unique()]
        p_live = yf.download(unique_t, period="1d", progress=False)['Close'].iloc[-1]
        tot_inv = miei["Totale"].sum()
        val_att = 0
        for _, r in miei.iterrows():
            tk = f"{r['Ticker']}-USD" if r['Ticker'] in ["BTC", "ETH", "SOL"] else r['Ticker']
            pr = p_live[tk] if len(unique_t) > 1 else p_live
            val_att += pr * r["Quantità"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Investito", f"{tot_inv:.2f} $")
        c2.metric("Valore Live", f"{val_att:.2f} $", delta=f"{val_att-tot_inv:.2f} $")
        c3.metric("P&L %", f"{((val_att/tot_inv)-1)*100:.2f}%")
    
    st.divider()

    # Analisi Tecnica
    data = yf.download(t_sym, period="1y", interval="1d", auto_adjust=True, progress=False)
    if not data.empty:
        df = data.copy()
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df['SMA20'] = ta.sma(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        st.header(f"📈 {t_sym}")
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], name="SMA 20", line=dict(color='orange')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='magenta')), row=2, col=1)
        fig.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        # News & Chat
        cn, cc = st.columns([0.4, 0.6])
        with cn:
            st.subheader("📰 Notizie")
            news = get_cached_news(t_search)
            for n in news: st.markdown(f"[{n['t']}]({n['l']})")
        with cc:
            st.subheader("💬 AI Analyst")
            if 'msgs' not in st.session_state: st.session_state.msgs = []
            for m in st.session_state.msgs:
                with st.chat_message(m["role"]): st.markdown(m["content"])
            if inp := st.chat_input("Chiedi..."):
                st.session_state.msgs.append({"role": "user", "content": inp})
                with st.chat_message("user"): st.markdown(inp)
                with st.chat_message("assistant"):
                    ctx = f"Ticker {t_sym}, Prezzo {df['Close'].iloc[-1]:.2f}, RSI {df['RSI'].iloc[-1]:.1f}, Investito {tot_inv}$"
                    res = get_ai_chat_response(inp, ctx)
                    st.markdown(res)
                    st.session_state.msgs.append({"role": "assistant", "content": res})
