# ===============================
# 📊 台股選股器（穩定版 A）
# ===============================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="台股選股器", layout="wide")

# ===============================
# 📌 股票池
# ===============================
stocks = [
    "2330.TW","2317.TW","2454.TW","2303.TW","2412.TW",
    "2308.TW","2382.TW","2881.TW","2882.TW","2891.TW",
    "2886.TW","2884.TW","2885.TW","1303.TW","2002.TW"
]

market = "^TWII"

# ===============================
# 📌 資料下載
# ===============================
@st.cache_data
def get_data(stock):
    try:
        return yf.download(stock, period="6mo", auto_adjust=False, progress=False).dropna()
    except:
        return pd.DataFrame()

@st.cache_data
def get_index():
    return yf.download(market, period="6mo", auto_adjust=False, progress=False).dropna()

# ===============================
# 📌 safe float
# ===============================
def safe(x):
    try:
        if isinstance(x, pd.Series):
            return float(x.iloc[-1])
        return float(x)
    except:
        return np.nan

# ===============================
# 📌 基本面（fallback版）
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
    c = df["Close"]

    price = safe(c.iloc[-1])
    ma60 = safe(c.rolling(60).mean().iloc[-1])

    stock_ret = safe(c.pct_change(20).iloc[-1])
    market_ret = safe(market_df["Close"].pct_change(20).iloc[-1])

    alpha = stock_ret - market_ret

    return price, ma60, alpha

# ===============================
# 📌 Sharpe
# ===============================
def sharpe(df):
    r = df["Close"].pct_change().dropna()

    if len(r) < 30:
        return 0.0

    std = r.std()
    if pd.isna(std) or std == 0:
        return 0.0

    return float((r.mean() / std) * np.sqrt(252))

# ===============================
# 📊 UI
# ===============================
st.title("📊 台股選股器（穩定版 A）")

market_df = get_index()

rows = []

for s in stocks:
    df = get_data(s)
    if df.empty:
        continue

    pe, roe, mcap = fundamental(s)
    price, ma60, alpha = tech(df, market_df)
    sh = sharpe(df)

    ok = True

    if not np.isnan(price) and not np.isnan(ma60):
        if price < ma60:
            ok = False

    if not np.isnan(alpha) and alpha < 0:
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

# ===============================
# 📈 報酬曲線
# ===============================
st.subheader("📈 投資組合報酬")

top_n = st.slider("選幾檔", 1, 5, 3)

top = df.head(top_n)["股票"]

portfolio = pd.DataFrame()

for s in top:
    d = get_data(s)
    portfolio[s] = d["Close"].pct_change()

portfolio["avg"] = portfolio.mean(axis=1)
cum = (1 + portfolio["avg"]).cumprod()

st.line_chart(cum)
