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
st.set_page_config(page_title="CyberTrading Turbo v8.9", layout="wide", page_icon="⚡")

st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #00ff41; }
    div[data-testid="stMetric"] { 
        background: rgba(20, 20, 20, 0.8); border: 1px solid #00ff41; 
        padding: 15px; border-radius: 10px; box-shadow: 0 0 10px #00ff41;
    }
    .stButton>button { 
        background-color: #ff00ff !important; color: white !important; 
        border: none; box-shadow: 0 0 15px #ff00ff; font-weight: bold;
    }
    .stTextInput>div>div>input { color: #ff00ff !important; font-family: 'Courier New', monospace; }
    hr { border: 1px solid #00ff41; box-shadow: 0 0 5px #00ff41; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNZIONI CACHED (VELOCIZZAZIONE) ---
@st.cache_data(ttl=300)
def get_market_prices(tickers_list):
    try:
        return yf.download(list(tickers_list), period="1d", group_by='ticker', progress=False)
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

# --- 3. SICUREZZA & DATABASE ---
def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()
def check_hashes(password, hashed_text): return make_hashes(password) == hashed_text

conn = st.connection("gsheets", type=GSheetsConnection)

def carica_tabella(nome):
    return conn.read(worksheet=nome, ttl=0)

# --- 4. CHAT IA (BRAIN v8.7 INTEGRATO) ---
def get_ai_chat_response(prompt, context):
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key: return "⚠️ Chiave mancante."
        genai.configure(api_key=api_key)
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        selected_model = next((m for m in ['models/gemini-1.5-flash', 'models/gemini-pro'] if m in available_models), available_models[0])
        model = genai.GenerativeModel(selected_model)
        system_instruction = f"""
        Sei 'CYBER-ANALYST v8.9'. Analista mercati senior. 
        Contesto dati: {context}. 
        REGOLE: RSI>70 Ipercomprato, RSI<30 Ipervenduto. Prezzo>SMA20 trend UP.
        Rispondi in italiano con tono professionale e cyberpunk.
        """
        response = model.generate_content([system_instruction, prompt])
        return f"**[AI Node: {selected_model}]**\n\n{response.text}"
    except Exception as e: return f"❌ Errore IA: {e}"

# --- 5. LOGICA ACCESSO ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""

if not st.session_state.logged_in:
    st.title("📟 CyberLink Access")
    t1, t2 = st.tabs(["🔐 LOGIN", "📝 REGISTRAZIONE"])
    with t1:
        e = st.text_input("Email").lower()
        p = st.text_input("Password", type="password")
        if st.button("AUTENTICAZIONE"):
            df_u = carica_tabella("Utenti")
            u = df_u[df_u["Email"] == e]
            if not u.empty and check_hashes(p, u["Password"].values[0]):
                st.session_state.logged_in = True
                st.session_state.user_email = e
                st.rerun()
            else: st.error("Accesso negato.")
    with t2:
        ne = st.text_input("Nuova Email").lower()
        np = st.text_input("Nuova Password", type="password")
        if st.button("CREA NODO"):
            df_u = carica_tabella("Utenti")
            if ne in df_u["Email"].values: st.warning("Esistente.")
            elif "@" in ne:
                nu = pd.DataFrame([{"Email": ne, "Password": make_hashes(np)}])
                conn.update(worksheet="Utenti", data=pd.concat([df_u, nu], ignore_index=True))
                st.success("Registrato! Fai il login.")
    st.stop()

# --- 6. DASHBOARD PRINCIPALE ---
st.markdown("### 🌍 Panorama Mercati")
main_indices = ["^GSPC", "BTC-USD", "GC=F", "NVDA"]
m_data = get_market_prices(main_indices)

cols = st.columns(len(main_indices))
for i, sym in enumerate(main_indices):
    try:
        val = m_data[sym]['Close'].iloc[-1] if len(main_indices)>1 else m_data['Close'].iloc[-1]
        cols[i].metric(sym.replace("^GSPC", "S&P 500"), f"{val:.2f}")
    except: pass

st.divider()

# RIEPILOGO PATRIMONIO (v8.8 INTEGRATO)
db_p = carica_tabella("Portafoglio")
miei_titoli = db_p[db_p["Email"] == st.session_state.user_email]

tot_investito = 0
if not miei_titoli.empty:
    st.subheader("📊 Performance Globale Patrimonio")
    unique_t = [f"{t}-USD" if t in ["BTC", "ETH", "SOL"] else t for t in miei_titoli["Ticker"].unique()]
    # Scarico prezzi attuali in blocco
    p_live = yf.download(unique_t, period="1d", progress=False)['Close'].iloc[-1]
    
    tot_investito = miei_titoli["Totale"].sum()
    valore_attuale_tot = 0
    
    for _, row in miei_titoli.iterrows():
        t_key = f"{row['Ticker']}-USD" if row['Ticker'] in ["BTC", "ETH", "SOL"] else row['Ticker']
        prezzo = p_live[t_key] if len(unique_t) > 1 else p_live
        valore_attuale_tot += prezzo * row["Quantità"]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Capitale Investito", f"{tot_investito:.2f} $")
    c2.metric("Valore Live", f"{valore_attuale_tot:.2f} $", delta=f"{valore_attuale_tot - tot_investito:.2f} $")
    c3.metric("P&L Globale", f"{((valore_attuale_tot/tot_investito)-1)*100:.2f}%")
else:
    st.info("Nessun titolo nel portafoglio cloud.")

st.divider()

# --- SIDEBAR & OPERAZIONI ---
st.sidebar.title(f"👾 {st.session_state.user_email}")
t_search = st.sidebar.text_input("🔍 Cerca Titolo", "AAPL").upper()
t_sym = f"{t_search}-USD" if t_search in ["BTC", "ETH", "SOL"] else t_search

with st.sidebar.container(border=True):
    st.subheader("💾 Salva Operazione")
    p_acq = st.sidebar.number_input("Prezzo Carico ($)", min_value=0.0)
    q_acq = st.sidebar.number_input("Quantità", min_value=0.0)
    if st.sidebar.button("INVIA AL CLOUD"):
        nuova = pd.DataFrame([{"Email": st.session_state.user_email, "Ticker": t_search, "Prezzo": p_acq, "Quantità": q_acq, "Totale": p_acq * q_acq, "Data": str(pd.Timestamp.now().date())}])
        conn.update(worksheet="Portafoglio", data=pd.concat([db_p, nuova], ignore_index=True))
        st.sidebar.success("Sincronizzato!")
        st.rerun()

if st.sidebar.button("🚪 LOGOUT"):
    st.session_state.logged_in = False
    st.rerun()

# --- ANALISI DETTAGLIATA ---
try:
    data = yf.download(t_sym, period="1y", interval="1d", auto_adjust=True, progress=False)
    if not data.empty:
        df = data.copy()
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df['SMA20'] = ta.sma(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        last_p = float(df['Close'].iloc[-1])
        
        st.header(f"📈 Analisi Tattica: {t_sym}")
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Market"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], name="SMA 20", line=dict(color='orange')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='magenta')), row=2, col=1)
        fig.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        col_n, col_c = st.columns([0.4, 0.6])
        with col_n:
            st.subheader("📰 Data Stream")
            news = get_cached_news(t_search)
            n_ctx = ""
            for n in news:
                n_ctx += f"- {n['t']}\n"
                st.markdown(f"[{n['t']}]({n['l']})")
        with col_c:
            st.subheader("💬 AI Tactical Advisor")
            if 'msgs' not in st.session_state: st.session_state.msgs = []
            for m in st.session_state.msgs:
                with st.chat_message(m["role"]): st.markdown(m["content"])
            
            if inp := st.chat_input("Comando..."):
                st.session_state.msgs.append({"role": "user", "content": inp})
                with st.chat_message("user"): st.markdown(inp)
                with st.chat_message("assistant"):
                    ctx = f"Ticker {t_sym}, Prezzo {last_p}, RSI {df['RSI'].iloc[-1]:.1f}, SMA20 {df['SMA20'].iloc[-1]:.1f}. News: {n_ctx}. Investito Totale: {tot_investito}$"
                    res = get_ai_chat_response(inp, ctx)
                    st.markdown(res)
                    st.session_state.msgs.append({"role": "assistant", "content": res})
except Exception as e: st.error(f"Sistema offline: {e}")
