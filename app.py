import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd
import streamlit as st

st.set_page_config(page_title="SatsCommander Live", layout="wide")

st.markdown("""
<div style="background:linear-gradient(90deg,#111827,#0a0f1c);
padding:24px;border-radius:16px;border:1px solid #00d1ff;margin-bottom:20px;">
<h1 style="color:white;margin:0;">SatsCommander</h1>
<p style="color:#f7931a;margin:0;font-weight:700;font-size:18px;">Turn Altcoins Into Bitcoin</p>
<p style="color:#9aa4b2;margin-top:6px;">Live-price execution engine for stacking sats.</p>
</div>
""", unsafe_allow_html=True)

COINGECKO_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "LINK": "chainlink",
    "SOL": "solana",
    "ADA": "cardano",
    "XRP": "ripple",
    "SUI": "sui",
    "RENDER": "render-token",
    "TAO": "bittensor",
    "AVAX": "avalanche-2",
    "DOT": "polkadot",
    "MATIC": "matic-network",
    "POL": "polygon-ecosystem-token",
    "GRT": "the-graph",
    "AIOZ": "aioz-network",
    "STX": "blockstack",
    "QNT": "quant-network",
    "CRO": "crypto-com-chain",
    "ENJ": "enjincoin",
    "CELO": "celo",
}

DEMO = pd.DataFrame([
    {"Coin": "LINK", "Amount": 150.0, "Trigger Price": 20.00, "Sell %": 0.25},
    {"Coin": "SOL", "Amount": 12.0, "Trigger Price": 150.00, "Sell %": 0.25},
    {"Coin": "ETH", "Amount": 2.0, "Trigger Price": 3500.00, "Sell %": 0.15},
    {"Coin": "ADA", "Amount": 5000.0, "Trigger Price": 0.50, "Sell %": 0.30},
])

if "portfolio" not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(columns=["Coin", "Amount", "Trigger Price", "Sell %"])

if "executions" not in st.session_state:
    st.session_state.executions = []

if "btc_total" not in st.session_state:
    st.session_state.btc_total = 0.0

st.sidebar.header("SatsCommander Setup")
mode = st.sidebar.radio("Data Mode", ["Demo Portfolio", "Private Session Portfolio"])
price_mode = st.sidebar.radio("Price Mode", ["Live CoinGecko Prices", "Manual Prices"], help="Live prices use CoinGecko. Manual mode is fallback if an ID is unsupported.")
st.sidebar.caption("Private Session data is not saved to GitHub. It only exists in your browser session.")

@st.cache_data(ttl=60)
def fetch_prices(symbols):
    ids = []
    symbol_to_id = {}
    for sym in symbols:
        sym = str(sym).upper().strip()
        cg_id = COINGECKO_IDS.get(sym)
        if cg_id:
            ids.append(cg_id)
            symbol_to_id[sym] = cg_id

    if not ids:
        return {}, "No supported CoinGecko IDs found."

    params = urlencode({
        "ids": ",".join(sorted(set(ids))),
        "vs_currencies": "usd",
        "include_24hr_change": "true",
    })
    url = f"https://api.coingecko.com/api/v3/simple/price?{params}"

    try:
        req = Request(url, headers={"User-Agent": "SatsCommander/1.0"})
        with urlopen(req, timeout=10) as response:
            raw = response.read().decode("utf-8")
            data = json.loads(raw)

        prices = {}
        changes = {}
        for sym, cg_id in symbol_to_id.items():
            prices[sym] = data.get(cg_id, {}).get("usd", 0)
            changes[sym] = data.get(cg_id, {}).get("usd_24h_change", None)

        return {"prices": prices, "changes": changes}, None
    except Exception as e:
        return {}, f"Live price fetch failed: {e}"

