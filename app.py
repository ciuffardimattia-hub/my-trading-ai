import streamlit as st
import google.generativeai as genai
import os
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import xml.etree.ElementTree as ET
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from datetime import datetime
import hashlib
import time

# --- 1. CONFIGURAZIONE E FORZATURA BARRA LATERALE ---
st.set_page_config(
    page_title="Market-Core Terminal", 
    layout="wide", 
    page_icon="icona.png",
    initial_sidebar_state="expanded"
)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- 2. LINGUE ESPANSE (TRADUZIONE TOTALE) ---
LANGUAGES = {
    "IT": {
        "hero_t": "MARKET-CORE", "hero_s": "Analisi Quantitativa IA in tempo reale.",
        "about_h": "Perché Market-Core", "about_p": "Il nostro Hub fonde i dati live con la potenza di Google Gemini per un'analisi professionale 24/7.",
        "feat_ia": "Analisi Tattica IA", "feat_ia_p": "Segnali basati su RSI e SMA.",
        "feat_cloud": "Portfolio Criptato", "feat_cloud_p": "Dati salvati su cloud sicuri.",
        "feat_turbo": "Dati Tempo Reale", "feat_turbo_p": "Connessione diretta ai mercati mondiali.",
        "btn_enter": "ACCEDI AL TERMINALE", "main_search": "CERCA NOME O TICKER (es. Bitcoin o NVDA)",
        "chat_title": "AI Tactical Support", "news_title": "Data Stream News",
        "port_title": "📁 PORTAFOGLIO CLOUD", 
        "port_subtitle": "I tuoi Asset",
        "port_add": "AGGIUNGI TITOLO",
        "port_ticker": "Ticker (es. NVDA)", "port_qty": "Quantità", "port_price": "Prezzo ($)", "btn_save": "SALVA",
        "disclaimer": "⚠️ Market-Core è uno strumento IA. Non costituisce consulenza finanziaria.",
        "chart_settings": "📊 Impostazioni Grafico", "period": "📅 Periodo", "style": "📈 Stile", "indicators": "⚙️ Indicatori",
        "candles": "Candele", "line": "Linea", "price": "Prezzo",
        "no_news": "Nessuna notizia trovata.", "ask_ai": "Chiedimi un'analisi sul titolo...",
        "no_asset": "Nessun asset salvato.", "logout": "LOGOUT SICURO", "error_ai": "L'IA non è al momento disponibile.",
        "loading_chart": "Compilazione dati grafici in corso..."
    },
    "EN": {
        "hero_t": "MARKET-CORE", "hero_s": "Real-time AI Quantitative Analysis.",
        "about_h": "Why Market-Core", "about_p": "Our Hub merges live data with Google Gemini for professional 24/7 analysis.",
        "feat_ia": "AI Tactical Analysis", "feat_ia_p": "Signals based on RSI and SMA.",
        "feat_cloud": "Encrypted Portfolio", "feat_cloud_p": "Data saved on secure clouds.",
        "feat_turbo": "Real-Time Data", "feat_turbo_p": "Direct connection to global markets.",
        "btn_enter": "ACCESS TERMINAL", "main_search": "SEARCH NAME OR TICKER (e.g. Bitcoin or NVDA)",
        "chat_title": "AI Tactical Support", "news_title": "Data Stream News",
        "port_title": "📁 CLOUD PORTFOLIO", 
        "port_subtitle": "Your Assets",
        "port_add": "ADD ASSET",
        "port_ticker": "Ticker (e.g. NVDA)", "port_qty": "Quantity", "port_price": "Price ($)", "btn_save": "SAVE",
        "disclaimer": "⚠️ Market-Core is an AI tool. Not financial advice.",
        "chart_settings": "📊 Chart Settings", "period": "📅 Period", "style": "📈 Style", "indicators": "⚙️ Indicators",
        "candles": "Candles", "line": "Line", "price": "Price",
        "no_news": "No news found.", "ask_ai": "Ask for an analysis...",
        "no_asset": "No assets saved.", "logout": "SECURE LOGOUT", "error_ai": "AI is currently unavailable.",
        "loading_chart": "Compiling chart data..."
    },
    "ES": {
        "hero_t": "MARKET-CORE", "hero_s": "Análisis Cuantitativo IA en tiempo real.",
        "about_h": "¿Por qué Market-Core?", "about_p": "Nuestro Hub fusiona datos en vivo con la potencia de Google Gemini para un análisis profesional 24/7.",
        "feat_ia": "Análisis Táctico IA", "feat_ia_p": "Señales basadas en RSI y SMA.",
        "feat_cloud": "Portafolio Cifrado", "feat_cloud_p": "Datos en la nube segura.",
        "feat_turbo": "Datos en Tiempo Real", "feat_turbo_p": "Conexión directa a los mercados.",
        "btn_enter": "ACCEDER AL TERMINAL", "main_search": "BUSCAR NOMBRE O TICKER",
        "chat_title": "Soporte Táctico IA", "news_title": "Noticias Data Stream",
        "port_title": "📁 PORTAFOLIO CLOUD", 
        "port_subtitle": "Tus Activos",
        "port_add": "AÑADIR ACTIVO",
        "port_ticker": "Ticker (ej. NVDA)", "port_qty": "Cantidad", "port_price": "Precio ($)", "btn_save": "GUARDAR",
        "disclaimer": "⚠️ Market-Core es una herramienta de IA. No es asesoramiento financiero.",
        "chart_settings": "📊 Ajustes del Gráfico", "period": "📅 Período", "style": "📈 Estilo", "indicators": "⚙️ Indicadores",
        "candles": "Velas", "line": "Línea", "price": "Precio",
        "no_news": "No se encontraron noticias.", "ask_ai": "Pide un análisis...",
        "no_asset": "Ningún activo guardado.", "logout": "CERRAR SESIÓN", "error_ai": "La IA no está disponible.",
        "loading_chart": "Recopilando datos del gráfico..."
    },
    "FR": {
        "hero_t": "MARKET-CORE", "hero_s": "Analyse Quantitative IA en temps réel.",
        "about_h": "Pourquoi Market-Core", "about_p": "Notre Hub fusionne les données avec la puissance de Google Gemini pour une analyse 24/7.",
        "feat_ia": "Analyse Tactique IA", "feat_ia_p": "Signaux basés sur RSI et SMA.",
        "feat_cloud": "Portefeuille Crypté", "feat_cloud_p": "Données sur le cloud sécurisé.",
        "feat_turbo": "Données en Temps Réel", "feat_turbo_p": "Connexion directe aux marchés.",
        "btn_enter": "ACCÉDER AU TERMINAL", "main_search": "RECHERCHER UN NOM OU UN TICKER",
        "chat_title": "Support Tactique IA", "news_title": "Actualités Data Stream",
        "port_title": "📁 PORTEFEUILLE CLOUD", 
        "port_subtitle": "Vos Actifs",
        "port_add": "AJOUTER ACTIF",
        "port_ticker": "Ticker (ex. NVDA)", "port_qty": "Quantité", "port_price": "Prix ($)", "btn_save": "ENREGISTRER",
        "disclaimer": "⚠️ Market-Core est un outil d'IA. Ce n'est pas un conseil financier.",
        "chart_settings": "📊 Paramètres du Graphique", "period": "📅 Période", "style": "📈 Style", "indicators": "⚙️ Indicateurs",
        "candles": "Bougies", "line": "Ligne", "price": "Prix",
        "no_news": "Aucune actualité trouvée.", "ask_ai": "Demander une analyse...",
        "no_asset": "Aucun actif enregistré.", "logout": "DÉCONNEXION", "error_ai": "L'IA est indisponible.",
        "loading_chart": "Compilation des données..."
    }
}

