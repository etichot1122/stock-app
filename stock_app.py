# ===============================
# 📊 0050 選股系統（穩定修正版 v1）
# ===============================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="0050選股系統", layout="wide")

# ===============================
# 📌 成分股
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
    df = yf.download(stock, period="6mo", auto_adjust=False)
    return df.dropna()

@st.cache_data
def get_index():
    return yf.download(market, period="6mo", auto_adjust=False).dropna()

# ===============================
# 📌 safe float（超重要）
# ===============================
def f(x):
    try:
        if isinstance(x, pd.Series):
            return float(x.iloc[-1])
        return float(x)
    except:
        return np.nan

# ===============================
# 📌 基本面（yfinance 不穩 → 允許 NaN）
# ===============================
def fundamental(stock):
    try:
        info = yf.Ticker(stock).info
        pe = info.get("trailingPE", np.nan)
        roe = info.get("returnOnEquity", np.nan)
        mcap = info.get("marketCap", np.nan)
        return pe, roe, mcap
    except:
        return np.nan, np.nan, np.nan

# ===============================
# 📌 技術面
# ===============================
def tech(df, market_df):
    try:
        c = df["Close"]

        price = f(c.iloc[-1])
        ma60 = f(c.rolling(60).mean().iloc[-1])

        stock_ret = f(c.pct_change(20).iloc[-1])
        market_ret = f(market_df["Close"].pct_change(20).iloc[-1])

        alpha20 = stock_ret - market_ret

        return price, ma60, alpha20
    except:
        return np.nan, np.nan, np.nan

# ===============================
# 📌 Sharpe（完全防爆）
# ===============================
def sharpe(df):
    try:
        r = df["Close"].pct_change().dropna()

        if len(r) < 30:
            return 0.0

        std = r.std()

        # 🔥 關鍵：避免 Series / NaN 爆炸
        if std is None or np.isnan(std) or std == 0:
            return 0.0

        return float((r.mean() / std) * np.sqrt(252))
    except:
        return 0.0

# ===============================
# 📊 UI
# ===============================
st.title("📊 0050 選股系統（穩定版）")

market_df = get_index()

results = []

for s in stocks:
    df = get_data(s)
    if df.empty:
        continue

    pe, roe, mcap = fundamental(s)
    price, ma60, alpha20 = tech(df, market_df)
    sh = sharpe(df)

    pass_filter = True

    # ===============================
    # 📌 基本面
    # ===============================
    if not np.isnan(pe) and pe > 25:
        pass_filter = False

    if not np.isnan(roe) and roe < 0.15:
        pass_filter = False

    # ===============================
    # 📌 技術面
    # ===============================
    if not np.isnan(price) and not np.isnan(ma60):
        if price < ma60:
            pass_filter = False

    if not np.isnan(alpha20) and alpha20 < 0:
        pass_filter = False

    # ===============================
    # 📌 市值
    # ===============================
    if not np.isnan(mcap) and mcap > 1e11:
        pass_filter = False

    results.append([
        s, pe, roe, mcap,
        price, ma60, alpha20,
        sh, pass_filter
    ])

df = pd.DataFrame(results, columns=[
    "股票","PE","ROE","市值",
    "現價","60MA","20日Alpha",
    "Sharpe","通過"
])

# ===============================
# 📌 篩選
# ===============================
df = df[df["通過"] == True]

# 🔥 修正 sort_values bug（NaN-safe）
df = df.sort_values("Sharpe", ascending=False, na_position="last")

# ===============================
# 📊 Output
# ===============================
st.subheader("📊 篩選結果")
st.dataframe(df, use_container_width=True)
