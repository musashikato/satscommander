import streamlit as st
import pandas as pd

st.set_page_config(page_title="SatsCommander", layout="wide")

st.markdown("""
<div style="background:linear-gradient(90deg,#111827,#0a0f1c);
padding:22px;border-radius:14px;border:1px solid #00d1ff;margin-bottom:20px;">
<h1 style="color:white;margin:0;">SatsCommander</h1>
<p style="color:#f7931a;margin:0;font-weight:700;">Execution Engine for Stacking Sats</p>
<p style="color:#9aa4b2;margin-top:6px;">Turn altcoins into Bitcoin with disciplined execution.</p>
</div>
""", unsafe_allow_html=True)

DEMO_DATA = pd.DataFrame([
    {"Coin": "LINK", "Amount": 150, "Current Price": 18.50, "Trigger Price": 20.00, "Sell %": 0.25},
    {"Coin": "SOL", "Amount": 12, "Current Price": 142.00, "Trigger Price": 150.00, "Sell %": 0.25},
    {"Coin": "ETH", "Amount": 2.0, "Current Price": 3200.00, "Trigger Price": 3500.00, "Sell %": 0.15},
])

st.sidebar.header("Privacy Mode")
mode = st.sidebar.radio(
    "Choose data mode",
    ["Demo Mode", "Private Session Mode"],
    help="Demo Mode uses fake sample data. Private Session Mode keeps your data only in this browser session."
)

st.sidebar.info(
    "Privacy note: Private Session Mode does not save your portfolio to GitHub or show it to other users. "
    "It only exists while your app session is open."
)

btc_price = st.sidebar.number_input("BTC price", value=78000.00, min_value=0.0, step=100.0)

if "private_data" not in st.session_state:
    st.session_state.private_data = pd.DataFrame(columns=["Coin", "Amount", "Current Price", "Trigger Price", "Sell %"])

if mode == "Demo Mode":
    portfolio = DEMO_DATA.copy()
    st.success("Demo Mode active — using fake sample data. Safe to share publicly.")
else:
    st.warning("Private Session Mode active — your data stays in this browser session only.")

    uploaded = st.file_uploader("Optional: upload private portfolio CSV", type=["csv"])
    if uploaded is not None:
        st.session_state.private_data = pd.read_csv(uploaded)

    st.caption("Required columns: Coin, Amount, Current Price, Trigger Price, Sell %")
    st.session_state.private_data = st.data_editor(
        st.session_state.private_data,
        num_rows="dynamic",
        use_container_width=True,
        key="private_editor"
    )
    portfolio = st.session_state.private_data.copy()

def calculate_signals(df: pd.DataFrame, btc_price: float) -> pd.DataFrame:
    if df.empty:
        return df

    required = ["Coin", "Amount", "Current Price", "Trigger Price", "Sell %"]
    for col in required:
        if col not in df.columns:
            df[col] = 0 if col != "Coin" else ""

    for col in ["Amount", "Current Price", "Trigger Price", "Sell %"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    alerts = []
    commands = []
    gross_sells = []
    btc_gains = []

    for _, r in df.iterrows():
        coin = str(r["Coin"]).upper()
        price = float(r["Current Price"])
        trigger = float(r["Trigger Price"])
        sell_pct = float(r["Sell %"])
        value = float(r["Amount"]) * price
        gross_sell = value * sell_pct

        if trigger > 0 and price >= trigger:
            alert = "SELL NOW"
            command = f"SELL {coin} NOW — {sell_pct:.0%}"
        elif trigger > 0 and price >= trigger * 0.8:
            alert = "ARMED"
            command = f"{coin} IS ARMED — PREPARE"
            gross_sell = 0
        elif trigger > 0 and price >= trigger * 0.6:
            alert = "TRACKING"
            command = f"TRACK {coin} — APPROACHING LEVEL"
            gross_sell = 0
        else:
            alert = "STANDBY"
            command = "STANDBY — NO ACTION"
            gross_sell = 0

        btc_gain = gross_sell / btc_price if btc_price else 0

        alerts.append(alert)
        commands.append(command)
        gross_sells.append(gross_sell)
        btc_gains.append(btc_gain)

    df["Alert"] = alerts
    df["Command"] = commands
    df["Gross Sell"] = gross_sells
    df["BTC Captured"] = btc_gains
    return df

signals = calculate_signals(portfolio.copy(), btc_price)

st.subheader("DO THIS NOW")

if signals.empty:
    st.info("No portfolio data loaded.")
else:
    top = signals.sort_values("BTC Captured", ascending=False).iloc[0]
    command = top["Command"]

    if "SELL" in command:
        st.error(command)
    elif "ARMED" in command:
        st.success(command)
    elif "TRACK" in command:
        st.warning(command)
    else:
        st.success("STANDBY — NO ACTION")

st.subheader("Command Queue")
if signals.empty:
    st.write("No data yet.")
else:
    st.dataframe(
        signals[["Coin", "Amount", "Current Price", "Trigger Price", "Sell %", "Alert", "Command", "Gross Sell", "BTC Captured"]],
        use_container_width=True,
        hide_index=True
    )

st.subheader("Execution Log")

if "execution_log" not in st.session_state:
    st.session_state.execution_log = []

if not signals.empty:
    selected_coin = st.selectbox("Select command to execute", signals["Coin"].astype(str).tolist())
    selected_row = signals[signals["Coin"].astype(str) == selected_coin].iloc[0]

    if st.button("EXECUTE COMMAND", type="primary"):
        st.session_state.execution_log.append({
            "Coin": selected_row["Coin"],
            "Command": selected_row["Command"],
            "Gross Sell": selected_row["Gross Sell"],
            "BTC Captured": selected_row["BTC Captured"],
        })
        st.success(f"Execution logged for {selected_row['Coin']}.")

st.dataframe(pd.DataFrame(st.session_state.execution_log), use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("SatsCommander privacy model: Demo data is public. Private Session Mode is not saved to GitHub or shared with other users.")
