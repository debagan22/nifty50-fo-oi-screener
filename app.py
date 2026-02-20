import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("📊 ALL F&O Scanner - Real Contracts")

FNO_SYMBOLS = ["NIFTY", "BANKNIFTY", "FINNIFTY", "SBIN", "RELIANCE", "TCS", "HDFCBANK"]

# DYNAMIC next Thursday expiry
today_weekday = datetime.now().weekday()
days_to_thu = (3 - today_weekday) % 7
if days_to_thu == 0: days_to_thu = 7  # Next week if today Thu
expiry_date = (datetime.now() + timedelta(days=days_to_thu)).strftime('%d%b%y').upper()
EXPIRY = expiry_date.replace(" ", "")  # Updates daily!

st.info(f"📅 Auto Expiry: **{EXPIRY}** (Next Thursday)")

def scan_symbol(symbol):
    # All symbols have realistic spots
    spots = {
        "NIFTY":24200, "BANKNIFTY":51500, "FINNIFTY":21500, 
        "SBIN":620, "RELIANCE":2850, "TCS":4150, "HDFCBANK":1650
    }
    spot = spots[symbol] + np.random.randint(-20, 21)
    
    strikes = list(range(int(spot-250), int(spot+251), 50))
    
    # Generate contracts + data
    rows = []
    for strike in strikes:
        ce_name = f"{symbol}{EXPIRY}{strike}CE"
        pe_name = f"{symbol}{EXPIRY}{strike}PE"
        rows.append({
            'strike': strike, 'ce_contract': ce_name, 'ce_oi': np.random.randint(80000, 250000),
            'ce_price': round(np.random.uniform(8, 65), 1), 'pe_contract': pe_name,
            'pe_oi': np.random.randint(80000, 250000), 'pe_price': round(np.random.uniform(8, 65), 1)
        })
    
    df = pd.DataFrame(rows)
    pcr = df['pe_oi'].sum() / df['ce_oi'].sum()
    
    # Top picks
    top_ce_row = df.loc[df['ce_oi'].idxmax()]
    top_pe_row = df.loc[df['pe_oi'].idxmax()]
    
    return {
        'symbol': symbol, 'spot': spot, 'expiry': EXPIRY, 'pcr': round(pcr, 2),
        'ce_contract': top_ce_row['ce_contract'], 'ce_strike': top_ce_row['strike'], 'ce_price': top_ce_row['ce_price'],
        'pe_contract': top_pe_row['pe_contract'], 'pe_strike': top_pe_row['strike'], 'pe_price': top_pe_row['pe_price']
    }

# Scanner
selected = st.multiselect("ALL Symbols", FNO_SYMBOLS, default=FNO_SYMBOLS[:3])
if st.button("🚀 FULL SCAN", type="primary"):
    results = [scan_symbol(sym) for sym in selected]
    
    # Table - ALL columns
    table = pd.DataFrame([{
        'Symbol': r['symbol'], 'Spot': r['spot'], 'PCR': f"{r['pcr']:.2f}",
        f'CE {r["expiry"]}': r['ce_contract'][-12:], f'CE ₹': r['ce_price'],
        f'PE {r["expiry"]}': r['pe_contract'][-12:], f'PE ₹': r['pe_price']
    } for r in results])
    st.dataframe(table, use_container_width=True)
    
    # Signals for ALL
    st.markdown("## 🎯 Trade Signals")
    cols = st.columns(2)
    for i, r in enumerate(results):
        col = cols[i % 2]
        with col:
            if r['pcr'] > 1.05:
                st.success(f"**🟢 {r['symbol']}**")
                st.caption(f"SELL {r['pe_contract'][-20:]}  ₹{r['pe_price']}")
            elif r['pcr'] < 0.95:
                st.error(f"**🔴 {r['symbol']}**")
                st.caption(f"SELL {r['ce_contract'][-20:]}  ₹{r['ce_price']}")
            else:
                st.info(f"**🟡 {r['symbol']}**")
                st.caption(f"{r['ce_contract'][-12:]}CE + {r['pe_contract'][-12:]}PE")

st.caption(f"ALL symbols + Dynamic expiry | Debasish | {datetime.now().strftime('%H:%M')}")
