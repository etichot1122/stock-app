import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="券商級選股系統", layout="wide")

# ===============================
# 📌 股票池（0050 + 強化）
# ===============================
stocks = [
    "2330.TW","2308.TW","2317.TW","2454.TW","2382.TW",
    "2881.TW","2882.TW","2886.TW","2891.TW","2303.TW",
    "3711.TW","2412.TW","1303.TW","1301.TW","2002.TW",
    "2603.TW","3008.TW","2383.TW","2357.TW","3045.TW"
]

market = "^TWII"

# ===============================
# 📌 Data
# ===============================
@st.cache_data
def get_data(stock):
    return yf.download(stock, period="1y", auto_adjust=False).dropna()

@st.cache_data
def get_index():
    return yf.download(market, period="1y", auto_adjust=False).dropna()

# ===============================
# 📌 技術指標
# ===============================
def tech_score(df):
    c = df["Close"]

    ma20 = c.rolling(20).mean()
    ma60 = c.rolling(60).mean()

    rsi = 100 - (100 / (1 + c.pct_change().rolling(14).mean()))

    trend = 0

    if c.iloc[-1] > ma20.iloc[-1]:
        trend += 1
    if c.iloc[-1] > ma60.iloc[-1]:
        trend += 1
    if ma20.iloc[-1] > ma60.iloc[-1]:
        trend += 1
    if rsi.iloc[-1] > 50:
        trend += 1

    return trend / 4 * 100

# ===============================
# 📌 動能
# ===============================
def momentum(df, market_df):
    c = df["Close"]

    r5 = c.pct_change(5).iloc[-1]
    r20 = c.pct_change(20).iloc[-1]
    r60 = c.pct_change(60).iloc[-1]

    mkt = market_df["Close"].pct_change(20).iloc[-1]

    alpha = r20 - mkt

    return (r5*0.2 + r20*0.5 + r60*0.3) * 100 + alpha * 100

# ===============================
# 📌 籌碼（用量能替代）
# ===============================
def chip(df):
    v = df["Volume"]

    if len(v) < 20:
        return 0

    return (v.tail(5).mean() / v.tail(20).mean()) * 100

# ===============================
# 📌 基本面（簡化穩定版）
# ===============================
def fundamental(stock):
    try:
        info = yf.Ticker(stock).info
        pb = info.get("priceToBook", np.nan)

        if np.isnan(pb):
            return 50

        return max(0, 100 - pb * 10)
    except:
        return 50

# ===============================
# 📊 UI
# ===============================
st.title("📊 券商級選股系統 v1")

market_df = get_index()

results = []

for s in stocks:
    df = get_data(s)

    if df.empty:
        continue

    t = tech_score(df)
    m = momentum(df, market_df)
    c = chip(df)
    f = fundamental(s)

    score = (
        t * 0.4 +
        m * 0.3 +
        c * 0.2 +
        f * 0.1
    )

    results.append([s, t, m, c, f, score])

df = pd.DataFrame(results, columns=[
    "股票","技術","動能","籌碼","基本面","總分"
])

df = df.sort_values("總分", ascending=False)

st.subheader("📊 券商級選股排名")
st.dataframe(df, use_container_width=True)
