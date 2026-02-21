import streamlit as st
import google.generativeai as genai
import os
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# --- 1. CONFIGURAZIONE PAGINA E RIMOZIONE LOGHI ---
st.set_page_config(page_title="Market-Core Terminal", page_icon="⚡", layout="wide")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- 2. INIZIALIZZAZIONE GEMINI AI ---
API_KEY = os.environ.get("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-pro')
else:
    st.error("⚠️ Errore critico: GEMINI_API_KEY non trovata sul server.")
    st.stop()

# --- 3. CONNESSIONE SICURA DATABASE (Anti-Crash) ---
def check_db_connection():
    # Verifica se le credenziali cloud esistono, senza far crashare l'app se mancano
    return os.environ.get("GOOGLE_CREDENTIALS") is not None

db_connected = check_db_connection()

# --- 4. INTERFACCIA TERMINALE ---
st.title("🤖 Market-Core AI Terminal")
st.markdown("**Version 10.0 - Beta Access**")

if not db_connected:
    st.warning("⚠️ Modulo salvataggio Cloud offline. Analisi tecnica IA operativa al 100%.")

# Creazione delle due sezioni principali
tab1, tab2 = st.tabs(["⚡ Quant Analysis (Live)", "🛡️ AI Portfolio Health Check"])

# --- TAB 1: ANALISI SINGOLO ASSET (Perfetta per il Video 2) ---
with tab1:
    st.subheader("Single Asset Terminal")
    ticker = st.text_input("Enter Asset Ticker (e.g., NVDA, BTC-USD):", "NVDA").upper()
    
    if st.button("Run Quantitative Analysis ⚡"):
        if ticker:
            with st.spinner(f"Downloading market data for {ticker} & calculating indicators..."):
                try:
                    # Scarica i dati di mercato reali
                    data = yf.download(ticker, period="3mo")
                    
                    if data.empty:
                        st.error("Ticker non trovato. Verifica il simbolo.")
                    else:
                        # Calcolo reale di SMA20 e RSI14
                        data.ta.sma(length=20, append=True)
                        data.ta.rsi(length=14, append=True)
                        
                        # Estrazione ultimi dati
                        last_close = float(data['Close'].iloc[-1].iloc[0]) if isinstance(data['Close'].iloc[-1], pd.Series) else float(data['Close'].iloc[-1])
                        last_sma = float(data['SMA_20'].iloc[-1].iloc[0]) if isinstance(data['SMA_20'].iloc[-1], pd.Series) else float(data['SMA_20'].iloc[-1])
                        last_rsi = float(data['RSI_14'].iloc[-1].iloc[0]) if isinstance(data['RSI_14'].iloc[-1], pd.Series) else float(data['RSI_14'].iloc[-1])
                        
                        # Mostra i dati a schermo (ottimo per il video)
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Current Price", f"${last_close:.2f}")
                        col2.metric("SMA 20", f"${last_sma:.2f}")
                        col3.metric("RSI 14", f"{last_rsi:.2f}")
                        
                        # Chiamata all'IA con i dati veri integrati
                        prompt = f"Act as an elite quantitative analyst. Analyze {ticker}. Current Price is {last_close}, the 20-day SMA is {last_sma}, and the RSI is {last_rsi}. Is it a bull trap or a strong support? Keep it highly technical, professional, and brief."
                        
                        response = model.generate_content(prompt)
                        
                        st.success("Analysis Complete.")
                        st.markdown("### 📊 AI Quantitative Report")
                        st.write(response.text)
                        
                except Exception as e:
                    st.error(f"Errore durante l'elaborazione dei dati: {e}")
        else:
            st.info("Inserisci un Ticker per iniziare.")

# --- TAB 2: LA KILLER FEATURE ---
with tab2:
    st.subheader("Portfolio Risk Assessment")
    st.markdown("Inserisci le tue posizioni aperte. L'IA valuterà la tua esposizione e il rischio sistemico.")
    
    portfolio_input = st.text_area("Example: 10 NVDA at $800, 0.5 BTC at $60000, 50 TSLA at $170", height=100)
    
    if st.button("Run Health Check 🩺"):
        if portfolio_input:
            with st.spinner("L'IA sta scansionando l'esposizione del tuo portafoglio..."):
                try:
                    prompt = f"Analizza questo portafoglio finanziario: {portfolio_input}. 1. Identifica se c'è un'esposizione eccessiva in un singolo settore. 2. Valuta il rischio macroeconomico. 3. Assegna un 'Risk Score' da 1 a 100. Rispondi come un wealth manager istituzionale in inglese."
                    response = model.generate_content(prompt)
                    
                    st.markdown("### 🛡️ AI Risk & Exposure Report")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"Errore durante l'analisi del portafoglio: {e}")
        else:
            st.info("Inserisci le tue posizioni per avviare l'analisi.")
