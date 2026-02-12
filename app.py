import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import plotly.graph_objects as go
from openai import OpenAI
from datetime import datetime

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="AI Hybrid Advisor PRO", layout="wide")
st.title("🏦 AI Hybrid Advisor: Tecnica, Fondamentale & Portafoglio")

# --- 2. GESTIONE SESSIONE (MEMORIA ACQUISTI) ---
if 'transazioni' not in st.session_state:
    st.session_state.transazioni = []

# --- 3. BARRA LATERALE ---
st.sidebar.header("🔑 Accesso & Configurazione")
api_key = st.sidebar.text_input("OpenAI API Key", type="password")
ticker = st.sidebar.text_input("Simbolo (es. AAPL, NVDA, BTC-USD)", "AAPL").upper()

st.sidebar.divider()

st.sidebar.header("➕ Registra Acquisto")
with st.sidebar.container(border=True):
    data_ins = st.sidebar.date_input("Data", datetime.now())
    prezzo_ins = st.sidebar.number_input("Prezzo ($)", min_value=0.0, step=0.01)
    quantita_ins = st.sidebar.number_input("Quantità", min_value=0.0, step=0.1)
    if st.sidebar.button("Aggiungi al Portafoglio"):
        if prezzo_ins > 0 and quantita_ins > 0:
            st.session_state.transazioni.append({
                "Data": data_ins, "Prezzo": prezzo_ins,
                "Quantità": quantita_ins, "Totale": prezzo_ins * quantita_ins
            })
            st.sidebar.success("Registrato!")

if st.sidebar.button("🗑️ Svuota Portafoglio"):
    st.session_state.transazioni = []
    st.rerun()

st.sidebar.divider()
tipo_grafico = st.sidebar.radio("Grafico:", ["Candele (Pro)", "Linea"])
periodo = st.sidebar.selectbox("Storico:", ["5y", "2y", "1y", "max"], index=1)

# --- 4. FUNZIONE AI ---
def chiedi_a_gpt(dati_t, dati_f, simbolo, riepilogo_p):
    try:
        client = OpenAI(api_key=api_key)
        prompt = f"""
        Analizza {simbolo}. 
        TECNICA: Prezzo {dati_t['prezzo']}, RSI {dati_t['rsi']}, SMA200 {dati_t['sma200']}.
        FONDAMENTALE: P/E {dati_f.get('pe_ratio')}, Margine {dati_f.get('profit_margin')}.
        PORTAFOGLIO: {riepilogo_p}
        Fornisci un'analisi ibrida professionale in Markdown. Sii critico sulla strategia di accumulo.
        """
        risposta = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        return risposta.choices[0].message.content
    except Exception as e: return f"❌ Errore AI: {str(e)}"

# --- 5. LOGICA PRINCIPALE ---
if api_key:
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=periodo)
        
        if not df.empty:
            # Pulizia e Indicatori
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            df['SMA200'] = ta.sma(df['Close'], length=200)
            
            ultimo_prezzo = float(df['Close'].iloc[-1])
            ultimo_rsi = float(df['RSI'].dropna().iloc[-1]) if not df['RSI'].dropna().empty else 50.0
            ultima_sma = float(df['SMA200'].dropna().iloc[-1]) if not df['SMA200'].dropna().empty else ultimo_prezzo

            # --- SEZIONE METRICHE MERCATO ---
            st.subheader(f"📊 Analisi di Mercato: {ticker}")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Prezzo Attuale", f"{ultimo_prezzo:.2f} $")
            m2.metric("RSI (14d)", f"{ultimo_rsi:.1f}")
            m3.metric("Trend SMA200", "Bullish 📈" if ultimo_prezzo > ultima_sma else "Bearish 📉")
            m4.metric("Distanza SMA200", f"{(((ultimo_prezzo/ultima_sma)-1)*100):.1f}%")

            # --- SEZIONE METRICHE PORTAFOGLIO ---
            riepilogo_ai = "L'utente non ha posizioni."
            if st.session_state.transazioni:
                st.divider()
                st.subheader("💰 Performance Portafoglio")
                df_p = pd.DataFrame(st.session_state.transazioni)
                quant_tot = df_p['Quantità'].sum()
                spesa_tot = df_p['Totale'].sum()
                pmc = spesa_tot / quant_tot
                valore_att = ultimo_prezzo * quant_tot
                profitto_ass = valore_att - spesa_tot
                profitto_perc = (profitto_ass / spesa_tot) * 100

                p1, p2, p3, p4 = st.columns(4)
                p1.metric("Prezzo Medio (PMC)", f"{pmc:.2f} $")
                p2.metric("P&L Totale %", f"{profitto_perc:.2f}%", delta=f"{profitto_perc:.2f}%")
                p3.metric("P&L Assoluto", f"{profitto_ass:.2f} $", delta=f"{profitto_ass:.2f} $")
                p4.metric("Valore Totale", f"{valore_att:.2f} $")
                
                with st.expander("Visualizza dettaglio acquisti"):
                    st.table(df_p)
                riepilogo_ai = f"Possiede {quant_tot} azioni, PMC {pmc:.2f}$. P&L: {profitto_perc:.2f}%."

            # --- GRAFICO ---
            st.divider()
            if tipo_grafico == "Candele (Pro)":
                fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Prezzo")])
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA200'], name="SMA 200", line=dict(color='orange', width=1.5)))
                fig.update_layout(height=500, template="plotly_white", xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.line_chart(df['Close'])

            # --- ANALISI FONDAMENTALE E AI ---
            if st.button("🚀 Genera Report Ibrido AI"):
                info = stock.info
                fond = {"pe_ratio": info.get('forwardPE'), "profit_margin": info.get('profitMargins')}
                with st.chat_message("assistant"):
                    report = chiedi_a_gpt({"prezzo": ultimo_prezzo, "rsi": ultimo_rsi, "sma200": ultima_sma}, fond, ticker, riepilogo_ai)
                    st.markdown(report)

    except Exception as e: st.error(f"Errore: {e}")
else: st.info("👈 Inserisci l'API Key a sinistra.")