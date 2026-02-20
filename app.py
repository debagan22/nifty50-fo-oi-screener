import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("🔥 NSE EOD F&O Scanner - Real Data")

FNO_SYMBOLS = ["NIFTY", "BANKNIFTY", "SBIN", "RELIANCE", "HDFCBANK"]

@st.cache_data(ttl=3600)
def get_nse_eod_fo():
    """NSE REAL EOD F&O bhavcopy - all contracts"""
    yesterday = (datetime.now() - timedelta(1)).strftime('%d%b%Y').upper()
    urls = [
        "https://www.nseindia.com/content/fo/fo_underlying.csv",  # F&O summary
        "https://www.nseindia.com/content/fo/fo_mktlots.csv"      # Lots/OI
    ]
    
    all_data = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    
    for url in urls:
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                df = pd.read_csv(StringIO(resp.text))
                all_data.append(df)
        except:
            pass
    
    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        return combined[combined['SYMBOL'].str.contains('|'.join(FNO_SYMBOLS), na=False)]
    
    st.error("❌ EOD fetch failed - try after 6PM IST")
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_symbol_contracts(symbol):
    """Parse real contracts from EOD"""
    df = get_nse_eod_fo()
    if df.empty:
        return "No EOD data"
    
    sym_data = df[df['SYMBOL'].str.contains(symbol, na=False)]
    if sym_data.empty:
        return f"No {symbol} contracts"
    
    # Extract top OI contracts
    sym_data['OI_INT'] = pd.to_numeric(sym_data['OI'], errors='coerce').fillna(0)
    top_contracts = sym_data.nlargest(3, 'OI_INT')
    
    return {
        'symbol': symbol,
        'contracts': len(sym_data),
        'top_oi': top_contracts[['SYMBOL', 'OI', 'CLOSE']].to_dict('records'),
        'latest': top_contracts.iloc[0]['TIMESTAMP'] if 'TIMESTAMP' in top_contracts else 'Today'
    }

# MAIN APP
st.subheader("📥 NSE EOD Data")
eod_df = get_nse_eod_fo()
if not eod_df.empty:
    st.success(f"✅ Loaded **{len(eod_df)}** real EOD contracts")
    st.dataframe(eod_df[['SYMBOL', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'OI']].head(20), use_container_width=True)
else:
    st.info("⏳ EOD available ~6PM IST - Market open now")

st.subheader("🎯 Top Signals")
selected = st.multiselect("Symbols", FNO_SYMBOLS, default=FNO_SYMBOLS)
if st.button("📊 ANALYZE EOD", type="primary"):
    signals = []
    for sym in selected:
        result = get_symbol_contracts(sym)
        if isinstance(result, dict):
            signals.append(result)
    
    if signals:
        for sig in signals:
            with st.expander(f"{sig['symbol']} ({sig['contracts']} contracts)"):
                st.write("**Top OI Contracts:**")
                for contract in sig['top_oi']:
                    st.markdown(f"**{contract['SYMBOL']}** | ₹{contract['CLOSE']} | OI {contract['OI']:,}")
                st.caption(f"Data: {sig['latest']}")

st.caption("Debasish Ganguly | NSE EOD Real Data | Updated 12:20 PM IST")
