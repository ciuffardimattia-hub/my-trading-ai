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
st.set_page_config(page_title="CyberTrading Hub v9.1", layout="wide", page_icon="⚡")

st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #00ff41; }
    
    /* Hero Section */
    .hero-title {
        font-size: clamp(40px, 8vw, 70px); font-weight: 800; text-align: center;
        background: -webkit-linear-gradient(#00ff41, #ff00ff);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-top: 30px; margin-bottom: 0px;
    }
    
    /* Box Spiegazione Centrale */
    .about-section {
        background: rgba(10, 10, 10, 0.8);
        border-left: 5px solid #ff00ff;
        padding: 30px;
        margin: 40px auto;
        max-width: 900px;
        border-radius: 0 15px 15px 0;
        line-height: 1.6;
        box-shadow: 10px 10px 30px rgba(0,0,0,0.5);
    }
    
    .feature-card {
        background: rgba(20, 20, 20, 0.9); border: 1px solid #00ff41;
        padding: 25px; border-radius: 15px; text-align: center;
        height: 100%; transition: 0.3s;
    }
    .feature-card:hover { border-color: #ff00ff; box-shadow: 0 0 20px rgba(255, 0, 255, 0.4); }
    
    .stButton>button { 
        background: linear-gradient(45deg, #ff00ff, #00ff41) !important;
        color: white !important; font-weight: bold; border: none; border-radius: 30px;
        padding: 20px 40px !important; font-size: 1.2rem !important;
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
        system_instruction = f"Sei 'CYBER-ANALYST v9.1'. Analista mercati senior. Dati: {context}. Rispondi in italiano con tono cyberpunk."
        response = model.generate_content([system_instruction, prompt])
        return f"**[AI Node: {selected_model}]**\n\n{response.text}"
    except Exception as e: return f"❌ Errore IA: {e}"

# --- 3. GESTIONE NAVIGAZIONE ---
if 'page' not in st.session_state: st.session_state.page = "landing"
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 4. LANDING PAGE (VETRINA) ---
if st.session_state.page == "landing" and not st.session_state.logged_in:
    st.markdown("<div class='hero-title'>CYBERTRADING HUB</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888; font-size: 1.2rem;'>Advanced Financial Intelligence Terminal</p>", unsafe_allow_html=True)
    
    # --- SEZIONE SPIEGAZIONE ---
    st.markdown(f"""
    <div class='about-section'>
        <h2 style='color: #00ff41; margin-top:0;'>Cos'è CyberTrading Hub?</h2>
        <p style='color: #eee; font-size: 1.1rem;'>
            Benvenuto nel futuro dell'analisi finanziaria. <b>CyberTrading Hub</b> non è solo un visualizzatore di grafici, 
            ma un ecosistema intelligente progettato per darti un vantaggio competitivo sui mercati. 
            <br><br>
            A differenza delle piattaforme tradizionali, il nostro sistema utilizza l'<b>Intelligenza Artificiale Generativa</b> 
            per incrociare i dati live di mercato (RSI, Medie Mobili, News) con la tua specifica situazione patrimoniale. 
            L'IA non analizza solo il titolo, ma analizza la <b>TUA posizione</b>, aiutandoti a decidere quando mediare il prezzo, 
            quando prendere profitto o quando proteggere il capitale.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='feature-card'><h3>🧠 IA Tattica</h3><p>L'intelligenza Gemini analizza trend e volatilità fornendoti report immediati basati su indicatori tecnici reali.</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='feature-card'><h3>💼 Cloud Vault</h3><p>Monitora il valore totale del tuo patrimonio. I tuoi acquisti sono salvati in sicurezza e accessibili da ogni dispositivo.</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='feature-card'><h3>⚡ Real-Time Data</h3><p>Connessione diretta ai database finanziari globali per prezzi, candele e notizie dell'ultima ora senza ritardi.</p></div>", unsafe_allow_html=True)
    
    st.write("##")
    st.write("##")
    col_btn, _ = st.columns([1, 1])
    with col_btn:
        if st.button("ACCEDI AL TERMINALE OPERATIVO"):
            st.session_state.page = "auth"
            st.rerun()

# --- 5. AUTH & DASHBOARD (RESTO DEL CODICE INVARIATO) ---
elif st.session_state.page == "auth" and not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>🔐 Accesso al Nodo</h2>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["LOGIN", "REGISTRAZIONE"])
    with t1:
        e = st.text_input("Email").lower()
        p = st.text_input("Password", type="password")
        if st.button("AVVIA"):
            df_u = conn.read(worksheet="Utenti", ttl=0)
            u = df_u[df_u["Email"] == e]
            if not u.empty and check_hashes(p, u["Password"].values[0]):
                st.session_state.logged_in = True
                st.session_state.user_email = e
                st.rerun()
            else: st.error("Errore.")
    with t2:
        ne = st.text_input("Nuova Email").lower()
        np = st.text_input("Nuova Password", type="password")
        if st.button("CREA"):
            df_u = conn.read(worksheet="Utenti", ttl=0)
            if ne in df_u["Email"].values: st.warning("Esistente.")
            elif "@" in ne:
                nu = pd.DataFrame([{"Email": ne, "Password": make_hashes(np)}])
                conn.update(worksheet="Utenti", data=pd.concat([df_u, nu], ignore_index=True))
                st.success("Fatto!")
    if st.button("← Indietro"):
        st.session_state.page = "landing"
        st.rerun()

elif st.session_state.logged_in:
    # --- DASHBOARD CUORE ---
    st.sidebar.title(f"👾 {st.session_state.user_email}")
    t_search = st.sidebar.text_input("🔍 Ticker", "NVDA").upper()
    t_sym = f"{t_search}-USD" if t_search in ["BTC", "ETH", "SOL"] else t_search
    
    if st.sidebar.button("🚪 LOGOUT"):
        st.session_state.logged_in = False
        st.session_state.page = "landing"
        st.rerun()

    # Logica Mercati & Patrimonio (v8.9)
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
        st.subheader("📊 Performance Patrimonio")
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
        c3.metric("Profitto Totale %", f"{((val_att/tot_inv)-1)*100:.2f}%")
    
    # Analisi Tecnica & Chat
    data = yf.download(t_sym, period="1y", auto_adjust=True, progress=False)
    if not data.empty:
        df = data.copy()
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        st.header(f"📈 {t_sym}")
        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
        fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

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
