# ===============================
# 📊 台股選股器（FinMind 版本）
# ===============================

import streamlit as st
import pandas as pd
import numpy as np
from FinMind.data import DataLoader

st.set_page_config(page_title="台股選股器", layout="wide")

# ===============================
# 📌 Token（換成你的）
# ===============================
API_TOKEN = "YOUR_API_TOKEN"

fm = DataLoader()
fm.login_by_token(API_TOKEN)

# ===============================
# 📌 股票池（可自行加）
# ===============================
stocks = [
    "2330", "2317", "2454", "2303", "2412",
    "2308", "2382", "2881", "2882", "2891",
    "2886", "2884", "2885", "2880"
]

# ===============================
# 📌 抓價格
# ===============================
@st.cache_data
def get_price(stock):
    df = fm.taiwan_stock_daily(stock_id=stock, start_date="2024-01-01")
    return df

# ===============================
# 📌 財報（PE / ROE）
# ===============================
@st.cache_data
def get_fundamental(stock):
    df = fm.financial_statement(
        stock_id=stock,
        start_date="2023-01-01"
    )
    return df

# ===============================
# 📌 籌碼
# ===============================
@st.cache_data
def get_institution(stock):
    df = fm.taiwan_stock_institutional_investors(
        stock_id=stock,
        start_date="2024-01-01"
    )
    return df

# ===============================
# 📌 技術指標
# ===============================
def tech_score(df):
    df = df.copy()
    df["ma60"] = df["close"].rolling(60).mean()
    return df

# ===============================
# 📌 Sharpe
# ===============================
def sharpe(df):
    r = df["close"].pct_change().dropna()
    if len(r) < 30:
        return 0
    std = r.std()
    if std == 0:
        return 0
    return (r.mean() / std) * np.sqrt(252)

# ===============================
# 📊 UI
# ===============================
st.title("📊 台股選股器（FinMind版）")

rows = []

for s in stocks:
    price = get_price(s)

    if price.empty:
        continue

    price = tech_score(price)

    last_close = price["close"].iloc[-1]
    ma60 = price["ma60"].iloc[-1]
    sh = sharpe(price)

    # 技術條件
    trend_ok = last_close > ma60

    rows.append([
        s,
        last_close,
        ma60,
        sh,
        trend_ok
    ])

df = pd.DataFrame(rows, columns=[
    "股票", "收盤價", "60MA", "Sharpe", "多頭"
])

# ===============================
# 📌 篩選
# ===============================
df = df[df["多頭"] == True]
df = df.sort_values("Sharpe", ascending=False)

st.subheader("📊 篩選結果")
st.dataframe(df, use_container_width=True)

# ===============================
# 📈 報酬曲線（簡化版）
# ===============================
st.subheader("📈 報酬曲線")

top = df.head(5)["股票"]

portfolio = pd.DataFrame()

for s in top:
    d = get_price(s)
    portfolio[s] = d["close"].pct_change()

portfolio["avg"] = portfolio.mean(axis=1)
cum = (1 + portfolio["avg"]).cumprod()

st.line_chart(cum)
