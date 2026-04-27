import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="券商級選股系統 v2", layout="wide")

# ===============================
# 📌 股票池
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
    try:
        df = yf.download(stock, period="1y", auto_adjust=False)
        return df.dropna()
    except:
        return pd.DataFrame()

@st.cache_data
def get_index():
    try:
        df = yf.download(market, period="1y", auto_adjust=False)
        return df.dropna()
    except:
        return pd.DataFrame()

# ===============================
# 📌 強制轉 float（核心修正）
# ===============================
def safe(x):
    try:
        if isinstance(x, pd.Series):
            x = x.dropna()
            return float(x.iloc[-1]) if len(x) > 0 else 0.0
        return float(x)
    except:
        return 0.0

# ===============================
# 📌 技術分數
# ===============================
def tech_score(df):
    try:
        c = df["Close"].dropna()
        if len(c) < 60:
            return 0.0

        ma20 = c.rolling(20).mean()
        ma60 = c.rolling(60).mean()

        price = safe(c.iloc[-1])
        ma20_v = safe(ma20)
        ma60_v = safe(ma60)

        # RSI
        delta = c.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()

        rs = gain / (loss + 1e-9)
        rsi = 100 - (100 / (1 + rs))
        rsi_v = safe(rsi)

        score = 0.0

        if price > ma20_v:
            score += 25
        if price > ma60_v:
            score += 25
        if ma20_v > ma60_v:
            score += 25
        if rsi_v > 50:
            score += 25

        return float(score)

    except:
        return 0.0

# ===============================
# 📌 動能
# ===============================
def momentum(df, market_df):
    try:
        c = df["Close"].dropna()
        m = market_df["Close"].dropna()

        if len(c) < 30 or len(m) < 30:
            return 0.0

        r5 = safe(c.pct_change(5))
        r20 = safe(c.pct_change(20))
        r60 = safe(c.pct_change(60))
        m20 = safe(m.pct_change(20))

        alpha = r20 - m20

        return float((r5*0.2 + r20*0.5 + r60*0.3) * 100 + alpha * 100)

    except:
        return 0.0

# ===============================
# 📌 籌碼（量能）
# ===============================
def chip(df):
    try:
        v = df["Volume"].dropna()

        if len(v) < 20:
            return 0.0

        return float(v.tail(5).mean() / (v.tail(20).mean() + 1e-9) * 100)

    except:
        return 0.0

# ===============================
# 📌 基本面（穩定版）
# ===============================
def fundamental(stock):
    try:
        info = yf.Ticker(stock).info
        pb = info.get("priceToBook", np.nan)

        if pb is None or np.isnan(pb):
            return 50.0

        return float(max(0, 100 - pb * 10))

    except:
        return 50.0

# ===============================
# 📊 UI
# ===============================
st.title("📊 券商級選股系統 v2（穩定版）")

market_df = get_index()
results = []

for s in stocks:
    df = get_data(s)

    if df.empty or len(df) < 60:
        continue

    t = safe(tech_score(df))
    m = safe(momentum(df, market_df))
    c = safe(chip(df))
    fscore = safe(fundamental(s))

    total = float(
        t * 0.4 +
        m * 0.3 +
        c * 0.2 +
        fscore * 0.1
    )

    results.append([s, t, m, c, fscore, total])

df = pd.DataFrame(results, columns=[
    "股票","技術","動能","籌碼","基本面","總分"
])

# ===============================
# 📌 防炸排序（關鍵）
# ===============================
df["總分"] = pd.to_numeric(df["總分"], errors="coerce").fillna(0)
df = df.dropna(subset=["總分"])
df = df.sort_values("總分", ascending=False)

# ===============================
# 📌 Filter
# ===============================
st.sidebar.header("篩選")

min_score = st.sidebar.slider("最低分數", 0, 200, 50)

df = df[df["總分"] >= min_score]

# ===============================
# 📊 Output
# ===============================
st.subheader("📊 排名結果")
st.dataframe(df, use_container_width=True)
