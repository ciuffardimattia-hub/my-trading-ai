import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from openai import OpenAI
import requests
import xml.etree.ElementTree as ET
import os
import re

# --- 1. CONFIGURAZIONE & DATABASE ---
st.set_page_config(page_title="Trading Hub Pro v6.5", layout="wide", page_icon="📈")
DB_FILE = "portafoglio_email_db.csv"

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def carica_dati():
    cols = ["Email", "Ticker", "Prezzo", "Quantità", "Totale", "Data"]
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            return df if "Email" in df.columns else pd.DataFrame(columns=cols)
        except: return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

def salva_dati(df):
    df.to_csv(DB_FILE, index=False)

# --- 2. GESTIONE SECRETS ---
openai_key = st.secrets.get("OPENAI_API_KEY", "")

# --- 3. LOGIN ---
st.sidebar.header("🔐 Accesso")
email_utente = st.sidebar.text_input("Email", "").strip().lower()

if not email_utente or not is_valid_email(email_utente):
    st.info("👋 Accedi con la tua email per sbloccare le funzioni.")
    st.stop()

# --- 4. HOMEPAGE (MARKET MOVERS) ---
def mostra_homepage():
    st.markdown("### 🌍 Panorama Mercati")
    indices = {"^GSPC": "S&P 500", "BTC-USD": "Bitcoin", "GC=F": "Oro", "NVDA": "Nvidia", "TSLA": "Tesla"}
    cols = st.columns(len(indices))
    for i, (sym, name) in enumerate(indices.items()):
        try:
            d = yf.Ticker(sym).history(period="2d")
            if not d.empty:
                curr, prev = d['Close'].iloc[-1], d['Close'].iloc[-2]
                pct = ((curr - prev) / prev) * 100
                cols[i].metric(name, f"{curr:.2f}", f"{pct:.2f}%")
        except: cols[i].write(f"N/A {name}")

# --- 5. MOTORE NEWS (VERSIONE AVANZATA 24h/7g) ---
def get_clean_news(symbol):
    news_items = []
    seen = set()
    q = symbol.replace("-USD", "")
    for timeframe in ["1d", "7d"]:
        label = "ULTIME 24 ORE" if timeframe == "1d" else "ULTIMI 7 GIORNI"
        url = f"https://news.google.com/rss/search?q={q}+stock+news+when:{timeframe}&hl=it&gl=IT&ceid=IT:it"
        try:
            resp = requests.get(url, timeout=5)
            root = ET.fromstring(resp.content)
            for item in root.findall('.//item')[:5]:
                title = item.find('title').text
                if title and title not in seen and len(title) > 20:
                    news_items.append({
                        't': title, 's': item.find('source').text,
                        'l': item.find('link').text, 'd': item.find('pubDate').text[:16], 'p': label
                    })
                    seen.add(title)
            if news_items and timeframe == "1d": break
        except: continue
    return news_items

# --- 6. SIDEBAR: RICERCA E DATABASE ---
st.sidebar.divider()
ticker_in = st.sidebar.text_input("🔍 Cerca Titolo", "AAPL").upper()
ticker_sym = f"{ticker_in}-USD" if ticker_in in ["BTC", "ETH", "SOL", "XRP"] else ticker_in

with st.sidebar.container(border=True):
    st.subheader("➕ Registra Acquisto")
    d_acq = st.sidebar.date_input("Data")
    p_acq = st.sidebar.number_input("Prezzo ($)", min_value=0.0, step=0.01)
    q_acq = st.sidebar.number_input("Quantità", min_value=0.0, step=0.1)
    if st.sidebar.button("💾 Salva nel Database"):
        if p_acq > 0 and q_acq > 0:
            db = carica_dati()
            nuova = pd.DataFrame([{"Email": email_utente, "Ticker": ticker_in, "Prezzo": p_acq, "Quantità": q_acq, "Totale": p_acq*q_acq, "Data": d_acq}])
            salva_dati(pd.concat([db, nuova], ignore_index=True))
            st.rerun()

