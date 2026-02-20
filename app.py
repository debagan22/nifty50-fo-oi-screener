import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(layout="wide", page_title="Live F&O Scanner")
st.title("🚀 Nifty F&O OI Scanner - Complete")

@st.cache_data(ttl=300)
def generate_fo_analysis(symbol):
    """Complete F&O analysis engine"""
    # Realistic market data
    spot = 24150 + np.random.normal(0, 30)
    strikes = np.arange(int(spot - 400), int(spot
