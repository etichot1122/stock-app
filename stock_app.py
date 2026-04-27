# ===============================
# 📊 0050 選股系統（穩定券商版）
# ===============================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="0050選股系統", layout="wide")

# ===============================
# 📌 股票池
# ===============================
stocks = [
    "2330.TW","2308.TW","2317.TW","2454.TW","3711.TW","2891.TW",
    "2345.TW","2383.TW","2382.TW","2881.TW","2882.TW","2303.TW",
    "3017.TW","2360.TW","2887.TW","2412.TW","2884.TW","2885.TW",
    "2886.TW","2890.TW","2357.TW","3231.TW","2327.TW","1303.TW",
    "1216.TW","6669.TW","3653.TW","2880.TW","2892.TW","2883.TW",
    "2368.TW","2449.TW","2344.TW","2301.TW","5880.TW","2408.TW",
    "2603.TW","2002.TW","3008.TW","3661.TW","1301.TW","4904.TW",
    "3045.TW","2395.TW","2207.TW","6505.TW"
]

market = "^TWII"

# ===============================
# 📌 Data
# ===============================
@st.cache_data
def get_data(stock):
    try:
        df = yf.download(stock, period="6mo", auto_adjust=False, progress=False)
        return df.dropna()
    except:
        return pd.DataFrame()

@st.cache_data
def get_index():
    try:
        return yf.download(market, period="6mo", auto_adjust=False, progress=False).dropna()
    except:
        return pd.DataFrame()

# ===============================
# 📌 safe float（核心）
# ===============================
def safe(x):
    try:
        if isinstance(x, pd.Series):
            return float(x.iloc[-1])
        return float(x)
    except:
        return np.nan

# ===============================
# 📌 基本面（修正版）
# ===============================
def fundamental(stock):
    try:
        info = yf.Ticker(stock).info or {}

        pe = info.get("trailingPE", np.nan)
        roe = info.get("returnOnEquity", np.nan)
        mcap = info.get("marketCap", np.nan)

        return safe(pe), safe(roe), safe(mcap)
    except:
        return np.nan, np.nan, np.nan

# ===============================
# 📌 技術面
# ===============================
def tech(df, market_df):
    try:
        c = df["Close"]

        price = safe(c.iloc[-1])
        ma60 = safe(c.rolling(60).mean().iloc[-1])

        stock_ret = safe(c.pct_change(20).iloc[-1])
        market_ret = safe(market_df["Close"].pct_change(20).iloc[-1])

        alpha = stock_ret - market_ret

        return price, ma60, alpha
    except:
        return np.nan, np.nan, np.nan

# ===============================
# 📌 Sharpe（完全防炸）
# ===============================
def sharpe(df):
    try:
        r = df["Close"].pct_change().dropna()

        if len(r) < 30:
            return 0.0

        std = r.std()

        if pd.isna(std) or std == 0:
            return 0.0

        return float((r.mean() / std) * np.sqrt(252))
    except:
        return 0.0

# ===============================
# 📊 UI
# ===============================
st.title("📊 0050 選股系統（穩定券商版）")

market_df = get_index()

pe_limit = st.sidebar.slider("P/E上限", 5, 50, 25)
roe_limit = st.sidebar.slider("ROE下限", 0, 50, 15) / 100
mcap_limit = st.sidebar.slider("市值上限(億)", 100, 20000, 1000) * 1e8

rows = []

for s in stocks:
    df = get_data(s)
    if df.empty:
        continue

    pe, roe, mcap = fundamental(s)
    price, ma60, alpha = tech(df, market_df)
    sh = sharpe(df)

    ok = True

    # 基本面
    if not np.isnan(pe) and pe > pe_limit:
        ok = False

    if not np.isnan(roe) and roe < roe_limit:
        ok = False

    # 技術
    if not np.isnan(price) and not np.isnan(ma60):
        if price < ma60:
            ok = False

    if not np.isnan(alpha) and alpha < 0:
        ok = False

    # 市值
    if not np.isnan(mcap) and mcap > mcap_limit:
        ok = False

    rows.append([s, pe, roe, mcap, price, ma60, alpha, sh, ok])

df = pd.DataFrame(rows, columns=[
    "股票","PE","ROE","市值","現價","60MA","Alpha","Sharpe","通過"
])

df = df[df["通過"] == True]

if not df.empty:
    df = df.sort_values("Sharpe", ascending=False)

st.subheader("📊 篩選結果")
st.dataframe(df, use_container_width=True)
