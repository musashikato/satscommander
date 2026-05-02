import json
from datetime import datetime
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen

import pandas as pd
import streamlit as st

st.set_page_config(page_title="SatsCommander SaaS UI", layout="wide")

# ---------------- THEME ----------------
st.markdown("""
<style>
.stApp { background: #050A12; color: #E5E7EB; }
.block-container { max-width: 1500px; padding-top: 1rem; }
h1,h2,h3 { color: white; }
[data-testid="stMetric"] {
    background: linear-gradient(180deg,#111827,#0a0f1c);
    border: 1px solid #1e3a5f;
    border-radius: 16px;
    padding: 16px;
}
[data-testid="stMetricLabel"] { color: #00d1ff !important; font-weight: 800; }
[data-testid="stMetricValue"] { color: white !important; font-weight: 900; }
.brand {
    background: linear-gradient(90deg,#111827,#0a0f1c);
    border: 1px solid #00d1ff;
    border-radius: 18px;
    padding: 24px;
    margin-bottom: 18px;
}
.brand-title { font-size: 36px; font-weight: 950; color: white; margin: 0; }
.brand-sub { color: #f7931a; font-size: 18px; font-weight: 900; margin: 0; }
.brand-note { color: #9aa4b2; margin-top: 6px; }
.command-box {
    border-radius: 18px;
    padding: 28px;
    border: 2px solid rgba(255,255,255,.16);
    margin-bottom: 18px;
}
.command-title { font-size: 34px; font-weight: 950; line-height: 1.1; }
.command-sub { font-size: 16px; margin-top: 10px; opacity: .95; }
.card {
    background: linear-gradient(180deg,#111827,#0b1220);
    border: 1px solid #1e3a5f;
    border-radius: 16px;
    padding: 16px;
    margin-bottom: 12px;
}
.coin { font-size: 24px; font-weight: 950; color: white; }
.badge { padding: 5px 9px; border-radius: 8px; font-weight: 900; font-size: 12px; }
.red { background:#ff3b3b;color:white; }
.orange { background:#fb923c;color:black; }
.yellow { background:#facc15;color:black; }
.green { background:#00ff9c;color:black; }
.purple { background:#9b5cff;color:white; }
.cyan { background:#00d1ff;color:black; }
.dark { background:#101827;color:#94a3b8; }
.small { color:#9aa4b2; font-size: 13px; }
.btc { color:#f7931a; font-weight: 950; font-size: 18px; }
.saas-card {
    background: linear-gradient(180deg,#101827,#08101d);
    border: 1px solid #1e3a5f;
    border-radius: 16px;
    padding: 18px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- DATA ----------------
COINGECKO_IDS = {
    "BTC": "bitcoin", "ETH": "ethereum", "LINK": "chainlink", "SOL": "solana",
    "ADA": "cardano", "XRP": "ripple", "SUI": "sui", "RENDER": "render-token",
    "TAO": "bittensor", "AVAX": "avalanche-2", "DOT": "polkadot",
    "MATIC": "matic-network", "POL": "polygon-ecosystem-token", "GRT": "the-graph",
    "AIOZ": "aioz-network", "STX": "blockstack", "QNT": "quant-network",
    "CRO": "crypto-com-chain", "ENJ": "enjincoin", "CELO": "celo",
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
if "dismissed_alerts" not in st.session_state:
    st.session_state.dismissed_alerts = []
if "btc_total" not in st.session_state:
    st.session_state.btc_total = 0.0
if "missed_snapshots" not in st.session_state:
    st.session_state.missed_snapshots = []
if "alert_history" not in st.session_state:
    st.session_state.alert_history = []

# ---------------- SIDEBAR ----------------
st.sidebar.header("SatsCommander")
mode = st.sidebar.radio("Data Mode", ["Demo Portfolio", "Private Session Portfolio"])
price_mode = st.sidebar.radio("Price Mode", ["Live CoinGecko Prices", "Manual Prices"])
st.sidebar.caption("Private Session data is session-only and not stored in GitHub.")

st.sidebar.markdown("---")
st.sidebar.subheader("BTC Goal")
starting_btc = st.sidebar.number_input("Starting BTC Stack", value=0.0, min_value=0.0, format="%.8f")
btc_goal = st.sidebar.number_input("BTC Goal", value=1.0, min_value=0.00000001, format="%.8f")

st.sidebar.markdown("---")
st.sidebar.subheader("Alerts")
enable_visual_alerts = st.sidebar.checkbox("Enable visual alerts", value=True)
alert_threshold = st.sidebar.selectbox("Alert sensitivity", ["SELL NOW only", "PREPARE + SELL NOW"], index=0)

st.sidebar.markdown("---")
st.sidebar.subheader("Restore Backup")
backup = st.sidebar.file_uploader("Upload backup JSON", type=["json"])
if backup:
    try:
        restored = json.load(backup)
        st.session_state.executions = restored.get("executions", [])
        st.session_state.dismissed_alerts = restored.get("dismissed_alerts", [])
        st.session_state.btc_total = float(restored.get("btc_total", 0.0))
        st.session_state.missed_snapshots = restored.get("missed_snapshots", [])
        st.session_state.alert_history = restored.get("alert_history", [])
        if restored.get("portfolio"):
            st.session_state.portfolio = pd.DataFrame(restored["portfolio"])
        st.sidebar.success("Backup restored.")
    except Exception as e:
        st.sidebar.error(f"Could not restore backup: {e}")

# ---------------- FUNCTIONS ----------------
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
    if "BTC" not in symbol_to_id:
        ids.append("bitcoin")
        symbol_to_id["BTC"] = "bitcoin"

    params = urlencode({
        "ids": ",".join(sorted(set(ids))),
        "vs_currencies": "usd",
        "include_24hr_change": "true",
    })
    url = f"https://api.coingecko.com/api/v3/simple/price?{params}"

    try:
        req = Request(url, headers={"User-Agent": "SatsCommander/1.0"})
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        prices, changes = {}, {}
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

def alert_key(row):
    return f"{row['Coin']}-{row['Alert']}-{float(row['Trigger Price']):.8f}"

def calculate(df, btc_price, live_prices=None, manual_prices=None, changes=None, executed_coins=None, dismissed_keys=None):
    df = normalize(df)
    live_prices = live_prices or {}
    manual_prices = manual_prices or {}
    changes = changes or {}
    executed_coins = executed_coins or set()
    dismissed_keys = dismissed_keys or set()
    rows = []

    for _, r in df.iterrows():
        coin = r["Coin"]
        amount = float(r["Amount"])
        trigger = float(r["Trigger Price"])
        sell_pct = float(r["Sell %"])
        price = float(live_prices.get(coin, manual_prices.get(coin, 0)) or 0)

        value = amount * price
        progress = price / trigger if trigger > 0 else 0
        gross_sell = 0.0
        btc = 0.0
        missed = 0.0
        confidence = 0

        if coin == "" or amount <= 0:
            alert = "INCOMPLETE"; command = "ADD POSITION DETAILS"; note = "Add coin and amount."
        elif price <= 0:
            alert = "NO PRICE"; command = f"ADD/VERIFY PRICE FOR {coin}"; note = "Use Manual Prices or supported ticker."; confidence = 5
        elif trigger <= 0:
            alert = "NO TRIGGER"; command = f"SET TRIGGER FOR {coin}"; note = "Add trigger price."; confidence = 10
        elif coin in executed_coins:
            alert = "EXECUTED"; command = f"{coin} ALREADY EXECUTED"; note = "Logged this session."
        elif price >= trigger:
            alert = "SELL NOW"
            gross_sell = value * sell_pct
            btc = gross_sell / btc_price if btc_price else 0
            missed = btc
            command = f"SELL {coin} NOW — {sell_pct:.0%}"
            note = f"Price is {progress:.0%} of trigger."
            confidence = 95
        elif progress >= 0.80:
            alert = "PREPARE"; command = f"{coin} IS ARMED — PREPARE"; note = f"Price is {progress:.0%} of trigger."; confidence = 70
        elif progress >= 0.60:
            alert = "WATCH"; command = f"TRACK {coin} — APPROACHING LEVEL"; note = f"Price is {progress:.0%} of trigger."; confidence = 40
        else:
            alert = "STANDBY"; command = "STANDBY — NO ACTION"; note = f"Price is {progress:.0%} of trigger." if trigger > 0 else "No action."; confidence = 10

        temp = {
            **r.to_dict(), "Current Price": price, "24h Change %": changes.get(coin),
            "Position Value": value, "Progress to Trigger": progress, "Alert": alert,
            "Command": command, "Status Note": note, "Confidence": confidence,
            "Gross Sell": gross_sell, "BTC Captured": btc, "Missed BTC": missed,
        }
        temp["Alert Key"] = alert_key(temp)
        temp["Dismissed"] = temp["Alert Key"] in dismissed_keys
        rows.append(temp)

    out = pd.DataFrame(rows)
    score_map = {"SELL NOW":100, "PREPARE":70, "WATCH":40, "STANDBY":10, "NO TRIGGER":5, "NO PRICE":3, "INCOMPLETE":0, "EXECUTED":-1}
    out["Priority"] = out["Alert"].map(score_map).fillna(0)
    return out.sort_values(["Priority", "BTC Captured"], ascending=[False, False])

def execute_row(row, btc_price):
    st.session_state.executions.append({
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Coin": row["Coin"], "Command": row["Command"],
        "Current Price": float(row["Current Price"]),
        "Gross Sell": float(row["Gross Sell"]),
        "BTC Captured": float(row["BTC Captured"]),
        "BTC Price": float(btc_price), "Confidence": int(row["Confidence"]),
        "Alert Key": row["Alert Key"],
    })
    st.session_state.btc_total += float(row["BTC Captured"])

def dismiss_row(row):
    st.session_state.dismissed_alerts.append({
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Coin": row["Coin"], "Command": row["Command"],
        "BTC Missed": float(row["Missed BTC"]), "Alert Key": row["Alert Key"],
        "Reason": "Dismissed / skipped",
    })

def discipline_score(executions, dismissed_alerts, active_sells_count):
    executed_count = len(executions)
    dismissed_count = len(dismissed_alerts)
    denominator = executed_count + dismissed_count
    if denominator == 0:
        return 50 if active_sells_count > 0 else 100
    return round((executed_count / denominator) * 100)

def badge_class(alert):
    if alert == "SELL NOW": return "red"
    if alert == "PREPARE": return "green"
    if alert == "WATCH": return "yellow"
    if alert == "EXECUTED": return "cyan"
    if alert in ["NO PRICE", "NO TRIGGER", "INCOMPLETE"]: return "purple"
    return "dark"

# ---------------- DATA LOAD ----------------
portfolio = DEMO.copy() if mode == "Demo Portfolio" else normalize(st.session_state.portfolio.copy())
executed_coins = {str(x.get("Coin", "")).upper() for x in st.session_state.executions}
dismissed_keys = {str(x.get("Alert Key", "")) for x in st.session_state.dismissed_alerts}
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

results = calculate(
    portfolio, btc_price,
    live_prices=live_prices, manual_prices=manual_prices, changes=changes,
    executed_coins=executed_coins, dismissed_keys=dismissed_keys
)

# ---------------- LAYOUT ----------------
st.markdown("""
<div class="brand">
  <div class="brand-title">SatsCommander</div>
  <p class="brand-sub">Turn Altcoins Into Bitcoin</p>
  <div class="brand-note">SaaS-style execution dashboard for disciplined alt → BTC rotation.</div>
</div>
""", unsafe_allow_html=True)

tabs = st.tabs(["Command Deck", "Portfolio", "Execution Log", "Performance", "Alerts", "SaaS Control"])

with tabs[0]:
    if results.empty or len(results[results["Coin"] != ""]) == 0:
        st.info("Load a portfolio first in the Portfolio tab.")
    else:
        total_value = results["Position Value"].sum()
        active_sells = results[(results["Alert"] == "SELL NOW") & (~results["Dismissed"])]
        active_prepares = results[(results["Alert"] == "PREPARE") & (~results["Dismissed"])]
        potential_btc = active_sells["BTC Captured"].sum()
        captured_total = float(st.session_state.btc_total)
        current_btc_stack = starting_btc + captured_total
        goal_progress = min(current_btc_stack / btc_goal, 1.0) if btc_goal else 0
        missed_total = max(0.0, potential_btc - captured_total)
        score = discipline_score(st.session_state.executions, st.session_state.dismissed_alerts, len(active_sells))

        st.session_state.missed_snapshots.append({
            "Timestamp": datetime.now().strftime("%H:%M:%S"),
            "Captured BTC": captured_total,
            "Missed BTC": missed_total,
            "Discipline Score": score,
        })
        st.session_state.missed_snapshots = st.session_state.missed_snapshots[-50:]

        alert_rows = active_sells.copy()
        if alert_threshold == "PREPARE + SELL NOW":
            alert_rows = pd.concat([alert_rows, active_prepares], ignore_index=True)

        new_alert_count = 0
        for _, row in alert_rows.iterrows():
            key = f"{row['Coin']}-{row['Alert']}-{row['Current Price']:.6f}"
            if key not in {x.get("Key") for x in st.session_state.alert_history}:
                new_alert_count += 1
                st.session_state.alert_history.append({
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Key": key, "Coin": row["Coin"], "Alert": row["Alert"],
                    "Command": row["Command"], "Current Price": row["Current Price"],
                    "Trigger Price": row["Trigger Price"], "BTC Captured": row["BTC Captured"],
                    "Confidence": row["Confidence"],
                })
        st.session_state.alert_history = st.session_state.alert_history[-100:]

        if enable_visual_alerts and new_alert_count > 0:
            st.toast(f"🔔 {new_alert_count} new alert(s)", icon="🚨")
            st.warning(f"🔔 NEW ALERT DETECTED: {new_alert_count} signal(s) entered your alert zone.")

        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("BTC Goal", f"{current_btc_stack:.8f} / {btc_goal:.2f}", f"{goal_progress:.1%} complete")
        k2.metric("Captured BTC", f"{captured_total:.8f}")
        k3.metric("Missed BTC", f"{missed_total:.8f}")
        k4.metric("Discipline", f"{score}%")
        k5.metric("Portfolio", f"${total_value:,.0f}")

        st.progress(goal_progress, text=f"BTC Goal Progress: {goal_progress:.1%}")
        st.progress(score / 100, text=f"Discipline Score: {score}%")

        visible_results = results[~results["Dismissed"]]
        top = visible_results.iloc[0] if not visible_results.empty else results.iloc[0]

        left, right = st.columns([1.05, 2.0], gap="large")

        with left:
            st.subheader("Command Queue")
            for _, r in visible_results.head(5).iterrows():
                st.markdown(f"""
                <div class="card">
                  <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div class="coin">{r['Coin']}</div>
                    <span class="badge {badge_class(r['Alert'])}">{r['Alert']}</span>
                  </div>
                  <div style="font-weight:900;margin-top:8px;color:white;">{r['Command']}</div>
                  <div class="small">Price ${r['Current Price']:,.4f} · Trigger ${r['Trigger Price']:,.4f} · Confidence {r['Confidence']}%</div>
                  <div class="btc">+{r['BTC Captured']:.8f} BTC</div>
                </div>
                """, unsafe_allow_html=True)

        with right:
            st.subheader("DO THIS NOW")
            if top["Alert"] == "SELL NOW":
                bg = "#ff3b3b"; color = "white"
                title = top["Command"]
                sub = f"Convert ${top['Gross Sell']:,.2f} → {top['BTC Captured']:.8f} BTC · Confidence {top['Confidence']}%"
            elif top["Alert"] == "PREPARE":
                bg = "#00ff9c"; color = "black"
                title = top["Command"]
                sub = f"Price is {top['Progress to Trigger']:.0%} of trigger · Confidence {top['Confidence']}%"
            elif top["Alert"] == "WATCH":
                bg = "#facc15"; color = "black"
                title = top["Command"]
                sub = f"Price is {top['Progress to Trigger']:.0%} of trigger · Confidence {top['Confidence']}%"
            else:
                bg = "#020617"; color = "#94a3b8"
                title = "STANDBY — NO ACTION"
                sub = "No urgent command. Do not force a trade."

            st.markdown(f"""
            <div class="command-box" style="background:{bg}; color:{color};">
              <div class="command-title">{title}</div>
              <div class="command-sub">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

            if top["Alert"] == "SELL NOW":
                email_body = quote(f"SatsCommander Alert: {top['Command']}\n\nPrice: ${top['Current Price']:,.4f}\nTrigger: ${top['Trigger Price']:,.4f}\nEstimated BTC Captured: {top['BTC Captured']:.8f}")
                st.markdown(f"[Create Email Alert](mailto:?subject=SatsCommander SELL Alert - {top['Coin']}&body={email_body})")

            executable = results[(results["Alert"] == "SELL NOW") & (~results["Dismissed"])].copy()
            if executable.empty:
                st.info("No SELL NOW rows available.")
            else:
                labels = executable.apply(lambda r: f"{r['Coin']} — {r['Command']} — {r['BTC Captured']:.8f} BTC", axis=1).tolist()
                selected = st.selectbox("Choose row", labels)
                selected_row = executable.iloc[labels.index(selected)]
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("EXECUTE SELECTED ROW", type="primary"):
                        execute_row(selected_row, btc_price)
                        st.success(f"Executed {selected_row['Coin']}: captured {selected_row['BTC Captured']:.8f} BTC.")
                        st.rerun()
                with b2:
                    if st.button("DISMISS / SKIP SIGNAL"):
                        dismiss_row(selected_row)
                        st.warning(f"Dismissed {selected_row['Coin']} signal.")
                        st.rerun()

        st.subheader("Execution Grid")
        st.dataframe(
            results[["Coin", "Amount", "Current Price", "24h Change %", "Trigger Price", "Progress to Trigger", "Sell %", "Alert", "Dismissed", "Command", "Confidence", "Gross Sell", "BTC Captured", "Missed BTC", "Status Note"]],
            use_container_width=True, hide_index=True,
            column_config={
                "Current Price": st.column_config.NumberColumn(format="$%.6f"),
                "24h Change %": st.column_config.NumberColumn(format="%.2f%%"),
                "Trigger Price": st.column_config.NumberColumn(format="$%.6f"),
                "Progress to Trigger": st.column_config.ProgressColumn("Progress", min_value=0, max_value=1, format="%d%%"),
                "Sell %": st.column_config.NumberColumn(format="%.0%"),
                "Confidence": st.column_config.ProgressColumn("Confidence", min_value=0, max_value=100, format="%d%%"),
                "Gross Sell": st.column_config.NumberColumn(format="$%.2f"),
                "BTC Captured": st.column_config.NumberColumn(format="%.8f BTC"),
                "Missed BTC": st.column_config.NumberColumn(format="%.8f BTC"),
            }
        )

with tabs[1]:
    st.header("Portfolio")
    if mode == "Demo Portfolio":
        st.success("Demo Portfolio active — safe sample data.")
        st.dataframe(DEMO, use_container_width=True, hide_index=True)
    else:
        st.warning("Private Session Portfolio active — data is session-only and not saved to GitHub.")
        uploaded = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded:
            st.session_state.portfolio = normalize(pd.read_csv(uploaded))
        st.session_state.portfolio = st.data_editor(st.session_state.portfolio, num_rows="dynamic", use_container_width=True, key="portfolio_editor")

    st.download_button(
        "Download CSV Template",
        pd.DataFrame(columns=["Coin", "Amount", "Trigger Price", "Sell %"]).to_csv(index=False).encode(),
        "satscommander_template.csv", "text/csv"
    )

with tabs[2]:
    st.header("Execution Log")
    log = pd.DataFrame(st.session_state.executions)
    dismissed = pd.DataFrame(st.session_state.dismissed_alerts)
    c1, c2, c3 = st.columns(3)
    c1.metric("Executed Signals", len(log))
    c2.metric("Dismissed Signals", len(dismissed))
    c3.metric("Discipline Score", f"{discipline_score(st.session_state.executions, st.session_state.dismissed_alerts, 0)}%")

    if not log.empty:
        st.dataframe(log, use_container_width=True, hide_index=True)
        st.download_button("Download Execution Log", log.to_csv(index=False).encode(), "satscommander_execution_log.csv", "text/csv")
    else:
        st.info("No executions logged yet.")

    st.subheader("Dismissed / Skipped Signals")
    if not dismissed.empty:
        st.dataframe(dismissed, use_container_width=True, hide_index=True)
    else:
        st.info("No dismissed signals yet.")

    if st.button("Clear Execution + Dismissal Logs"):
        st.session_state.executions = []
        st.session_state.dismissed_alerts = []
        st.session_state.btc_total = 0.0
        st.rerun()

with tabs[3]:
    st.header("Performance")
    chart_df = pd.DataFrame(st.session_state.missed_snapshots)
    if not chart_df.empty:
        st.line_chart(chart_df.set_index("Timestamp")[["Captured BTC", "Missed BTC"]])
        if "Discipline Score" in chart_df.columns:
            st.line_chart(chart_df.set_index("Timestamp")[["Discipline Score"]])
    else:
        st.info("No performance data yet. Visit Command Deck first.")

    current_btc_stack = starting_btc + float(st.session_state.btc_total)
    goal_progress = min(current_btc_stack / btc_goal, 1.0) if btc_goal else 0
    st.metric("BTC Remaining to Goal", f"{max(btc_goal - current_btc_stack, 0):.8f}")
    st.progress(goal_progress, text=f"{goal_progress:.1%} complete")

    backup_payload = {
        "portfolio": st.session_state.portfolio.to_dict(orient="records"),
        "executions": st.session_state.executions,
        "dismissed_alerts": st.session_state.dismissed_alerts,
        "btc_total": st.session_state.btc_total,
        "missed_snapshots": st.session_state.missed_snapshots,
        "alert_history": st.session_state.alert_history,
    }
    st.download_button("Download Private Backup JSON", json.dumps(backup_payload, indent=2).encode(), "satscommander_private_backup.json", "application/json")

with tabs[4]:
    st.header("Alerts")
    alert_df = pd.DataFrame(st.session_state.alert_history)
    if not alert_df.empty:
        st.dataframe(alert_df.drop(columns=["Key"], errors="ignore"), use_container_width=True, hide_index=True)
        st.download_button("Download Alert History", alert_df.to_csv(index=False).encode(), "satscommander_alert_history.csv", "text/csv")
    else:
        st.info("No alerts recorded this session.")
    st.caption("True automatic background alerts require accounts/backend. This version alerts while app is open.")

with tabs[5]:
    st.header("SaaS Control Panel")
    st.markdown("### Future SaaS modules")
    a, b, c = st.columns(3)
    with a:
        st.markdown('<div class="saas-card"><h3>🔐 Private Portfolios</h3><p class="small">Saved per user with secure login.</p></div>', unsafe_allow_html=True)
    with b:
        st.markdown('<div class="saas-card"><h3>🔔 Real Alerts</h3><p class="small">Email, SMS, and push notifications.</p></div>', unsafe_allow_html=True)
    with c:
        st.markdown('<div class="saas-card"><h3>💳 Stripe Billing</h3><p class="small">Free, Pro, and Elite subscriptions.</p></div>', unsafe_allow_html=True)

    st.markdown("### Supported Live Price Symbols")
    st.dataframe(pd.DataFrame([{"Coin": k, "CoinGecko ID": v} for k, v in COINGECKO_IDS.items()]), use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("SatsCommander SaaS UI — live prices via CoinGecko. Private Session Mode is session-only and not stored in GitHub.")
