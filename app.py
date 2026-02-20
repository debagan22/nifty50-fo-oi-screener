import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(layout="wide", page_title="F&O Scanner")
st.title("📈 Nifty F&O OI Scanner - All Symbols")

# Realistic Nifty F&O data generator
def generate_fo_data(symbol, spot_base=24150):
    np.random.seed(hash(symbol) % 1000)  # Consistent per symbol
    spot = spot_base + np.random.normal(0, 50)
    strikes = np.arange(int(spot-400), int(spot+401), 50)
    
    calls = pd.DataFrame({
        'strike': strikes,
        'oi': np.random.exponential(150000, len(strikes)).astype(int),
        'premium': np.maximum(20, np.random.exponential(40, len(strikes)))
    })
    
    puts
