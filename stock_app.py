# ===============================
# 📊 0050選股系統（完整版 + 報酬曲線 + 穩定修正版）
# ===============================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="0050選股系統", layout="wide")

# ===============================
# 📌 股票池（0050擴展）
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
    df = yf.download(market, period="6mo", auto_adjust=False)
    return df.dropna()

# ===============================
# 📌 safe float（完全防炸）
# ===============================
def safe(x):
    try:
        if isinstance(x, pd.Series):
            return float(x.iloc[-1])
        return float(x)
    except:
        return np.nan

# ===============================
# 📌 基本面
# ===============================
def fundamental(stock):
    try:
        info = yf.Ticker(stock).info
        return (
            info.get("trailingPE", np.nan),
            info.get("returnOnEquity", np.nan),
            info.get("marketCap", np.nan),
        )
    except:
        return np.nan, np.nan, np.nan

# ===============================
# 📌 技術面
# ===============================
def tech(df, market_df):
    try:
        c = df["Close"]

        price = safe(c.iloc[-1])
        ma60 = safe(c.rolling(60).mean())

        stock_ret = safe(c.pct_change(20))
        market_ret = safe(market_df["Close"].pct_change(20))

        alpha = stock_ret - market_ret

        return price, ma60, alpha
    except:
        return np.nan, np.nan, np.nan

# ===============================
# 📌 Sharpe（100%穩定版）
# ===============================
def sharpe(df):
    r = df["Close"].pct_change().dropna()

    if len(r) < 30:
        return 0.0

    mean = r.mean()
    std = r.std()

    mean = float(mean.iloc[0]) if isinstance(mean, pd.Series) else float(mean)
    std = float(std.iloc[0]) if isinstance(std, pd.Series) else float(std)

    if np.isnan(std) or std == 0:
        return 0.0

    return float((mean / std) * np.sqrt(252))

# ===============================
# 📊 UI
# ===============================
st.title("📊 0050選股系統（券商級穩定版）")

market_df = get_index()

rows = []

# ===============================
# 📌 主迴圈
# ===============================
for s in stocks:
    df = get_data(s)
    if df.empty:
        continue

    pe, roe, mcap = fundamental(s)
    price, ma60, alpha = tech(df, market_df)
    sh = sharpe(df)

    ok = True

    # 基本面
    if not np.isnan(pe) and pe > 25:
        ok = False
    if not np.isnan(roe) and roe < 0.15:
        ok = False

    # 技術面
    if not np.isnan(price) and not np.isnan(ma60):
        if price < ma60:
            ok = False

    if not np.isnan(alpha) and alpha < 0:
        ok = False

    # 市值
    if not np.isnan(mcap) and mcap > 1e11:
        ok = False

    rows.append([s, pe, roe, mcap, price, ma60, alpha, sh, ok])

df = pd.DataFrame(rows, columns=[
    "股票","PE","ROE","市值","現價","60MA","Alpha","Sharpe","通過"
])

# 防 sort bug
df["Sharpe"] = pd.to_numeric(df["Sharpe"], errors="coerce")
df = df.dropna(subset=["Sharpe"])

df = df[df["通過"] == True]
df = df.sort_values(by="Sharpe", ascending=False)

# ===============================
# 📊 篩選結果
# ===============================
st.subheader("📊 篩選結果")
st.dataframe(df, use_container_width=True)

# ===============================
# 📈 報酬曲線（升級版）
# ===============================
st.subheader("📈 投資報酬曲線")

top_n = st.slider("選幾檔", 1, 10, 5)
top_stocks = df.head(top_n)["股票"].tolist()

portfolio = pd.DataFrame()

for s in top_stocks:
    data = get_data(s)
    portfolio[s] = data["Close"].pct_change()

portfolio["portfolio"] = portfolio.mean(axis=1)
cum = (1 + portfolio["portfolio"].fillna(0)).cumprod()

st.line_chart(cum)
