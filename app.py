import streamlit as st
import google.generativeai as genai
import os
import json
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_gsheets import GSheetsConnection
import requests
import xml.etree.ElementTree as ET
import hashlib
import time

# --- HACK PER RENDER: AUTO-CREAZIONE SECRETS IN BACKGROUND ---
os.makedirs(".streamlit", exist_ok=True)
if not os.path.exists(".streamlit/secrets.toml"):
    creds = os.environ.get("GOOGLE_CREDENTIALS")
    url = os.environ.get("SPREADSHEET_URL")
    if creds and url:
        try:
            creds_dict = json.loads(creds)
            with open(".streamlit/secrets.toml", "w") as f:
                f.write("[connections.gsheets]\n")
                f.write(f'spreadsheet = "{url}"\n')
                f.write("[connections.gsheets.service_account]\n")
                for k, v in creds_dict.items():
                    v_escaped = str(v).replace('\n', '\\n')
                    f.write(f'{k} = "{v_escaped}"\n')
        except Exception as e:
            pass

# --- 1. CONFIGURAZIONE & STYLE ---
st.set_page_config(page_title="CyberTrading Hub v9.9.4", layout="wide", page_icon="⚡")

# NASCONDI I LOGHI DI STREAMLIT
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

LANGUAGES = {
    "IT": {
        "hero_t": "CYBERTRADING HUB", "hero_s": "L'intelligenza artificiale al servizio del tuo patrimonio.",
        "about_h": "Perché scegliere CyberTrading Hub?",
        "about_p": "In un mercato dominato dagli algoritmi, l'investitore retail ha bisogno di strumenti avanzati. Il nostro Hub fonde i dati live con la potenza dell'IA per darti un analista privato 24/7.",
        "feat_ia": "Analisi Tattica IA", "feat_ia_p": "Segnali basati su RSI e SMA20.",
        "feat_cloud": "Portfolio Criptato", "feat_cloud_p": "Dati salvati su cloud sicuri.",
        "feat_turbo": "Dati in Tempo Reale", "feat_turbo_p": "Connessione diretta ai mercati mondiali.",
        "btn_enter": "ENTRA NEL TERMINALE", "btn_login": "ACCEDI", "btn_reg": "REGISTRATI",
        "btn_back": "← Indietro", "btn_logout": "ESCI", "sidebar_search": "Cerca Titolo",
        "side_save_op": "Salva Operazione", "side_price": "Prezzo ($)", "side_qty": "Quantità", "side_btn_save": "SALVA", "side_success": "Salvato!",
        "chat_title": "AI Tactical Advisor", "news_title": "Data Stream News", "auth_title": "Autenticazione Nodo",
        "disclaimer": "⚠️ Disclaimer Legale: CyberTrading Hub è uno strumento di analisi basato su IA. Non costituisce consulenza finanziaria. I mercati sono volatili. Investi a tuo rischio."
    }
}

