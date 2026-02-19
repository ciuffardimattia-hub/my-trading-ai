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
st.set_page_config(page_title="CyberTrading AI v8.8", layout="wide", page_icon="⚡")

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
    .stTextInput>div>div>input { color: #ff00ff !important; font-family: 'Courier New', Courier, monospace; }
    hr { border: 1px solid #00ff41; box-shadow: 0 0 5px #00ff41; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNZIONI CORE ---
def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()
def check_hashes(password, hashed_text): return make_hashes(password) == hashed_text

def get_advanced_news(symbol):
    news_items = []
    q = symbol.replace("-USD", "")
    url = f"https://news.google.com/rss/search?q={q}+stock+news+when:7d&hl=it&gl=IT&ceid=IT:it"
    try:
        resp = requests.get(url, timeout=5)
        root = ET.fromstring(resp.content)
        for item in root.findall('.//item')[:5]:
            news_items.append({'t': item.find('title').text, 'l': item.find('link').text, 'p': "MARKET DATA"})
    except: pass
    return news_items

# --- 3. DATABASE ---
conn = st.connection("gsheets", type=GSheetsConnection)
def carica_tabella(nome):
    try: return conn.read(worksheet=nome, ttl=0)
    except:
        if nome == "Utenti": return pd.DataFrame(columns=["Email", "Password"])
        return pd.DataFrame(columns=["Email", "Ticker", "Prezzo", "Quantità", "Totale", "Data"])

# --- 4. CHAT IA ANALYST ---
def get_ai_chat_response(prompt, context):
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key: return "⚠️ Chiave mancante."
        genai.configure(api_key=api_key)
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        selected_model = next((m for m in ['models/gemini-1.5-flash', 'models/gemini-pro'] if m in available_models), available_models[0])
        model = genai.GenerativeModel(selected_model)
        system_instruction = f"Sei 'CYBER-ANALYST v8.8'. Analista mercati senior. Dati: {context}. Rispondi in italiano con tono cyberpunk."
        response = model.generate_content([system_instruction, prompt])
        return f"**[AI Node: {selected_model}]**\n\n{response.text}"
    except Exception as e: return f"❌ Errore IA: {e}"

# --- 5. ACCESSO ---
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
                st.success("Account creato!")
    st.stop()

# --- 6. DASHBOARD PRINCIPALE ---
st.markdown("### 🌍 Panorama Mercati")
indices = {"^GSPC": "S&P 500", "BTC-USD": "Bitcoin", "GC=F": "Oro", "NVDA": "Nvidia"}
cols = st.columns(len(indices))
for i, (sym, name) in enumerate(indices.items()):
    try:
        d = yf.Ticker(sym).history(period="2d")
        v = d['Close'].iloc[-1]
        cols[i].metric(name, f"{v:.2f}")
    except: pass

st.divider()

# --- 🚀 NUOVA DASHBOARD DI RIEPILOGO GLOBALE ---
st.subheader("📊 Il Tuo Patrimonio Cyber (Totale)")
db_full = carica_tabella("Portafoglio")
miei_titoli = db_full[db_full["Email"] == st.session_state.user_email]

if not miei_titoli.empty:
    # Calcolo Live
    tot_investito = miei_titoli["Totale"].sum()
    valore_attuale_tot = 0
    
    unique_tickers = miei_titoli["Ticker"].unique()
    # Recupero prezzi in blocco per velocità
    prezzi_live = {}
    for t in unique_tickers:
        try:
            tsym = f"{t}-USD" if t in ["BTC", "ETH", "SOL"] else t
            prezzi_live[t] = yf.Ticker(tsym).history(period="1d")['Close'].iloc[-1]
        except: prezzi_live[t] = 0
        
    for index, row in miei_titoli.iterrows():
        valore_attuale_tot += prezzi_live.get(row["Ticker"], 0) * row["Quantità"]
    
    profitto_tot = valore_attuale_tot - tot_investito
    perc_tot = (profitto_tot / tot_investito * 100) if tot_investito > 0 else 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Capitale Investito", f"{tot_investito:.2f} $")
    c2.metric("Valore di Mercato", f"{valore_attuale_tot:.2f} $", delta=f"{profitto_tot:.2f} $")
    c3.metric("Performance Globale", f"{perc_tot:.2f}%", delta=f"{perc_tot:.2f}%")
else:
    st.info("Aggiungi titoli nel portafoglio per vedere il riepilogo globale.")

st.divider()

# Sidebar
st.sidebar.title(f"👾 {st.session_state.user_email}")
t_search = st.sidebar.text_input("🔍 Cerca Titolo", "BTC").upper()
t_sym = f"{t_search}-USD" if t_search in ["BTC", "ETH", "SOL"] else t_search

with st.sidebar.container(border=True):
    st.subheader("💾 Operazione")
    p_acq = st.sidebar.number_input("Prezzo ($)", min_value=0.0)
    q_acq = st.sidebar.number_input("Quantità", min_value=0.0)
    if st.sidebar.button("INVIA AL CLOUD"):
        nuova = pd.DataFrame([{"Email": st.session_state.user_email, "Ticker": t_search, "Prezzo": p_acq, "Quantità": q_acq, "Totale": p_acq * q_acq, "Data": str(pd.Timestamp.now().date())}])
        conn.update(worksheet="Portafoglio", data=pd.concat([db_full, nuova], ignore_index=True))
        st.sidebar.success("Sincronizzato!")
        st.rerun()

if st.sidebar.button("🚪 LOGOUT"):
    st.session_state.logged_in = False
    st.rerun()

# Analisi Titolo Singolo
try:
    data = yf.download(t_sym, period="1y", interval="1d", auto_adjust=True)
    if not data.empty:
        df = data.copy()
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df['SMA20'] = ta.sma(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        last_p = float(df['Close'].iloc[-1])
        
        st.header(f"📈 Analisi Tattica: {t_sym}")
        
        # Grafico
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Market"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], name="SMA 20", line=dict(color='orange')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='magenta')), row=2, col=1)
        fig.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        cn, cc = st.columns([0.4, 0.6])
        with cn:
            st.subheader("📰 Data Stream")
            notizie = get_advanced_news(t_search)
            n_ctx = ""
            for n in notizie:
                n_ctx += f"- {n['t']}\n"
                st.markdown(f"[{n['t']}]({n['l']})")
        with cc:
            st.subheader("💬 AI Advisor")
            if 'msgs' not in st.session_state: st.session_state.msgs = []
            for m in st.session_state.msgs:
                with st.chat_message(m["role"]): st.markdown(m["content"])
            if inp := st.chat_input("Comando..."):
                st.session_state.msgs.append({"role": "user", "content": inp})
                with st.chat_message("user"): st.markdown(inp)
                with st.chat_message("assistant"):
                    ctx = f"Titolo {t_sym}, Prezzo {last_p}, RSI {df['RSI'].iloc[-1]:.1f}, Capitale Totale {tot_investito if not miei_titoli.empty else 0}$"
                    res = get_ai_chat_response(inp, ctx)
                    st.markdown(res)
                    st.session_state.msgs.append({"role": "assistant", "content": res})
except Exception as e: st.error(f"Sistema offline: {e}")
