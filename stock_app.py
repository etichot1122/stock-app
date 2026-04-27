# ===============================
# 📊 0050 券商級選股系統（穩定完整版）
# ===============================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="0050選股系統", layout="wide")

# ===============================
# 📌 0050 成分股（完整版）
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
    df = df.dropna()
    return df

@st.cache_data
def get_index():
    df = yf.download(market, period="6mo", auto_adjust=False)
    return df.dropna()

# ===============================
# 📌 safe float（核心修正）
# ===============================
def safe(x):
    try:
        if isinstance(x, pd.Series):
            return float(x.iloc[-1])
        return float(x)
    except:
        return np.nan

# ===============================
# 📌 基本面（完全防 None）
# ===============================
def fundamental(stock):
    try:
        info = yf.Ticker(stock).info
        pe = safe(info.get("trailingPE"))
        roe = safe(info.get("returnOnEquity"))
        mcap = safe(info.get("marketCap"))
        return pe, roe, mcap
    except:
        return np.nan, np.nan, np.nan

# ===============================
# 📌 技術面（券商風格）
# ===============================
def tech(df, market_df):
    try:
        c = df["Close"]

        price = safe(c.iloc[-1])
        ma60 = safe(c.rolling(60).mean().iloc[-1])

        stock_ret = safe(c.pct_change(20).iloc[-1])
        market_ret = safe(market_df["Close"].pct_change(20).iloc[-1])

        alpha20 = stock_ret - market_ret

        return price, ma60, alpha20
    except:
        return np.nan, np.nan, np.nan

# ===============================
# 📌 Sharpe（100% 防炸版）
# ===============================
def sharpe(df):
    try:
        r = df["Close"].pct_change().dropna()

        if len(r) < 30:
            return 0.0

        std = float(r.std())
        mean = float(r.mean())

        if np.isnan(std) or std == 0:
            return 0.0

        return float((mean / std) * np.sqrt(252))
    except:
        return 0.0

# ===============================
# 📊 UI
# ===============================
st.title("📊 0050 券商級選股系統（穩定版）")

market_df = get_index()

results = []

# ===============================
# 📌 主迴圈
# ===============================
for s in stocks:
    df = get_data(s)
    if df.empty:
        continue

    pe, roe, mcap = fundamental(s)
    price, ma60, alpha20 = tech(df, market_df)
    sh = sharpe(df)

    # ===============================
    # 📌 防 None 顯示
    # ===============================
    pe = pe if not pd.isna(pe) else np.nan
    roe = roe if not pd.isna(roe) else np.nan
    mcap = mcap if not pd.isna(mcap) else np.nan

    # ===============================
    # 📌 總分（券商模型）
    # ===============================
    score = 0

    if not np.isnan(pe):
        score += max(0, 30 - pe)

    if not np.isnan(roe):
        score += roe * 200

    if not np.isnan(alpha20):
        score += alpha20 * 100

    score += sh * 10

    results.append([
        s, pe, roe, mcap,
        price, ma60, alpha20,
        sh, score
    ])

# ===============================
# 📊 DataFrame（修正排序 bug）
# ===============================
df = pd.DataFrame(results, columns=[
    "股票","PE","ROE","市值",
    "現價","60MA","20日Alpha",
    "Sharpe","總分"
])

# 保證全部 numeric
df["總分"] = pd.to_numeric(df["總分"], errors="coerce")
df = df.dropna(subset=["總分"])

# 排序（避免你之前 crash）
df = df.sort_values(by="總分", ascending=False)

# ===============================
# 📊 Sidebar（券商風格）
# ===============================
st.sidebar.header("📌 篩選器")

min_score = st.sidebar.slider("最低總分", 0, 500, 50)
only_positive_alpha = st.sidebar.checkbox("只看資金流入(Alpha > 0)", True)

filtered = df.copy()

filtered = filtered[filtered["總分"] >= min_score]

if only_positive_alpha:
    filtered = filtered[filtered["20日Alpha"] > 0]

# ===============================
# 📊 Output
# ===============================
st.subheader("📊 篩選結果（券商風格）")
st.dataframe(filtered, use_container_width=True)
