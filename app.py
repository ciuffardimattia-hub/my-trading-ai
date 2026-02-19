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
import re

# --- 1. CONFIGURAZIONE & STYLE CYBERPUNK ---
st.set_page_config(page_title="CyberTrading AI v8.6", layout="wide", page_icon="⚡")

st.markdown("""
    <style>
    /* Sfondo e Testi */
    .stApp { background-color: #050505; color: #00ff41; }
    
    /* Card Metriche */
    div[data-testid="stMetric"] { 
        background: rgba(20, 20, 20, 0.8); 
        border: 1px solid #00ff41; 
        padding: 15px; 
        border-radius: 10px; 
        box-shadow: 0 0 10px #00ff41;
    }
    
    /* Bottoni Neon */
    .stButton>button { 
        background-color: #ff00ff !important; 
        color: white !important; 
        border: none; 
        box-shadow: 0 0 15px #ff00ff; 
        font-weight: bold;
    }
    
    /* Input personalizzati */
    .stTextInput>div>div>input { color: #ff00ff !important; font-family: 'Courier New', Courier, monospace; }
    
    /* Divider Neon */
    hr { border: 1px solid #00ff41; box-shadow: 0 0 5px #00ff41; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNZIONI DI SICUREZZA ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

# --- 3. MOTORE NOTIZIE ---
def get_advanced_news(symbol):
    news_items = []
    seen = set()
    q = symbol.replace("-USD", "")
    for timeframe in ["1d", "7d"]:
        url = f"https://news.google.com/rss/search?q={q}+stock+news+when:{timeframe}&hl=it&gl=IT&ceid=IT:it"
        try:
            resp = requests.get(url, timeout=5)
            root = ET.fromstring(resp.content)
            for item in root.findall('.//item')[:5]:
                title = item.find('title').text
                if title and title not in seen and len(title) > 20:
                    news_items.append({
                        't': title, 's': item.find('source').text,
                        'l': item.find('link').text, 'd': item.find('pubDate').text[:16],
                        'p': "RECENTE" if timeframe == "1d" else "SETTIMANALE"
                    })
                    seen.add(title)
            if news_items and timeframe == "1d": break
        except: continue
    return news_items

# --- 4. CONNESSIONE DATABASE (GOOGLE SHEETS) ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carica_tabella(nome_foglio):
    try:
        return conn.read(worksheet=nome_foglio, ttl=0)
    except:
        if nome_foglio == "Utenti": return pd.DataFrame(columns=["Email", "Password"])
        return pd.DataFrame(columns=["Email", "Ticker", "Prezzo", "Quantità", "Totale", "Data"])

# --- 5. LOGICA CHAT IA (AUTO-SCANNER) ---
def get_ai_chat_response(prompt, context):
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key: return "⚠️ Chiave GEMINI_API_KEY non trovata nei Secrets."
        
        genai.configure(api_key=api_key)
        
        # Scanner dei modelli disponibili
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        if not available_models:
            return "❌ Nessun modello disponibile per questa API Key. Verifica su Google AI Studio."

        # Selezione automatica del modello migliore
        selected_model = ""
        # Cerchiamo i modelli in ordine di preferenza
        for pref in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']:
            if pref in available_models:
                selected_model = pref
                break
        
        if not selected_model: selected_model = available_models[0]

        model = genai.GenerativeModel(selected_model)
        full_p = f"Sei un assistente trading Cyberpunk. Contesto dati: {context}. Rispondi in italiano alla domanda: {prompt}"
        response = model.generate_content(full_p)
        
        return f"**[AI Node: {selected_model}]**\n\n{response.text}"

    except Exception as e:
        return f"❌ Errore critico: {str(e)}\n\nConsiglio: Crea una nuova API Key su Google AI Studio."

# --- 6. ACCESSO (LOGIN / REGISTRAZIONE) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""

if not st.session_state.logged_in:
    st.title("📟 CyberLink Access")
    t1, t2 = st.tabs(["🔐 LOGIN", "📝 REGISTRAZIONE"])
    
    with t1:
        email = st.text_input("Inserisci Email").lower()
        pwd = st.text_input("Inserisci Password", type="password")
        if st.button("AUTENTICAZIONE"):
            df_u = carica_tabella("Utenti")
            user_row = df_u[df_u["Email"] == email]
            if not user_row.empty and check_hashes(pwd, user_row["Password"].values[0]):
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.rerun()
            else: st.error("Accesso negato: credenziali non valide.")
            
    with t2:
        new_e = st.text_input("Nuova Email").lower()
        new_p = st.text_input("Nuova Password", type="password")
        if st.button("CREA NUOVO NODO"):
            df_u = carica_tabella("Utenti")
            if new_e in df_u["Email"].values:
                st.warning("Email già registrata nel sistema.")
            elif "@" in new_e and len(new_p) > 3:
                nuovo_u = pd.DataFrame([{"Email": new_e, "Password": make_hashes(new_p)}])
                conn.update(worksheet="Utenti", data=pd.concat([df_u, nuovo_u], ignore_index=True))
                st.success("Account creato! Procedi al Login.")
            else: st.error("Email o password non valide.")
    st.stop()

# --- 7. DASHBOARD OPERATIVA ---
# Panorama Mercati (Home)
st.markdown("### 🌍 Panorama Mercati")
indices = {"^GSPC": "S&P 500", "BTC-USD": "Bitcoin", "GC=F": "Oro", "NVDA": "Nvidia", "TSLA": "Tesla"}
cols = st.columns(len(indices))
for i, (sym, name) in enumerate(indices.items()):
    try:
        d = yf.Ticker(sym).history(period="2d")
        v = d['Close'].iloc[-1]
        cols[i].metric(name, f"{v:.2f}")
    except: pass

st.divider()

# Sidebar Setup
st.sidebar.title(f"👾 User: {st.session_state.user_email}")
ticker_search = st.sidebar.text_input("🔍 Cerca Titolo", "NVDA").upper()
ticker_sym = f"{ticker_search}-USD" if ticker_search in ["BTC", "ETH", "SOL"] else ticker_search

with st.sidebar.container(border=True):
    st.subheader("💾 Gestione Portafoglio")
    pr_acq = st.sidebar.number_input("Prezzo Carico ($)", min_value=0.0)
    qt_acq = st.sidebar.number_input("Quantità Totale", min_value=0.0)
    if st.sidebar.button("INVIA AL CLOUD"):
        db_p = carica_tabella("Portafoglio")
        nuova_op = pd.DataFrame([{
            "Email": st.session_state.user_email, "Ticker": ticker_search, 
            "Prezzo": pr_acq, "Quantità": qt_acq, 
            "Totale": pr_acq * qt_acq, "Data": str(pd.Timestamp.now().date())
        }])
        conn.update(worksheet="Portafoglio", data=pd.concat([db_p, nuova_op], ignore_index=True))
        st.sidebar.success("Database Sincronizzato!")

if st.sidebar.button("🚪 LOGOUT"):
    st.session_state.logged_in = False
    st.rerun()

# --- ANALISI, GRAFICI E CHAT ---
try:
    data = yf.download(ticker_sym, period="1y", interval="1d", auto_adjust=True)
    if not data.empty:
        df = data.copy()
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        df['SMA20'] = ta.sma(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        last_price = float(df['Close'].iloc[-1])
        
        st.header(f"🚀 {ticker_sym} Tactical Feed")

        # Metriche Portafoglio Personale
        db_p = carica_tabella("Portafoglio")
        miei = db_p[(db_p["Email"] == st.session_state.user_email) & (db_p["Ticker"] == ticker_search)]
        p_info_ai = "Nessuna posizione salvata."
        if not miei.empty:
            tot_q = miei["Quantità"].sum()
            pmc = miei["Totale"].sum() / tot_q
            pl = ((last_price - pmc) / pmc) * 100
            m1, m2, m3 = st.columns(3)
            m1.metric("Tuo PMC", f"{pmc:.2f} $")
            m2.metric("Quantità", f"{tot_q:.1f}")
            m3.metric("P&L Netto", f"{pl:.2f}%", delta=f"{pl:.2f}%")
            p_info_ai = f"L'utente possiede {tot_q} quote a un prezzo medio di {pmc:.2f} $."

        # Grafico Candele + RSI
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Market"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], name="SMA 20", line=dict(color='orange')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='magenta')), row=2, col=1)
        fig.update_layout(height=550, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        

        st.divider()
        col_news, col_chat = st.columns([0.5, 0.5])
        
        with col_news:
            st.subheader("📰 Data Stream (Notizie)")
            notizie = get_advanced_news(ticker_search)
            news_context = ""
            if notizie:
                for n in notizie:
                    news_context += f"- {n['t']}\n"
                    with st.container(border=True):
                        st.markdown(f"**{n['p']}** | [{n['t']}]({n['l']})")
                        st.caption(f"Source: {n['s']}")
            else: st.warning("Nessuna notizia rilevata nel settore.")

        with col_chat:
            st.subheader("💬 Tactical AI Advisor")
            if 'messages' not in st.session_state: st.session_state.messages = []
            
            for m in st.session_state.messages:
                with st.chat_message(m["role"]): st.markdown(m["content"])
            
            if chat_input := st.chat_input("Invia comando all'IA..."):
                st.session_state.messages.append({"role": "user", "content": chat_input})
                with st.chat_message("user"): st.markdown(chat_input)
                
                with st.chat_message("assistant"):
                    context_full = f"Ticker {ticker_sym}, Prezzo {last_price}, RSI {df['RSI'].iloc[-1]:.1f}. News: {news_context}. {p_info_ai}"
                    ai_response = get_ai_chat_response(chat_input, context_full)
                    st.markdown(ai_response)
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})

except Exception as e: st.error(f"Errore di sistema: {e}")
