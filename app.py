import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(layout="wide", page_title="Live F&O Scanner")
st.title("🔥 LIVE Nifty F&O OI Scanner")

@st.cache_data(ttl=300)
def get_live_data(symbol):
    ticker = yf.Ticker(symbol)
    spot = ticker.fast_info['lastPrice']
    
    try:
        chain = ticker.option_chain(ticker.options
