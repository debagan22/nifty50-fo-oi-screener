import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(layout="wide", page_title="Live F&O Scanner")
st.title("⚡ LIVE Nifty F&O Signals")

@st.cache_data(ttl=300)
def get_live_fo(symbol):
    """Live yfinance NSE data + OI logic"""
    ticker = yf.Ticker(symbol)
    
    # Live spot + options
    spot = ticker.fast_info['lastPrice']
    try:
        chain = ticker.option_chain(ticker.options[0])
        calls = chain.calls.copy()
        puts