def normalize(df):
    required = ["Coin", "Amount", "Trigger Price", "Sell %"]
    for col in required:
        if col not in df.columns:
            df[col] = "" if col == "Coin" else 0
    df = df[required].copy()
    df["Coin"] = df["Coin"].astype(str).str.upper().str.strip()
    for col in ["Amount", "Trigger Price", "Sell %"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df

def calculate(df, btc_price, live_prices=None, manual_prices=None, changes=None):
    df = normalize(df)
    current_prices = []
    alerts = []
    commands = []
    gross_sells = []
    btc_captured = []
    progress_vals = []
    change_vals = []

    live_prices = live_prices or {}
    manual_prices = manual_prices or {}
    changes = changes or {}

    for _, r in df.iterrows():
        coin = r["Coin"]
        amount = float(r["Amount"])
        trigger = float(r["Trigger Price"])
        sell_pct = float(r["Sell %"])
        price = float(live_prices.get(coin, manual_prices.get(coin, 0)) or 0)

        value = amount * price
        progress = price / trigger if trigger > 0 else 0
        gross_sell = 0

        if coin == "" or amount <= 0:
            alert = "INCOMPLETE"
            command = "ADD POSITION DETAILS"
        elif price <= 0:
            alert = "NO PRICE"
            command = f"ADD/VERIFY PRICE FOR {coin}"
        elif trigger <= 0:
            alert = "NO TRIGGER"
            command = f"SET TRIGGER FOR {coin}"
        elif price >= trigger:
            alert = "SELL NOW"
            gross_sell = value * sell_pct
            command = f"SELL {coin} NOW — {sell_pct:.0%}"
        elif progress >= 0.80:
            alert = "PREPARE"
            command = f"{coin} IS ARMED — PREPARE"
        elif progress >= 0.60:
            alert = "WATCH"
            command = f"TRACK {coin} — APPROACHING LEVEL"
        else:
            alert = "STANDBY"
            command = "STANDBY — NO ACTION"

        btc = gross_sell / btc_price if btc_price else 0

        current_prices.append(price)
        alerts.append(alert)
        commands.append(command)
        gross_sells.append(gross_sell)
        btc_captured.append(btc)
        progress_vals.append(progress)
        change_vals.append(changes.get(coin))

    df["Current Price"] = current_prices
    df["24h Change %"] = change_vals
    df["Position Value"] = df["Amount"] * df["Current Price"]
    df["Progress to Trigger"] = progress_vals
    df["Alert"] = alerts
    df["Command"] = commands
    df["Gross Sell"] = gross_sells
    df["BTC Captured"] = btc_captured

    score_map = {"SELL NOW": 100, "PREPARE": 70, "WATCH": 40, "STANDBY": 10, "NO TRIGGER": 5, "NO PRICE": 3, "INCOMPLETE": 0}
    df["Priority"] = df["Alert"].map(score_map).fillna(0)
    return df.sort_values(["Priority", "BTC Captured"], ascending=[False, False])

tabs = st.tabs(["1. Command Center", "2. Portfolio Input", "3. Execution Log", "4. Supported Coins"])

with tabs[1]:
    st.header("Step 1: Load Portfolio")

    if mode == "Demo Portfolio":
        portfolio = DEMO.copy()
        st.success("Demo Portfolio active — safe sample data.")
        st.dataframe(portfolio, use_container_width=True, hide_index=True)
    else:
        st.warning("Private Session Portfolio active — data is session-only and not saved to GitHub.")
        uploaded = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded:
            st.session_state.portfolio = normalize(pd.read_csv(uploaded))

        st.session_state.portfolio = st.data_editor(
            st.session_state.portfolio,
            num_rows="dynamic",
            use_container_width=True,
            key="portfolio_editor"
        )
        portfolio = st.session_state.portfolio.copy()

    st.download_button(
        "Download CSV Template",
        pd.DataFrame(columns=["Coin", "Amount", "Trigger Price", "Sell %"]).to_csv(index=False).encode(),
        "satscommander_template.csv",
        "text/csv"
    )

with tabs[0]:
    portfolio = DEMO.copy() if mode == "Demo Portfolio" else st.session_state.portfolio.copy()
    portfolio = normalize(portfolio)

    symbols = portfolio["Coin"].dropna().astype(str).str.upper().tolist()
    price_payload, error = fetch_prices(symbols) if price_mode == "Live CoinGecko Prices" else ({}, None)
    live_prices = price_payload.get("prices", {}) if isinstance(price_payload, dict) else {}
    changes = price_payload.get("changes", {}) if isinstance(price_payload, dict) else {}

    if error:
        st.warning(error)

    btc_price = live_prices.get("BTC")
    if not btc_price:
        btc_price = st.sidebar.number_input("Manual BTC Price", value=78000.00, min_value=0.0, step=100.0)

    manual_prices = {}
    if price_mode == "Manual Prices":
        st.sidebar.subheader("Manual Coin Prices")
        for sym in symbols:
            manual_prices[sym] = st.sidebar.number_input(f"{sym} Price", value=0.0, min_value=0.0, key=f"manual_{sym}")

    results = calculate(portfolio, btc_price, live_prices=live_prices, manual_prices=manual_prices, changes=changes)

    st.header("Step 2: Follow the Command")

    if results.empty or len(results[results["Coin"] != ""]) == 0:
        st.info("Load a portfolio first in the Portfolio Input tab.")
    else:
        total_value = results["Position Value"].sum()
        active_sells = results[results["Alert"] == "SELL NOW"]
        potential_btc = active_sells["BTC Captured"].sum()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Portfolio Value", f"${total_value:,.2f}")
        c2.metric("BTC Price", f"${btc_price:,.2f}")
        c3.metric("Active Sell Signals", len(active_sells))
        c4.metric("Potential BTC Captured", f"{potential_btc:.8f}")

        st.markdown("---")
        top = results.iloc[0]
        st.subheader("DO THIS NOW")

        if top["Alert"] == "SELL NOW":
            st.error(f"{top['Command']}  |  Est. BTC Captured: {top['BTC Captured']:.8f}")
        elif top["Alert"] == "PREPARE":
            st.success(f"{top['Command']}  |  Price is {top['Progress to Trigger']:.0%} of trigger.")
        elif top["Alert"] == "WATCH":
            st.warning(f"{top['Command']}  |  Price is {top['Progress to Trigger']:.0%} of trigger.")
        elif top["Alert"] == "STANDBY":
            st.info("STANDBY — NO ACTION. Do not force a trade.")
        else:
            st.info(top["Command"])

        if st.button("EXECUTE TOP COMMAND", type="primary", disabled=(top["Alert"] != "SELL NOW")):
            st.session_state.executions.append({
                "Coin": top["Coin"],
                "Command": top["Command"],
                "Current Price": top["Current Price"],
                "Gross Sell": top["Gross Sell"],
                "BTC Captured": top["BTC Captured"],
                "BTC Price": btc_price,
            })
            st.session_state.btc_total += float(top["BTC Captured"])
            st.success(
                f"Executed {top['Coin']}: sold ${top['Gross Sell']:,.2f}, "
                f"captured {top['BTC Captured']:.8f} BTC. "
                f"Total captured: {st.session_state.btc_total:.8f} BTC."
            )

        st.metric("Session BTC Captured", f"{st.session_state.btc_total:.8f}")

        st.subheader("Command Queue")
        st.dataframe(
            results[["Coin", "Amount", "Current Price", "24h Change %", "Trigger Price", "Progress to Trigger", "Sell %", "Alert", "Command", "Gross Sell", "BTC Captured"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Current Price": st.column_config.NumberColumn(format="$%.6f"),
                "24h Change %": st.column_config.NumberColumn(format="%.2f%%"),
                "Trigger Price": st.column_config.NumberColumn(format="$%.6f"),
                "Progress to Trigger": st.column_config.ProgressColumn("Progress", min_value=0, max_value=1, format="%d%%"),
                "Sell %": st.column_config.NumberColumn(format="%.0%"),
                "Gross Sell": st.column_config.NumberColumn(format="$%.2f"),
                "BTC Captured": st.column_config.NumberColumn(format="%.8f BTC"),
            }
        )

with tabs[2]:
    st.header("Step 3: Review Executions")
    log = pd.DataFrame(st.session_state.executions)
    if log.empty:
        st.info("No executions logged yet.")
    else:
        st.metric("Total BTC Captured", f"{log['BTC Captured'].sum():.8f}")
        st.dataframe(log, use_container_width=True, hide_index=True)
        st.download_button("Download Execution Log", log.to_csv(index=False).encode(), "satscommander_execution_log.csv", "text/csv")

with tabs[3]:
    st.header("Supported Live Price Symbols")
    st.write("Use these coin tickers for live prices. Unsupported coins can still be used in Manual Prices mode.")
    st.dataframe(pd.DataFrame([{"Coin": k, "CoinGecko ID": v} for k, v in COINGECKO_IDS.items()]), use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("SatsCommander Live — prices from CoinGecko simple/price. Private Session Mode is session-only and not stored in GitHub.")
