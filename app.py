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

# --- 1. CONFIGURAZIONE ESTETICA AVANZATA ---
st.set_page_config(page_title="Market-Core Terminal", layout="wide", page_icon="⚡")

st.markdown("""
    <style>
    /* Sfondo e Colori Base */
    .stApp { background-color: #050505; color: #00ff41; font-family: 'Courier New', Courier, monospace; }
    
    /* Titolo Market-Core */
    .hero-title { 
        font-size: clamp(50px, 10vw, 90px); 
        font-weight: 900; 
        text-align: center; 
        background: linear-gradient(90deg, #00ff41, #ff00ff); 
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent; 
        letter-spacing: -2px;
        margin-bottom: 0px;
    }
    .hero-subtitle { text-align: center; color: #888; font-size: 18px; margin-bottom: 40px; }

    /* Cards e Sezioni */
    .about-section { 
        background: rgba(10, 10, 10, 0.9); 
        border: 1px solid #333; 
        border-left: 5px solid #ff00ff; 
        padding: 30px; 
        border-radius: 10px; 
        margin: 20px auto; 
        max-width: 800px; 
    }

    /* Pulsante Accesso Cyber */
    .stButton>button { 
        background: transparent !important; 
        color: #00ff41 !important; 
        border: 2px solid #00ff41 !important; 
        border-radius: 5px !important;
        font-weight: bold !important;
        padding: 15px 30px !important;
        transition: 0.3s !important;
        width: 100%;
        text-transform: uppercase;
    }
    .stButton>button:hover { 
        background: #00ff41 !important; 
        color: #000 !important; 
        box-shadow: 0 0 20px #00ff41;
    }

    /* Nascondi elementi Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. INIZIALIZZAZIONE IA ---
API_KEY = os.environ.get("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Configurazione IA mancante.")

# --- 3. GESTIONE NAVIGAZIONE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 4. FUNZIONI DATI ---
@st.cache_data(ttl=300)
def get_market_prices(tickers_list):
    try: return yf.download(tickers_list, period="5d", group_by='ticker', progress=False)
    except: return None

def get_news(symbol):
    news = []
    url = f"https://news.google.com/rss/search?q={symbol}+stock+news&hl=it&gl=IT&ceid=IT:it"
    try:
        r = requests.get(url, timeout=3)
        root = ET.fromstring(r.content)
        for i in root.findall('.//item')[:4]:
            news.append({'t': i.find('title').text, 'l': i.find('link').text})
    except: pass
    return news

# --- 5. PAGINA INIZIALE (LANDING) ---
if not st.session_state.logged_in:
    st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='hero-title'>MARKET-CORE</div>", unsafe_allow_html=True)
    st.markdown("<div class='hero-subtitle'>Sistemi Avanzati di Analisi Quantitativa IA</div>", unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        st.markdown("""
            <div class='about-section'>
            <h3 style='color:#ff00ff; margin-top:0;'>Accesso Terminale v10.0</h3>
            <p style='color:#ccc;'>Benvenuto nell'Hub. Connessione ai mercati globali e motore IA Gemini attivo. Il sistema è pronto per l'elaborazione dati in tempo reale.</p>
            </div>
            """, unsafe_allow_html=True)
        if st.button("INIZIALIZZA NODO DI ACCESSO"):
            st.session_state.logged_in = True
            st.rerun()
    
    st.markdown("<p style='text-align:center; color:#444; margin-top:50px;'>Versione Cloud 2026. Beta Pubblica.</p>", unsafe_allow_html=True)

# --- 6. TERMINALE OPERATIVO ---
else:
    # Sidebar di Controllo
    st.sidebar.markdown("<h2 style='color:#ff00ff;'>MARKET-CORE</h2>", unsafe_allow_html=True)
    ticker_input = st.sidebar.text_input("CERCA TICKER (es. NVDA, BTC, TSLA)", "NVDA").upper()
    t_sym = f"{ticker_input}-USD" if ticker_input in ["BTC", "ETH", "SOL"] else ticker_input

    # Tendenza - Top Bar
    trending = {"BTC-USD": "BTC", "NVDA": "NVDA", "GC=F": "GOLD", "^IXIC": "NASDAQ"}
    m_prices = get_market_prices(list(trending.keys()))
    t_cols = st.columns(4)
    for i, (sym, name) in enumerate(trending.items()):
        try:
            p = m_prices[sym]['Close'].iloc[-1]
            t_cols[i].metric(name, f"${p:.2f}")
        except: t_cols[i].metric(name, "N/A")

    st.divider()

    # Scarico dati per analisi
    with st.spinner(f"Analisi {t_sym} in corso..."):
        data = yf.download(t_sym, period="1y", interval="1d", auto_adjust=True, progress=False)
        
        if not data.empty:
            df = data.copy()
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df['SMA20'] = ta.sma(df['Close'], length=20)
            df['RSI'] = ta.rsi(df['Close'], length=14)

            # Grafico Professionale
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.03)
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Prezzo"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], name="SMA 20", line=dict(color='#ffaa00', width=1.5)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='#ff00ff', width=1.5)), row=2, col=1)
            fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dot", line_color="cyan", row=2, col=1)
            fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)

            # Sezione News e AI Chat
            col_news, col_ai = st.columns([0.4, 0.6])
            
            with col_news:
                st.subheader("📡 LIVE FEED")
                news_list = get_news(ticker_input)
                for n in news_list:
                    st.markdown(f"• <a href='{n['l']}' style='color:#888; text-decoration:none;'>{n['t']}</a>", unsafe_allow_html=True)
            
            with col_ai:
                st.subheader("💬 AI TACTICAL ADVISOR")
                if 'chat_hist' not in st.session_state: st.session_state.chat_hist = []
                for m in st.session_state.chat_hist:
                    with st.chat_message(m["role"]): st.markdown(m["content"])
                
                if prompt := st.chat_input("Invia comando all'IA..."):
                    st.session_state.chat_hist.append({"role": "user", "content": prompt})
                    with st.chat_message("user"): st.markdown(prompt)
                    
                    with st.chat_message("assistant"):
                        stats = f"Asset {t_sym}, Prezzo {df['Close'].iloc[-1]:.2f}, RSI {df['RSI'].iloc[-1]:.1f}, SMA20 {df['SMA20'].iloc[-1]:.1f}."
                        ai_res = model.generate_content(f"Analista Senior. Dati: {stats}. Rispondi in italiano in modo tecnico e conciso: {prompt}").text
                        st.markdown(ai_res)
                        st.session_state.chat_hist.append({"role": "assistant", "content": ai_res})

    if st.sidebar.button("LOGOUT / RESET"):
        st.session_state.logged_in = False
        st.rerun()
