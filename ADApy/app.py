import streamlit as st
import requests
import pandas as pd
import altair as alt
from streamlit_autorefresh import st_autorefresh

# =======================
# Streamlit Page Config
# =======================
st.set_page_config(page_title="Krypto Dashboard", page_icon="🚀", layout="centered")
st.title("🚀 Krypto Dashboard – ADA / SNEK / CHAD")

# Auto Refresh alle 3 Sekunden
st_autorefresh(interval=3000, limit=None, key="autorefresh")

# =======================
# Konfiguration Coins
# =======================
coins = {
    "ADA": {
        "coingecko_id": "cardano",
        "minswap_pool_id": "c64a3d1fb6bb0e92cfdd84e485d42767bc13f6a03ae67a2bc5fb6fc59f3a0b50",  # Beispiel ADA Pool
    },
    "SNEK": {
        "coingecko_id": "snek",
        "minswap_pool_id": "9f5c22a8b8c648bdbb5d9010df17bb642f71e8f12bb3b03c1fbc7f6cb0472c48",  # Beispiel SNEK Pool
    },
    "CHAD": {
        "coingecko_id": "charles-the-chad",
        "minswap_pool_id": None  # kein Pool ID hier als Beispiel
    }
}

# =======================
# API Funktionen
# =======================

def get_price_minswap(pool_id):
    try:
        url = f"https://api-mainnet-prod.minswap.org/asset/{pool_id}"
        response = requests.get(url, timeout=5).json()
        return None, None  # Minswap (OnChain Pool API kann später erweitert werden)
    except:
        return None, None

def get_price_coingecko(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=eur&include_24hr_change=true"
        data = requests.get(url, timeout=5).json()
        price = data[coin_id]["eur"]
        change = data[coin_id]["eur_24h_change"]
        return price, change
    except:
        return None, None

def get_price_dexscreener(symbol):
    try:
        url = f"https://api.dexscreener.com/latest/dex/search?q={symbol}"
        data = requests.get(url, timeout=5).json()
        pair = data["pairs"][0]
        price_usd = float(pair["priceUsd"])
        price_eur = price_usd * get_usd_to_eur()
        change = float(pair["priceChange"]["h24"])
        return price_eur, change
    except:
        return None, None

def get_price_binance():
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr?symbol=ADAEUR"
        data = requests.get(url, timeout=5).json()
        price = float(data["lastPrice"])
        change = float(data["priceChangePercent"])
        return price, change
    except:
        return None, None

def get_price_hardcoded(coin_name):
    dummy_prices = {
        "ADA": 0.35,
        "SNEK": 0.00015,
        "CHAD": 0.0001
    }
    return dummy_prices[coin_name], None

def get_usd_to_eur():
    try:
        url = "https://api.exchangerate.host/latest?base=USD&symbols=EUR"
        data = requests.get(url, timeout=5).json()
        return float(data["rates"]["EUR"])
    except:
        return 0.92

def get_history_coingecko(coin_id, days):
    try:
        interval = "hourly" if days == 1 else "daily"
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=eur&days={days}&interval={interval}"
        response = requests.get(url, timeout=10).json()
        prices = response['prices']
        df = pd.DataFrame(prices, columns=["timestamp", "price"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df["smooth"] = df["price"].rolling(window=3, min_periods=1).mean()
        return df
    except:
        return None

# =======================
# Fallback Controller
# =======================

def get_price_aggregated(coin_name):
    fallback_reason = []

    pool_id = coins[coin_name]["minswap_pool_id"]

    if pool_id:
        price, change = get_price_minswap(pool_id)
        if price:
            return price, change, "Minswap", fallback_reason
        fallback_reason.append("Minswap failed")

    price, change = get_price_coingecko(coins[coin_name]["coingecko_id"])
    if price:
        return price, change, "CoinGecko", fallback_reason
    fallback_reason.append("CoinGecko failed")

    price, change = get_price_dexscreener(coin_name)
    if price:
        return price, change, "DexScreener", fallback_reason
    fallback_reason.append("DexScreener failed")

    if coin_name == "ADA":
        price, change = get_price_binance()
        if price:
            return price, change, "Binance", fallback_reason
        fallback_reason.append("Binance failed")

    price, change = get_price_hardcoded(coin_name)
    return price, change, "Hardcoded", fallback_reason

# =======================
# UI Schleife
# =======================

for coin_name in coins:
    st.header(coin_name)

    price, change, source, fallbacks = get_price_aggregated(coin_name)

    if price:
        delta_str = f"{change:+.2f}%" if change is not None else "n/a"
        color = "🟢" if change is not None and change >= 0 else "🔴"
        st.metric(label=f"Aktueller Preis ({source})", value=f"{price:.6f} EUR", delta=f"{delta_str} {color}")

        if fallbacks:
            st.caption(f"Fallback aktiv → Fehlerkette: {', '.join(fallbacks)}")
    else:
        st.error("Komplett keine Daten verfügbar!")

    st.subheader("Preisverlauf")
    period_selection = st.selectbox("Zeitraum auswählen", options={"24h": 1, "7 Tage": 7, "30 Tage": 30}, key=coin_name)

    df = get_history_coingecko(coins[coin_name]["coingecko_id"], period_selection)
    if df is not None and not df.empty:
        chart = alt.Chart(df).mark_line(color="#FF9900").encode(
            x=alt.X('timestamp:T', title="Zeit"),
            y=alt.Y('smooth:Q', title="Preis (EUR)", scale=alt.Scale(zero=False))
        ).properties(height=400, width=700)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.write("*(Noch keine historischen Daten verfügbar)*")
        st.altair_chart(alt.Chart(pd.DataFrame({"x": [], "y": []})).mark_line(), use_container_width=True)
