import streamlit as st
from alpha_vantage.timeseries import TimeSeries
import pandas as pd

st.title("🌟 LIVE Nifty F&O Signals - Alpha Vantage NSE")

API_KEY = "YOUR_FREE_KEY_HERE"  # Replace in 30s

@st.cache_data(ttl=300)
def get_nifty_data():
    ts = TimeSeries(key=API_KEY, output_format='pandas')
    data, meta = ts.get_intraday(symbol='NSE:NIFTY', interval='1min')
    return data

if st.button("📡 LIVE NIFTY DATA"):
    df = get_nifty_data()
    st.line_chart(df['4. close'])
    st.dataframe(df.tail(10))
    st.success("✅ LIVE NSE NIFTY 1min chart!")

st.info("Get key: alphavantage.co → 500 calls/day FREE")
