import streamlit as st
import pandas as pd
import numpy as np
from nsepython import nse_optionchain, index_fno_list  # Use optionchain for detailed data
from datetime import datetime

st.title("Nifty 50 F&O OI Screener with Buy/Sell Suggestions")

@st.cache_data(ttl=300)
def get_nifty_fo_stocks():
    return index_fno_list("NIFTY 50")

fo_stocks = get_nifty_fo_stocks()
selected_symbol = st.selectbox("Select Stock", fo_stocks[:20] if fo_stocks else [])  # Top 20 for demo

if selected_symbol and st.button("Analyze Option Chain & Suggest Trades"):
    with st.spinner("Fetching live option chain..."):
        chain_data = nse_optionchain(selected_symbol)  # Returns dict with 'records' having CE/PE
        
        if chain_data and 'records' in chain_data:
            df = pd.DataFrame(chain_data['records']['data'])
            ce_df = df[df['expiryDate'] == df['expiryDate'].iloc[0]]  # Nearest expiry
            pe_df = ce_df[ce_df['strikePrice'].isin(ce_df['strikePrice'])]  # Filter valid
            
            # Compute aggregates
            total_ce_oi = ce_df['CE']['openInterest'].sum()
            total_pe_oi = pe_df['PE']['openInterest'].sum()
            pcr_oi = total_pe_oi / total_ce_oi if total_ce_oi > 0 else 0
            
            # Max OI strikes
            max_ce_oi_strike = ce_df.loc[ce_df['CE']['openInterest'].idxmax(), 'strikePrice'] if not ce_df.empty else 0
            max_pe_oi_strike = pe_df.loc[pe_df['PE']['openInterest'].idxmax(), 'strikePrice'] if not pe_df.empty else 0
            
            st.subheader("Option Chain Summary")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("PCR (OI)", f"{pcr_oi:.2f}")
            col2.metric("Max Call OI Strike", max_ce_oi_strike)
            col3.metric("Max Put OI Strike", max_pe_oi_strike)
            col4.metric("LTP", f"₹{ce_df['CE']['lastPrice'].mean():.2f}")
            
            # Display chain table (top 10 strikes)
            chain_view = ce_df[['strikePrice', 'CE', 'PE']].head(10).copy()
            chain_view['CE_OI'] = chain_view['CE'].apply(lambda x: x['openInterest'] if isinstance(x, dict) else 0)
            chain_view['PE_OI'] = chain_view['PE'].apply(lambda x: x['openInterest'] if isinstance(x, dict) else 0)
            chain_view['CE_LTP'] = chain_view['CE'].apply(lambda x: x['lastPrice'] if isinstance(x, dict) else 0)
            chain_view['PE_LTP'] = chain_view['PE'].apply(lambda x: x['lastPrice'] if isinstance(x, dict) else 0)
            st.dataframe(chain_view[['strikePrice', 'CE_OI', 'PE_OI', 'CE_LTP', 'PE_LTP']])
            
            # Trade Suggestions
            st.subheader("Trade Suggestions (Educational)")
            if pcr_oi > 1.2:
                suggestion = f"""
                **Bullish Bias (High PCR)**: Puts unwinding.
                - **SELL Put** at {max_pe_oi_strike} strike, LTP ₹{pe_df['PE']['lastPrice'].loc[pe_df['strikePrice']==max_pe_oi_strike].iloc[0]:.2f} (Support level)
                - **BUY Call** at ATM (~LTP), LTP ₹{ce_df['CE']['lastPrice'].mean():.2f}
                Strategy: Bull Call Spread or Long Call.
                """
            elif pcr_oi < 0.8:
                suggestion = f"""
                **Bearish Bias (Low PCR)**: Calls building.
                - **SELL Call** at {max_ce_oi_strike} strike, LTP ₹{ce_df['CE']['lastPrice'].loc[ce_df['strikePrice']==max_ce_oi_strike].iloc[0]:.2f} (Resistance)
                - **BUY Put** at ATM (~LTP), LTP ₹{pe_df['PE']['lastPrice'].mean():.2f}
                Strategy: Bear Put Spread or Long Put.
                """
            else:
                suggestion = f"""
                **Neutral (PCR ~1)**: Range-bound {max_pe_oi_strike}-{max_ce_oi_strike}.
                - **SELL Straddle**: Sell Call {max_ce_oi_strike} LTP ₹{ce_df['CE']['lastPrice'].loc[ce_df['strikePrice']==max_ce_oi_strike].iloc[0]:.2f} & Put {max_pe_oi_strike} LTP ₹{pe_df['PE']['lastPrice'].loc[pe_df['strikePrice']==max_pe_oi_strike].iloc[0]:.2f}
                Risk: High theta decay near expiry.
                """
            
            st.markdown(suggestion)
            st.warning("Use SL 20-30% above premium. Not financial advice. Verify live data.")[web:17]
        else:
            st.error("No chain data. Check symbol/market hours.")

st.caption("Updated Feb 2026. Data via NSE API.")[web:24]