# --- 7. VISUALIZZAZIONE PRINCIPALE ---
mostra_homepage()
st.divider()

try:
    raw_data = yf.download(ticker_sym, period="1y", interval="1d", auto_adjust=True)
    
    if raw_data.empty:
        st.error(f"❌ Dati non trovati per {ticker_sym}")
    else:
        df_h = raw_data.copy()
        if isinstance(df_h.columns, pd.MultiIndex):
            df_h.columns = df_h.columns.get_level_values(0)

        # Calcolo Indicatori
        df_h['SMA20'] = ta.sma(df_h['Close'], length=20)
        df_h['RSI'] = ta.rsi(df_h['Close'], length=14)
        last_p = float(df_h['Close'].iloc[-1])
        last_sma = float(df_h['SMA20'].iloc[-1])
        
        # --- LOGICA TREND LABEL ---
        if last_p > last_sma * 1.01:
            trend_label = "BULLISH 📈"
            trend_color = "green"
        elif last_p < last_sma * 0.99:
            trend_label = "BEARISH 📉"
            trend_color = "red"
        else:
            trend_label = "NEUTRAL ↔️"
            trend_color = "gray"

        st.markdown(f"## 🚀 Analisi: {ticker_sym} | <span style='color:{trend_color}'>{trend_label}</span>", unsafe_allow_html=True)
        
        # Sezione Portafoglio
        db = carica_dati()
        miei = db[(db["Email"] == email_utente) & (db["Ticker"] == ticker_in)]
        p_summary = "Nessuna posizione aperta."
        
        if not miei.empty:
            tot_q = miei["Quantità"].sum()
            pmc = miei["Totale"].sum() / tot_q
            pl = ((last_p - pmc) / pmc) * 100
            c1, c2, c3 = st.columns(3)
            c1.metric("Tuo PMC", f"{pmc:.2f} $")
            c2.metric("Quantità", f"{tot_q:.1f}")
            c3.metric("Profitto/Perdita", f"{pl:.2f}%", delta=f"{pl:.2f}%")
            p_summary = f"L'utente ha {tot_q} quote con PMC {pmc:.2f} $. P&L attuale: {pl:.2f}%."

        # GRAFICO PROFESSIONALE (Candele + RSI)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        fig.add_trace(go.Candlestick(x=df_h.index, open=df_h['Open'], high=df_h['High'], low=df_h['Low'], close=df_h['Close'], name="Prezzo"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_h.index, y=df_h['SMA20'], name="SMA 20", line=dict(color='orange', width=1.5)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_h.index, y=df_h['RSI'], name="RSI", line=dict(color='magenta', width=1.5)), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        

        # SEZIONE NEWS E IA
        st.divider()
        col_news, col_ai = st.columns([0.6, 0.4])
        
        with col_news:
            st.subheader("📰 News Real-Time (24h/7g)")
            fresh_news = get_clean_news(ticker_in)
            news_ia = ""
            if fresh_news:
                for n in fresh_news:
                    news_ia += f"- {n['t']}\n"
                    with st.container(border=True):
                        cn1, cn2 = st.columns([0.8, 0.2])
                        cn1.markdown(f"**{n['p']}** | {n['t']}")
                        cn1.caption(f"Fonte: {n['s']} | Data: {n['d']}")
                        cn2.link_button("Leggi", n['l'])
            else: st.warning("Nessuna notizia recente trovata.")

        with col_ai:
            st.subheader("🧠 Report Strategico IA")
            if st.button("Genera Analisi IA"):
                if not openai_key: st.error("Manca OpenAI Key!")
                else:
                    client = OpenAI(api_key=openai_key)
                    with st.spinner("L'IA sta elaborando..."):
                        prompt = f"Analizza {ticker_sym} ({trend_label}). Prezzo {last_p:.2f}, RSI {df_h['RSI'].iloc[-1]:.1f}. Portafoglio: {p_summary}. News: {news_ia}. Rispondi in italiano."
                        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
                        st.success(res.choices[0].message.content)

except Exception as e: st.error(f"Errore: {e}")
