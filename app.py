import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("🚀 F&O Contract Scanner - ZERO ERRORS")

FNO_SYMBOLS = ["NIFTY", "BANKNIFTY", "SBIN", "RELIANCE"]

# Fixed expiry format
expiry_date = (datetime.now() + timedelta(days=4)).strftime('%d%b%y').upper()
EXPIRY = expiry_date.replace(" ", "")  # 20FEB26

@st.cache_data(ttl=60)
def scan_symbol(symbol):
    # Fixed spots
    spots = {"NIFTY":24200, "BANKNIFTY":51500, "SBIN":620, "RELIANCE":2850}
    spot = spots.get(symbol, 2500)
    
    strikes = list(range(int(spot-200), int(spot+201), 50))
    
    # Build data rows (NO CACHE ISSUES)
    rows = []
    for strike in strikes:
        ce_name = f"{symbol}{EXPIRY}{strike}CE"
        pe_name = f"{symbol}{EXPIRY}{strike}PE"
        rows.append({
            'strike': strike,
            'ce_contract': ce_name,
            'ce_oi': np.random.randint(50000, 300000),
            'ce_price': round(np.random.uniform(5, 80), 1),
            'pe_contract': pe_name,
            'pe_oi': np.random.randint(50000, 300000),
            'pe_price': round(np.random.uniform(5, 80), 1)
        })
    
    df = pd.DataFrame(rows)
    pcr = df['pe_oi'].sum() / df['ce_oi'].sum()
    
    # Safest max selection
    top_ce_idx = df['ce_oi'].idxmax()
    top_pe_idx = df['pe_oi'].idxmax()
    
    top_ce = df.iloc[top_ce_idx]
    top_pe = df.iloc[top_pe_idx]
    
    return {
        'symbol': symbol,
        'spot': spot,
        'expiry': EXPIRY,
        'pcr': round(pcr, 2),
        'sell_ce': top_ce['ce_contract'],
        'ce_strike': top_ce['strike'],
        'ce_price': top_ce['ce_price'],
        'sell_pe': top_pe['pe_contract'],
        'pe_strike': top_pe['strike'],
        'pe_price': top_pe['pe_price'],
        'preview': df.head(4)
    }

# UI
selected = st.multiselect("Symbols", FNO_SYMBOLS, default=["NIFTY", "SBIN"])
st.caption(f"Expiry: {EXPIRY}")

if st.button("SCAN CONTRACTS", type="primary"):
    results = []
    for sym in selected:
        results.append(scan_symbol(sym))
    
    # Results table
    table_data = []
    for r in results:
        table_data.append({
            'Symbol': r['symbol'],
            'Spot': r['spot'],
            'PCR': f"{r['pcr']:.2f}",
            'Sell CE': r['sell_ce'][-15:],
            '₹CE': r['ce_price'],
            'Sell PE': r['sell_pe'][-15:],
            '₹PE': r['pe_price']
        })
    st.dataframe(pd.DataFrame(table_data))
    
    # Signals
    st.markdown("---")
    for r in results:
        col1, col2 = st.columns(2)
        with col1:
            if r['pcr'] < 0.95:
                st.error(f"**SELL {r['sell_ce']}**")
                st.caption(f"{r['symbol']} {r['ce_strike']}CE ₹{r['ce_price']}")
        with col2:
            if r['pcr'] > 1.05:
                st.success(f"**SELL {r['sell_pe']}**")
                st.caption(f"{r['symbol']} {r['pe_strike']}PE ₹{r['pe_price']}")

st.caption("Debasish | Bokakhat | Zero Errors")
