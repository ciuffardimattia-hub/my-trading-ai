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

# --- 1. DIZIONARIO MULTILINGUA INTEGRALE ---
st.set_page_config(page_title="CyberTrading Hub v9.8", layout="wide", page_icon="🌐")

LANGUAGES = {
    "IT": {
        "hero_t": "CYBERTRADING HUB", "hero_s": "L'intelligenza artificiale al servizio del tuo patrimonio.",
        "about_h": "Perché scegliere CyberTrading Hub?",
        "about_p": "In un mercato dominato dagli algoritmi, l'investitore retail ha bisogno di strumenti avanzati. Il nostro Hub fonde i dati live di Yahoo Finance con la potenza di Google Gemini per darti un analista privato 24/7. Non solo grafici, ma decisioni basate su RSI, Medie Mobili e sulla TUA esposizione finanziaria.",
        "feat_ia": "Analisi Tattica IA", "feat_ia_p": "L'IA interpreta RSI e SMA20 per segnalarti ipercomprato o trend ribassisti.",
        "feat_cloud": "Portfolio Criptato", "feat_cloud_p": "I tuoi dati sono salvati su cloud sicuri, accessibili solo tramite il tuo nodo.",
        "feat_turbo": "Dati in Tempo Reale", "feat_turbo_p": "Connessione diretta ai mercati mondiali per notizie e prezzi istantanei.",
        "btn_enter": "ENTRA NEL TERMINALE", "btn_login": "ACCEDI", "btn_reg": "REGISTRATI",
        "btn_back": "← Indietro", "btn_logout": "ESCI", "sidebar_search": "Cerca Titolo",
        "side_save_op": "Salva Operazione", "side_price": "Prezzo di Carico ($)", "side_qty": "Quantità", "side_btn_save": "INVIA AL CLOUD", "side_success": "Sincronizzato!",
        "port_inv": "Investito", "port_val": "Valore Live", "port_perf": "Performance Patrimonio",
        "chat_title": "AI Tactical Advisor", "news_title": "Data Stream News", "auth_title": "Autenticazione Nodo"
    },
    "EN": {
        "hero_t": "CYBERTRADING HUB", "hero_s": "Artificial intelligence at the service of your assets.",
        "about_h": "Why choose CyberTrading Hub?",
        "about_p": "In a market dominated by algorithms, retail investors need advanced tools. Our Hub merges live data from Yahoo Finance with the power of Google Gemini to give you a 24/7 private analyst. Not just charts, but decisions based on RSI, Moving Averages, and YOUR financial exposure.",
        "feat_ia": "AI Tactical Analysis", "feat_ia_p": "AI interprets RSI and SMA20 to alert you to overbought or bearish trends.",
        "feat_cloud": "Encrypted Portfolio", "feat_cloud_p": "Your data is saved on secure clouds, accessible only through your node.",
        "feat_turbo": "Real-Time Data", "feat_turbo_p": "Direct connection to world markets for instant news and prices.",
        "btn_enter": "ENTER TERMINAL", "btn_login": "LOGIN", "btn_reg": "REGISTER",
        "btn_back": "← Back", "btn_logout": "LOGOUT", "sidebar_search": "Search Ticker",
        "side_save_op": "Save Trade", "side_price": "Entry Price ($)", "side_qty": "Quantity", "side_btn_save": "SEND TO CLOUD", "side_success": "Synchronized!",
        "port_inv": "Invested", "port_val": "Live Value", "port_perf": "Portfolio Performance",
        "chat_title": "AI Tactical Advisor", "news_title": "News Feed", "auth_title": "Node Authentication"
    },
    "ES": {
        "hero_t": "CYBERTRADING HUB", "hero_s": "Inteligencia artificial al servicio de su patrimonio.",
        "about_h": "¿Por qué elegir CyberTrading Hub?",
        "about_p": "En un mercado dominado por algoritmos, el inversor retail necesita herramientas avanzadas. Nuestro Hub fusiona datos en vivo con la potencia de Google Gemini para darle un analista privado 24/7.",
        "feat_ia": "Análisis Táctico IA", "feat_ia_p": "La IA interpreta RSI y SMA20 para alertarle sobre tendencias.",
        "feat_cloud": "Cartera Criptografiada", "feat_cloud_p": "Sus datos se guardan en nubes seguras, accesibles solo por su nodo.",
        "feat_turbo": "Datos en Tiempo Real", "feat_turbo_p": "Conexión directa a los mercados mundiales.",
        "btn_enter": "ENTRAR AL TERMINAL", "btn_login": "CONECTAR", "btn_reg": "REGISTRAR",
        "btn_back": "← Volver", "btn_logout": "SALIR", "sidebar_search": "Buscar Ticker",
        "side_save_op": "Guardar Operación", "side_price": "Precio de Entrada ($)", "side_qty": "Cantidad", "side_btn_save": "ENVIAR A LA NUBE", "side_success": "¡Sincronizado!",
        "port_inv": "Invertido", "port_val": "Valor en Vivo", "port_perf": "Rendimiento de Cartera",
        "chat_title": "Asesor IA", "news_title": "Noticias", "auth_title": "Autenticación de Nodo"
    }
}

