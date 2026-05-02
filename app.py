import streamlit as st
import pandas as pd

st.set_page_config(page_title="SatsCommander MVP v2", layout="wide")

st.markdown("""
<div style="background:linear-gradient(90deg,#111827,#0a0f1c);
padding:24px;border-radius:16px;border:1px solid #00d1ff;margin-bottom:20px;">
<h1 style="color:white;margin:0;">SatsCommander</h1>
<p style="color:#f7931a;margin:0;font-weight:700;font-size:18px;">Turn Altcoins Into Bitcoin</p>
<p style="color:#9aa4b2;margin-top:6px;">A guided execution engine that tells you when to sell, prepare, or stand down.</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.header("SatsCommander Setup")
btc_price = st.sidebar.number_input("BTC Price", value=78000.00, min_value=0.0, step=100.0)

mode = st.sidebar.radio(
    "Data Mode",
    ["Demo Portfolio", "Private Session Portfolio"],
    help="Demo is safe public data. Private Session data only exists in your browser session."
)

st.sidebar.markdown("---")
st.sidebar.caption("Privacy: do not hardcode personal portfolio data into GitHub. Use Private Session Mode for real data.")

DEMO = pd.DataFrame([
    {"Coin": "LINK", "Amount": 150.0, "Current Price": 18.50, "Trigger Price": 20.00, "Sell %": 0.25},
    {"Coin": "SOL", "Amount": 12.0, "Current Price": 142.00, "Trigger Price": 150.00, "Sell %": 0.25},
    {"Coin": "ETH", "Amount": 2.0, "Current Price": 3200.00, "Trigger Price": 3500.00, "Sell %": 0.15},
])

if "portfolio" not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(columns=["Coin", "Amount", "Current Price", "Trigger Price", "Sell %"])

if "executions" not in st.session_state:
    st.session_state.executions = []

def normalize(df):
    required = ["Coin", "Amount", "Current Price", "Trigger Price", "Sell %"]
    for col in required:
        if col not in df.columns:
            df[col] = "" if col == "Coin" else 0
    df = df[required].copy()
    for col in ["Amount", "Current Price", "Trigger Price", "Sell %"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["Coin"] = df["Coin"].astype(str).str.upper().str.strip()
    return df

def calculate(df, btc_price):
    df = normalize(df)
    alerts, commands, gross_sells, btc_captured, distance = [], [], [], [], []

    for _, r in df.iterrows():
        coin = r["Coin"]
        amount = float(r["Amount"])
        price = float(r["Current Price"])
        trigger = float(r["Trigger Price"])
        sell_pct = float(r["Sell %"])
        value = amount * price
        progress = price / trigger if trigger > 0 else 0
        gross_sell = 0

        if coin == "" or amount <= 0:
            alert = "INCOMPLETE"
            command = "ADD POSITION DETAILS"
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
        alerts.append(alert)
        commands.append(command)
        gross_sells.append(gross_sell)
        btc_captured.append(btc)
        distance.append(progress)

    df["Position Value"] = df["Amount"] * df["Current Price"]
    df["Progress to Trigger"] = distance
    df["Alert"] = alerts
    df["Command"] = commands
    df["Gross Sell"] = gross_sells
    df["BTC Captured"] = btc_captured

    score_map = {"SELL NOW": 100, "PREPARE": 70, "WATCH": 40, "STANDBY": 10, "NO TRIGGER": 5, "INCOMPLETE": 0}
    df["Priority"] = df["Alert"].map(score_map).fillna(0)
    return df.sort_values(["Priority", "BTC Captured"], ascending=[False, False])

def command_panel(top):
    alert = top["Alert"]
    command = top["Command"]
    btc = top["BTC Captured"]

    if alert == "SELL NOW":
        st.error(f"{command}  |  Est. BTC Captured: {btc:.8f}")
    elif alert == "PREPARE":
        st.success(f"{command}  |  No sale yet. Get ready.")
    elif alert == "WATCH":
        st.warning(f"{command}  |  Monitor closely.")
    elif alert == "STANDBY":
        st.info("STANDBY — NO ACTION. Do not force a trade.")
    else:
        st.info(command)

tabs = st.tabs(["1. Command Center", "2. Portfolio Input", "3. Execution Log"])

with tabs[1]:
    st.header("Step 1: Load Your Portfolio")

    if mode == "Demo Portfolio":
        st.success("Demo Portfolio active. This is fake sample data and safe to share.")
        active_portfolio = DEMO.copy()
        st.dataframe(active_portfolio, use_container_width=True, hide_index=True)
    else:
        st.warning("Private Session Portfolio active. Your data is not saved to GitHub and only exists during this session.")

        uploaded = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded:
            st.session_state.portfolio = normalize(pd.read_csv(uploaded))

        st.caption("Required columns: Coin, Amount, Current Price, Trigger Price, Sell %")
        st.session_state.portfolio = st.data_editor(
            st.session_state.portfolio,
            num_rows="dynamic",
            use_container_width=True,
            key="portfolio_editor"
        )
        active_portfolio = st.session_state.portfolio.copy()

    st.markdown("### CSV Template")
    template = pd.DataFrame(columns=["Coin", "Amount", "Current Price", "Trigger Price", "Sell %"])
    st.download_button("Download CSV Template", template.to_csv(index=False).encode(), "satscommander_template.csv", "text/csv")

with tabs[0]:
    st.header("Step 2: Follow the Command")

    active_portfolio = DEMO.copy() if mode == "Demo Portfolio" else st.session_state.portfolio.copy()
    results = calculate(active_portfolio, btc_price)

    if results.empty or len(results[results["Coin"] != ""]) == 0:
        st.info("Load a portfolio first in the Portfolio Input tab.")
    else:
        total_value = results["Position Value"].sum()
        active_sells = results[results["Alert"] == "SELL NOW"]
        potential_btc = active_sells["BTC Captured"].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("Portfolio Value", f"${total_value:,.2f}")
        c2.metric("Active Sell Signals", len(active_sells))
        c3.metric("Potential BTC Captured", f"{potential_btc:.8f}")

        st.markdown("---")
        top = results.iloc[0]
        st.subheader("DO THIS NOW")
        command_panel(top)

        if st.button("EXECUTE TOP COMMAND", type="primary", disabled=(top["Alert"] != "SELL NOW")):
            st.session_state.executions.append({
                "Coin": top["Coin"],
                "Command": top["Command"],
                "Gross Sell": top["Gross Sell"],
                "BTC Captured": top["BTC Captured"],
                "BTC Price": btc_price
            })
            st.success(f"Execution logged for {top['Coin']}.")

        st.subheader("Command Queue")
        display = results[["Coin", "Amount", "Current Price", "Trigger Price", "Progress to Trigger", "Sell %", "Alert", "Command", "Gross Sell", "BTC Captured"]]
        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Progress to Trigger": st.column_config.ProgressColumn("Progress", min_value=0, max_value=1, format="%d%%"),
                "Sell %": st.column_config.NumberColumn(format="%.0%"),
                "Current Price": st.column_config.NumberColumn(format="$%.6f"),
                "Trigger Price": st.column_config.NumberColumn(format="$%.6f"),
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
        total_btc = log["BTC Captured"].sum()
        total_gross = log["Gross Sell"].sum()

        c1, c2 = st.columns(2)
        c1.metric("Total Gross Executed", f"${total_gross:,.2f}")
        c2.metric("Total BTC Captured", f"{total_btc:.8f}")

        st.dataframe(log, use_container_width=True, hide_index=True)
        st.download_button("Download Execution Log", log.to_csv(index=False).encode(), "satscommander_execution_log.csv", "text/csv")

        if st.button("Clear Execution Log"):
            st.session_state.executions = []
            st.rerun()

st.markdown("---")
st.caption("SatsCommander MVP v2 — Demo data is public. Private Session Mode is session-only and not stored in GitHub.")