# --- 3. CSS CUSTOM ---
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #00ff41; font-family: 'Courier New', monospace; }
    .hero-title { font-size: clamp(50px, 8vw, 80px); font-weight: 900; text-align: center; background: linear-gradient(90deg, #00ff41, #ff00ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom:0; }
    .about-section { background: rgba(10, 10, 10, 0.9); border-left: 5px solid #ff00ff; padding: 25px; margin: 20px auto; max-width: 900px; border-radius: 0 15px 15px 0; }
    .feat-card { border: 1px solid #333; padding: 20px; border-radius: 15px; text-align: center; background: rgba(20,20,20,0.5); min-height: 160px; }
    .stButton>button { background: transparent !important; color: #00ff41 !important; border: 2px solid #00ff41 !important; width: 100%; font-weight: bold; transition: all 0.3s ease; }
    .stButton>button:hover { background: #00ff41 !important; color: black !important; box-shadow: 0 0 15px #00ff41; }
    .asset-box { border: 1px solid #333; padding: 10px; margin-bottom: 5px; border-radius: 5px; background: #111; border-left: 3px solid #ff00ff;}
    div[data-testid="stExpander"] { background-color: #111; border: 1px solid #00ff41; border-radius: 10px; }
    #MainMenu, footer {visibility: hidden;} 
    </style>
    """, unsafe_allow_html=True)

# --- 4. GESTIONE STATO ---
if 'lang' not in st.session_state: st.session_state.lang = "IT"
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'page' not in st.session_state: st.session_state.page = "landing"
if 'user_email' not in st.session_state: st.session_state.user_email = ""
if 'portfolio' not in st.session_state: st.session_state.portfolio = []
if 'terminal_booted' not in st.session_state: st.session_state.terminal_booted = False
L = LANGUAGES[st.session_state.lang]

def resolve_ticker(q):
    q = q.lower().strip()
    m = {"bitcoin": "BTC-USD", "ethereum": "ETH-USD", "solana": "SOL-USD", "amazon": "AMZN", "apple": "AAPL", "tesla": "TSLA", "nvidia": "NVDA", "oro": "GC=F", "gold": "GC=F"}
    if q in m: return m[q]
    if len(q) >= 5: 
        if q.upper() in ["BTC", "ETH", "SOL"]: return f"{q.upper()}-USD"
        return q.upper()
    return q.upper()

@st.cache_data(ttl=600)
def fetch_news_rss(q):
    news = []
    try:
        url = f"https://news.google.com/rss/search?q={q}+stock+market&hl=it&gl=IT"
        r = requests.get(url, timeout=5)
        root = ET.fromstring(r.content)
        for i in root.findall('.//item')[:5]: news.append({'t': i.find('title').text, 'l': i.find('link').text})
    except: pass
    return news

# --- 5. DATABASE ---
@st.cache_resource
def init_db():
    try:
        creds_json = os.environ.get("GOOGLE_CREDENTIALS")
        if not creds_json: return None, None
        creds_dict = json.loads(creds_json)
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key("1DJesdyf6AeyotOzBqzq-SJGKGe93v_kK6RXNB0LC_ck")
        return sheet.worksheet("Utenti"), sheet.worksheet("Portafoglio")
    except: return None, None

ws_utenti, ws_portafoglio = init_db()

def load_portfolio(email):
    if ws_portafoglio:
        all_data = ws_portafoglio.get_all_values()
        return [r for r in all_data if len(r) >= 4 and r[0] == email]
    return []

def delete_portfolio_item(email, ticker):
    if ws_portafoglio:
        records = ws_portafoglio.get_all_values()
        for i, row in enumerate(records):
            if len(row) >= 2 and row[0] == email and row[1] == ticker:
                ws_portafoglio.delete_rows(i + 1)
                return True
    return False

# --- 6. IA SINC ---
API_KEY = os.environ.get("GEMINI_API_KEY")
model = None
if API_KEY:
    genai.configure(api_key=API_KEY)
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target_model = None
        for m_name in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-1.0-pro']:
            if m_name in available_models:
                target_model = m_name
                break
        if not target_model and available_models: target_model = available_models[0]
        if target_model: model = genai.GenerativeModel(target_model)
    except: pass

# --- 7. APPLICAZIONE ---
if st.session_state.page == "landing":
    c1, c2, c3 = st.columns([4, 1, 4])
    with c2: st.session_state.lang = st.selectbox("🌐", ["IT", "EN", "ES", "FR"], index=["IT", "EN", "ES", "FR"].index(st.session_state.lang))
    
    st.markdown(f"<div class='hero-title'>{L['hero_t']}</div>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #888; font-size:20px;'>{L['hero_s']}</p>", unsafe_allow_html=True)
    st.markdown(f"<div class='about-section'><h2>{L['about_h']}</h2><p>{L['about_p']}</p></div>", unsafe_allow_html=True)
    
    col_f1, col_f2, col_f3 = st.columns(3)
    col_f1.markdown(f"<div class='feat-card'><h3>{L['feat_ia']}</h3><p>{L['feat_ia_p']}</p></div>", unsafe_allow_html=True)
    col_f2.markdown(f"<div class='feat-card' style='border-color:#ff00ff;'><h3>{L['feat_cloud']}</h3><p>{L['feat_cloud_p']}</p></div>", unsafe_allow_html=True)
    col_f3.markdown(f"<div class='feat-card'><h3>{L['feat_turbo']}</h3><p>{L['feat_turbo_p']}</p></div>", unsafe_allow_html=True)
    
    st.write("##")
    if st.button(L['btn_enter']):
        st.session_state.page = "auth"
        st.rerun()

elif st.session_state.page == "auth":
    st.markdown("<h2 style='text-align: center; color: #ff00ff;'>Autenticazione Nodo</h2>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["Accedi", "Registrati"])
    
    with t1:
        email_in = st.text_input("Email", key="login_mail")
        pass_in = st.text_input("Password", type="password", key="login_pass")
        if st.button("ENTRA NEL TERMINALE"):
            if email_in and pass_in:
                if ws_utenti:
                    users = ws_utenti.get_all_values()
                    hashed_input = hash_password(pass_in)
                    user_found = False
                    for row in users:
                        if len(row) >= 2 and row[0] == email_in and row[1] == hashed_input:
                            user_found = True
                            break
                    if user_found:
                        st.session_state.logged_in = True
                        st.session_state.user_email = email_in
                        st.session_state.portfolio = load_portfolio(email_in)
                        st.session_state.terminal_booted = False
                        st.session_state.page = "terminal"
                        st.rerun()
                    else: st.error("Email o password errati.")
                else: st.error("Errore Database.")
            else: st.warning("Inserisci credenziali.")

    with t2:
        reg_email = st.text_input("Nuova Email", key="reg_mail")
        reg_pass = st.text_input("Nuova Password", type="password", key="reg_pass")
        if st.button("CREA ACCOUNT CLOUD"):
            if reg_email and reg_pass:
                if ws_utenti:
                    try:
                        ws_utenti.append_row([reg_email, hash_password(reg_pass)])
                        st.success("Account creato! Ora puoi accedere.")
                    except: st.error("Errore di salvataggio Database.")
                else: st.error("Errore Server.")
            else: st.warning("Compila tutti i campi.")
            
    if st.button("← Torna alla Home"):
        st.session_state.page = "landing"
        st.rerun()

elif st.session_state.page == "terminal" and st.session_state.logged_in:
    
    if not st.session_state.terminal_booted:
        boot_placeholder = st.empty()
        boot_phrases = ["> Inizializzazione Hub v9...", "> Aggancio API globali...", "> Accesso garantito."]
        with boot_placeholder.container():
            st.markdown("<div style='margin-top:20vh; font-family: Courier New;'>", unsafe_allow_html=True)
            for phrase in boot_phrases:
                st.markdown(f"<h4 style='color:#00ff41;'>{phrase}</h4>", unsafe_allow_html=True)
                time.sleep(0.5)
            st.markdown("</div>", unsafe_allow_html=True)
            time.sleep(0.5)
        boot_placeholder.empty()
        st.session_state.terminal_booted = True
        st.rerun()

    with st.sidebar:
        st.markdown(f"<h2 style='color:#ff00ff;'>{L['hero_t']}</h2>", unsafe_allow_html=True)
        st.session_state.lang = st.selectbox("🌐 ", ["IT", "EN", "ES", "FR"], index=["IT", "EN", "ES", "FR"].index(st.session_state.lang))
        
        st.divider()
        st.markdown(f"### {L['port_title']}")
        if st.session_state.portfolio:
            st.markdown(f"<span style='color:#888;'>{L['port_subtitle']}</span>", unsafe_allow_html=True)
            for item in st.session_state.portfolio:
                ticker, price, qty = item[1], float(item[2]), float(item[3])
                col_txt, col_btn = st.columns([4, 1])
                with col_txt: st.markdown(f"<div class='asset-box'><b>{ticker}</b><br>{qty} qt | ${price:.2f}</div>", unsafe_allow_html=True)
                with col_btn:
                    if st.button("🗑️", key=f"del_{ticker}"):
                        if delete_portfolio_item(st.session_state.user_email, ticker):
                            st.session_state.portfolio = load_portfolio(st.session_state.user_email)
                            st.rerun()
        else:
            st.info(L['no_asset'])
        
        st.write("##")
        st.markdown(f"**{L['port_add']}**")
        p_ticker = st.text_input(L['port_ticker'], key="tck_in").upper()
        c_qty, c_prc = st.columns(2)
        with c_qty: p_qty = st.number_input(L['port_qty'], min_value=0.01, step=0.01)
        with c_prc: p_price = st.number_input(L['port_price'], min_value=0.01, step=0.01)
        
        if st.button(L['btn_save']):
            if p_ticker and ws_portafoglio:
                totale = p_qty * p_price
                new_row = [st.session_state.user_email, p_ticker, str(p_price), str(p_qty), str(totale), datetime.now().strftime("%Y-%m-%d")]
                try:
                    ws_portafoglio.append_row(new_row)
                    st.session_state.portfolio = load_portfolio(st.session_state.user_email)
                    st.rerun() 
                except: st.error("Errore DB.")
            elif not p_ticker:
                st.warning("Inserisci Ticker.")

        st.divider()
        if st.button(L['logout']):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.session_state.portfolio = []
            st.session_state.terminal_booted = False
            st.session_state.page = "landing"
            st.rerun()

    st.markdown(f"<h3 style='text-align:center;'>🔍 {L['main_search']}</h3>", unsafe_allow_html=True)
    u_in = st.text_input("", "Bitcoin", label_visibility="collapsed")
    t_sym = resolve_ticker(u_in)

    trend = {"BTC-USD": "BTC", "NVDA": "NVDA", "GC=F": "ORO", "TSLA": "TSLA", "^IXIC": "NASDAQ"}
    m_p = yf.download(list(trend.keys()), period="5d", group_by='ticker', progress=False)
    t_cols = st.columns(5)
    for i, (s, n) in enumerate(trend.items()):
        try:
            val = m_p[s]['Close'].dropna().iloc[-1]
            t_cols[i].metric(n, f"${val:.2f}")
        except: t_cols[i].metric(n, "N/A")

    st.divider()

    st.markdown(f"### {L['chart_settings']}")
    g_col1, g_col2, g_col3 = st.columns(3)
    with g_col1: periodo = st.selectbox(L['period'], ["3mo", "6mo", "1y", "2y", "5y"], index=1)
    with g_col2: stile_grafico = st.selectbox(L['style'], [L['candles'], L['line']])
    with g_col3: indicatori = st.multiselect(L['indicators'], ["SMA 20", "SMA 50", "Bande di Bollinger", "MACD"], default=["SMA 20"])

    st.write("---")

    with st.spinner(L['loading_chart']):
        data = yf.download(t_sym, period=periodo, interval="1d", auto_adjust=True, progress=False)
        
        if not data.empty:
            df = data.copy()
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            df['RSI'] = ta.rsi(df['Close'], length=14)
            if "SMA 20" in indicatori: df['SMA20'] = ta.sma(df['Close'], length=20)
            if "SMA 50" in indicatori: df['SMA50'] = ta.sma(df['Close'], length=50)
            if "Bande di Bollinger" in indicatori:
                bb = ta.bbands(df['Close'], length=20)
                if bb is not None:
                    df['BBL'] = bb.iloc[:, 0]
                    df['BBU'] = bb.iloc[:, 2]
            if "MACD" in indicatori:
                macd = ta.macd(df['Close'])
                if macd is not None:
                    df['MACD'] = macd.iloc[:, 0]
                    df['MACD_sig'] = macd.iloc[:, 2]

            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
            
            if stile_grafico == L['candles']:
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name=L['price']), row=1, col=1)
            else:
                fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name=L['price'], line=dict(color='#00ff41', width=2)), row=1, col=1)
            
            if "SMA 20" in indicatori: fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], name="SMA 20", line=dict(color='orange', width=1.5)), row=1, col=1)
            if "SMA 50" in indicatori: fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], name="SMA 50", line=dict(color='yellow', width=1.5)), row=1, col=1)
            if "Bande di Bollinger" in indicatori and 'BBU' in df.columns:
                fig.add_trace(go.Scatter(x=df.index, y=df['BBU'], name="BB Sup", line=dict(color='rgba(255,0,255,0.6)', dash='dot')), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['BBL'], name="BB Inf", line=dict(color='rgba(255,0,255,0.6)', dash='dot')), row=1, col=1)

            if "MACD" in indicatori and 'MACD' in df.columns:
                fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], name="MACD", line=dict(color='#00ff41')), row=2, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['MACD_sig'], name="Signal", line=dict(color='orange')), row=2, col=1)
            else:
                fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='magenta', width=1.5)), row=2, col=1)
                fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
                fig.add_hline(y=30, line_dash="dot", line_color="cyan", row=2, col=1)

            fig.update_layout(template="plotly_dark", height=550, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=10,b=0), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig, use_container_width=True)

            c1, c2 = st.columns([0.4, 0.6])
            with c1:
                st.subheader(f"📰 {L['news_title']}")
                news_feed = fetch_news_rss(u_in)
                if news_feed:
                    for n in news_feed: st.markdown(f"• [{n['t']}]({n['l']})")
                else: st.write(L['no_news'])

            with c2:
                # MENU A TENDINA PER LA CHAT (STILE WIDGET PROFESSIONALE)
                with st.expander(f"💬 {L['chat_title']} - Online", expanded=True):
                    if 'msgs' not in st.session_state: st.session_state.msgs = []
                    
                    # ICONE PERSONALIZZATE: 🧑‍💻 (User) e ⚡ (AI)
                    for m in st.session_state.msgs:
                        icona = "🧑‍💻" if m["role"] == "user" else "⚡"
                        with st.chat_message(m["role"], avatar=icona): st.markdown(m["content"])
                    
                    if inp := st.chat_input(L['ask_ai']):
                        st.session_state.msgs.append({"role": "user", "content": inp})
                        with st.chat_message("user", avatar="🧑‍💻"): st.markdown(inp)
                        
                        with st.chat_message("assistant", avatar="⚡"):
                            if model:
                                terminal_placeholder = st.empty()
                                fake_logs = ["⏳...", "📡...", "⚡..."]
                                for log in fake_logs:
                                    terminal_placeholder.markdown(log)
                                    time.sleep(0.3)
                                    
                                try:
                                    port_context = ""
                                    if st.session_state.portfolio:
                                        asset_list = ", ".join([f"{item[3]} quote di {item[1]} a {item[2]}$" for item in st.session_state.portfolio])
                                        port_context = f"Portafoglio attuale dell'utente: {asset_list}."

                                    ctx = f"Dati attuali - Asset: {t_sym}, Prezzo: {df['Close'].iloc[-1]:.2f}, RSI: {df['RSI'].iloc[-1]:.1f}. {port_context}"
                                    history = ""
                                    if len(st.session_state.msgs) > 1:
                                        history = "Contesto:\n" + "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.msgs[-5:-1]])
                                    
                                    prompt = f"Sei un analista finanziario IA. {ctx}\n{history}\nL'utente chiede: {inp}\nRispondi in modo schematico in lingua {st.session_state.lang}."
                                    
                                    res_stream = model.generate_content(prompt, stream=True)
                                    full_response = ""
                                    
                                    for chunk in res_stream:
                                        full_response += chunk.text
                                        terminal_placeholder.markdown(full_response + " █")
                                        time.sleep(0.01)
                                    
                                    terminal_placeholder.markdown(full_response)
                                    st.session_state.msgs.append({"role": "assistant", "content": full_response})
                                    
                                except Exception as e:
                                    terminal_placeholder.error(f"Errore: {e}")
                            else: st.error(L['error_ai'])

st.markdown(f"<div style='text-align:center; color:#444; font-size:10px; margin-top:50px;'>{L['disclaimer']}</div>", unsafe_allow_html=True)