# --- 2. STYLE CYBERPUNK ---
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #00ff41; }
    .hero-title { font-size: clamp(40px, 8vw, 70px); font-weight: 800; text-align: center; background: -webkit-linear-gradient(#00ff41, #ff00ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-top: 20px; }
    .about-section { background: rgba(10, 10, 10, 0.9); border-left: 5px solid #ff00ff; padding: 25px; margin: 30px auto; max-width: 950px; border-radius: 0 15px 15px 0; }
    div[data-testid="stMetric"] { background: rgba(20, 20, 20, 0.8); border: 1px solid #00ff41; border-radius: 10px; padding: 15px; box-shadow: 0 0 10px rgba(0,255,65,0.2); }
    .stButton>button { background: linear-gradient(45deg, #ff00ff, #00ff41) !important; color: white !important; font-weight: bold; border-radius: 30px; padding: 10px 25px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. GESTIONE STATO ---
if 'lang' not in st.session_state: st.session_state.lang = "IT"
if 'page' not in st.session_state: st.session_state.page = "landing"
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
L = LANGUAGES[st.session_state.lang]

# --- 4. FUNZIONI CORE ---
def make_hashes(p): return hashlib.sha256(str.encode(p)).hexdigest()
def check_hashes(p, h): return make_hashes(p) == h

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300)
def get_market_prices(tickers):
    try:
        df = yf.download(list(tickers), period="7d", interval="1d", group_by='ticker', progress=False)
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
        
        # PROMPT IA POTENZIATO PER TERMINOLOGIA FINANZIARIA NATIVA
        sys_i = f"""
        Role: Senior Quantitative Analyst & Cyberpunk Advisor v9.8. 
        Context Data: {context}. 
        INSTRUCTION: You MUST respond strictly in {lang}. 
        Use precise, high-level financial terminology native to the {lang} language (e.g., 'ipercomprato/ipervenduto' in IT, 'overbought/oversold' in EN). 
        Analyze the RSI and SMA20 trends deeply and provide a professional, data-driven assessment of the user's portfolio situation.
        """
        res = model.generate_content([sys_i, prompt])
        return res.text
    except Exception as e: return f"AI Error: {str(e)}"

# --- 5. LANDING PAGE ---
if st.session_state.page == "landing" and not st.session_state.logged_in:
    st.session_state.lang = st.selectbox("🌐 Select Language", ["IT", "EN", "ES"], index=["IT", "EN", "ES"].index(st.session_state.lang))
    st.markdown(f"<div class='hero-title'>{L['hero_t']}</div>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #888;'>{L['hero_s']}</p>", unsafe_allow_html=True)
    
    st.markdown(f"<div class='about-section'><h2>{L['about_h']}</h2><p>{L['about_p']}</p></div>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div style='border:1px solid #00ff41; padding:20px; border-radius:15px; text-align:center;'><h3>{L['feat_ia']}</h3><p>{L['feat_ia_p']}</p></div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='border:1px solid #ff00ff; padding:20px; border-radius:15px; text-align:center;'><h3>{L['feat_cloud']}</h3><p>{L['feat_cloud_p']}</p></div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='border:1px solid #00ff41; padding:20px; border-radius:15px; text-align:center;'><h3>{L['feat_turbo']}</h3><p>{L['feat_turbo_p']}</p></div>", unsafe_allow_html=True)
    
    st.write("##")
    if st.button(L['btn_enter']):
        st.session_state.page = "auth"
        st.rerun()

# --- 6. AUTH ---
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
                st.session_state.logged_in, st.session_state.user_email = True, e
                st.rerun()
    if st.button(L['btn_back']):
        st.session_state.page = "landing"; st.rerun()

# --- 7. DASHBOARD OPERATIVA ---
elif st.session_state.logged_in:
    st.sidebar.title(f"👾 Hub: {st.session_state.user_email}")
    st.session_state.lang = st.sidebar.selectbox("🌐 Language", ["IT", "EN", "ES"], index=["IT", "EN", "ES"].index(st.session_state.lang))
    
    t_search = st.sidebar.text_input(L['sidebar_search'], "BTC").upper()
    t_sym = f"{t_search}-USD" if t_search in ["BTC", "ETH", "SOL"] else t_search
    
    # --- RIPRISTINO INPUT PORTAFOGLIO ---
    db_p = conn.read(worksheet="Portafoglio", ttl=0) # Leggiamo prima il DB
    
    with st.sidebar.container(border=True):
        st.subheader(f"💾 {L['side_save_op']}")
        p_acq = st.sidebar.number_input(L['side_price'], min_value=0.0)
        q_acq = st.sidebar.number_input(L['side_qty'], min_value=0.0)
        
        if st.sidebar.button(L['side_btn_save']):
            nuova_op = pd.DataFrame([{
                "Email": st.session_state.user_email, "Ticker": t_search, 
                "Prezzo": p_acq, "Quantità": q_acq, 
                "Totale": p_acq * q_acq, "Data": str(pd.Timestamp.now().date())
            }])
            conn.update(worksheet="Portafoglio", data=pd.concat([db_p, nuova_op], ignore_index=True))
            st.sidebar.success(L['side_success'])
            st.rerun()
            
    if st.sidebar.button(L['btn_logout']):
        st.session_state.logged_in = False; st.rerun()
    # ------------------------------------

    # Indici Live
    m_data = get_market_prices(["^GSPC", "BTC-USD", "GC=F"])
    c_m = st.columns(3)
    for i, s in enumerate(["^GSPC", "BTC-USD", "GC=F"]):
        try:
            val = m_data[s]['Close'].ffill().iloc[-1]
            c_m[i].metric(s.replace("^GSPC", "S&P 500"), f"{val:.2f}")
        except: c_m[i].metric(s, "N/A")

    st.divider()

    # Patrimonio Calcolo
    miei = db_p[db_p["Email"] == st.session_state.user_email]
    tot_inv = 0
    if not miei.empty:
        st.subheader(f"📊 {L['port_perf']}")
        u_t = [f"{t}-USD" if t in ["BTC", "ETH", "SOL"] else t for t in miei["Ticker"].unique()]
        p_l = yf.download(u_t, period="7d", progress=False)['Close'].ffill()
        tot_inv = miei["Totale"].sum()
        val_att = 0
        for _, r in miei.iterrows():
            tk = f"{r['Ticker']}-USD" if r['Ticker'] in ["BTC", "ETH", "SOL"] else r['Ticker']
            price = p_l[tk].iloc[-1] if len(u_t) > 1 else p_l.iloc[-1]
            val_att += price * r["Quantità"]
        c1, c2, c3 = st.columns(3)
        c1.metric(L['port_inv'], f"{tot_inv:.2f} $")
        c2.metric(L['port_val'], f"{val_att:.2f} $", delta=f"{val_att-tot_inv:.2f} $")
        c3.metric("Total ROI %", f"{((val_att/tot_inv)-1)*100:.2f}%")

    # Grafico con SMA20 e RSI
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
                    ctx = f"Ticker {t_sym}, Price {df['Close'].iloc[-1]:.2f}, RSI {df['RSI'].iloc[-1]:.1f}, SMA20 {df['SMA20'].iloc[-1]:.1f}, Portfolio {tot_inv}$"
                    res = get_ai_chat_response(inp, ctx, st.session_state.lang)
                    st.markdown(res)
                    st.session_state.msgs.append({"role": "assistant", "content": res})