st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #00ff41; }
    .hero-title { font-size: clamp(40px, 8vw, 70px); font-weight: 800; text-align: center; background: -webkit-linear-gradient(#00ff41, #ff00ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-top: 20px; }
    .about-section { background: rgba(10, 10, 10, 0.9); border-left: 5px solid #ff00ff; padding: 25px; margin: 30px auto; max-width: 950px; border-radius: 0 15px 15px 0; }
    div[data-testid="stMetric"] { background: rgba(20, 20, 20, 0.8); border: 1px solid #00ff41; border-radius: 10px; padding: 10px; box-shadow: 0 0 5px rgba(0,255,65,0.2); }
    .stButton>button { background: linear-gradient(45deg, #ff00ff, #00ff41) !important; color: white !important; font-weight: bold; border-radius: 30px; }
    .legal-disclaimer { text-align: center; color: #555; font-size: 12px; margin-top: 50px; padding: 10px; border-top: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GESTIONE STATO ---
if 'lang' not in st.session_state: st.session_state.lang = "IT"
if 'page' not in st.session_state: st.session_state.page = "landing"
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
L = LANGUAGES[st.session_state.lang]

# --- 3. FUNZIONI CORE E INIZIALIZZAZIONE ---
def make_hashes(p): return hashlib.sha256(str.encode(p)).hexdigest()
def check_hashes(p, h): return make_hashes(p) == h

# Connessione Sicura a Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    db_connected = True
except Exception as e:
    db_connected = False

API_KEY = os.environ.get("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-pro')
else:
    st.error("⚠️ Errore critico: GEMINI_API_KEY non trovata sul server.")
    st.stop()

@st.cache_data(ttl=300)
def get_market_prices(tickers_list):
    try:
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

# --- 4. LANDING PAGE ---
if st.session_state.page == "landing" and not st.session_state.logged_in:
    st.markdown(f"<div class='hero-title'>{L['hero_t']}</div>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #888;'>{L['hero_s']}</p>", unsafe_allow_html=True)
    
    if not db_connected:
        st.warning("⚠️ Accesso Utenti in Manutenzione temporanea. Assicurati di aver impostato SPREADSHEET_URL su Render.")

    st.markdown(f"<div class='about-section'><h2>{L['about_h']}</h2><p>{L['about_p']}</p></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div style='border:1px solid #00ff41; padding:20px; border-radius:15px; text-align:center;'><h3>{L['feat_ia']}</h3><p>{L['feat_ia_p']}</p></div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='border:1px solid #ff00ff; padding:20px; border-radius:15px; text-align:center;'><h3>{L['feat_cloud']}</h3><p>{L['feat_cloud_p']}</p></div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='border:1px solid #00ff41; padding:20px; border-radius:15px; text-align:center;'><h3>{L['feat_turbo']}</h3><p>{L['feat_turbo_p']}</p></div>", unsafe_allow_html=True)
    st.write("##")
    
    if db_connected:
        if st.button(L['btn_enter']): st.session_state.page = "auth"; st.rerun()
    st.markdown(f"<div class='legal-disclaimer'>{L['disclaimer']}</div>", unsafe_allow_html=True)

# --- 5. AUTH ---
elif st.session_state.page == "auth" and not st.session_state.logged_in:
    st.markdown(f"<h2 style='text-align: center; color: #ff00ff;'>{L['auth_title']}</h2>", unsafe_allow_html=True)
    t1, t2 = st.tabs([L['btn_login'], L['btn_reg']])
    
    with t1:
        e = st.text_input("Email").lower().strip()
        p = st.text_input("Password", type="password").strip()
        if st.button(L['btn_login']):
            try:
                df_u = conn.read(worksheet="Utenti", ttl=0)
                df_u["Email_Safe"] = df_u["Email"].astype(str).str.strip().str.lower()
                u = df_u[df_u["Email_Safe"] == e]
                if not u.empty:
                    if check_hashes(p, str(u["Password"].values[0]).strip()):
                        st.session_state.logged_in = True
                        st.session_state.user_email = e
                        st.rerun()
                    else: st.error("Accesso negato. Password errata.")
                else: st.error("Accesso negato. Utente non trovato.")
            except Exception as ex: st.error(f"⚠️ Errore Database: {ex}")

    with t2:
        ne = st.text_input("Nuova Email").lower().strip()
        np = st.text_input("Nuova Password", type="password").strip()
        if st.button(L['btn_reg']):
            try:
                df_u = conn.read(worksheet="Utenti", ttl=0)
                if "Email" not in df_u.columns: df_u = pd.DataFrame(columns=["Email", "Password"])
                df_u["Email_Safe"] = df_u["Email"].astype(str).str.strip().str.lower()
                if ne in df_u["Email_Safe"].values: st.warning("Email già registrata.")
                elif "@" in ne:
                    df_to_save = df_u.drop(columns=["Email_Safe"])
                    nu = pd.DataFrame([{"Email": ne, "Password": make_hashes(np)}])
                    conn.update(worksheet="Utenti", data=pd.concat([df_to_save, nu], ignore_index=True))
                    st.success("Account creato! Ora fai il login.")
            except Exception as ex: st.error(f"⚠️ Errore Database: {ex}")

    if st.button(L['btn_back']): st.session_state.page = "landing"; st.rerun()

# --- 6. DASHBOARD ---
elif st.session_state.logged_in:
    st.sidebar.title(f"👾 Hub: {st.session_state.user_email}")
    t_search = st.sidebar.text_input(L['sidebar_search'], "BTC").upper()
    t_sym = f"{t_search}-USD" if t_search in ["BTC", "ETH", "SOL"] else t_search

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
                    ctx = f"Ticker {t_sym}, Price {df['Close'].iloc[-1]:.2f}, RSI {df['RSI'].iloc[-1]:.1f}, SMA20 {df['SMA20'].iloc[-1]:.1f}"
                    sys_i = f"Role: Senior Financial Analyst. Context: {ctx}. Respond in Italian. Keep it technical."
                    try:
                        res = model.generate_content([sys_i, inp]).text
                    except Exception as e:
                        res = f"AI Error: {e}"
                    st.markdown(res)
                    st.session_state.msgs.append({"role": "assistant", "content": res})

    if st.sidebar.button(L['btn_logout']): st.session_state.logged_in = False; st.rerun()
