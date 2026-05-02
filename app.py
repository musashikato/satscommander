import streamlit as st
import pandas as pd

st.set_page_config(page_title="SatsCommander v3", layout="wide")

st.markdown("""
<div style="background:linear-gradient(90deg,#111827,#0a0f1c);
padding:24px;border-radius:16px;border:1px solid #00d1ff;margin-bottom:20px;">
<h1 style="color:white;margin:0;">SatsCommander</h1>
<p style="color:#f7931a;margin:0;font-weight:700;font-size:18px;">Turn Altcoins Into Bitcoin</p>
</div>
""", unsafe_allow_html=True)

if "portfolio" not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(columns=["Coin","Amount","Current Price","Trigger Price","Sell %"])

if "executions" not in st.session_state:
    st.session_state.executions = []

if "btc_total" not in st.session_state:
    st.session_state.btc_total = 0.0

btc_price = st.sidebar.number_input("BTC Price", value=78000.0)

mode = st.sidebar.radio("Mode", ["Demo","Private"])

DEMO = pd.DataFrame([
    {"Coin":"LINK","Amount":150,"Current Price":18.5,"Trigger Price":20,"Sell %":0.25},
    {"Coin":"SOL","Amount":12,"Current Price":142,"Trigger Price":150,"Sell %":0.25},
    {"Coin":"ETH","Amount":2,"Current Price":3200,"Trigger Price":3500,"Sell %":0.15},
])

def calc(df):
    df = df.copy()
    df["Value"] = df["Amount"]*df["Current Price"]
    df["Progress"] = df["Current Price"]/df["Trigger Price"]
    alerts=[]
    btc=[]
    for _,r in df.iterrows():
        if r["Current Price"]>=r["Trigger Price"]:
            alerts.append("SELL")
            btc.append((r["Value"]*r["Sell %"])/btc_price)
        elif r["Progress"]>=0.8:
            alerts.append("PREPARE")
            btc.append(0)
        else:
            alerts.append("WAIT")
            btc.append(0)
    df["Alert"]=alerts
    df["BTC"]=btc
    return df

tabs = st.tabs(["Command","Portfolio","Log"])

with tabs[1]:
    if mode=="Demo":
        st.dataframe(DEMO)
        active=DEMO
    else:
        st.session_state.portfolio = st.data_editor(st.session_state.portfolio, num_rows="dynamic")
        active=st.session_state.portfolio

with tabs[0]:
    df = calc(active)
    if not df.empty:
        top = df.sort_values("BTC", ascending=False).iloc[0]

        if top["Alert"]=="SELL":
            st.error(f"🚨 SELL {top['Coin']} NOW")
        elif top["Alert"]=="PREPARE":
            st.success(f"🟢 PREPARE {top['Coin']}")
        else:
            st.info("WAIT")

        st.metric("Total BTC Captured", f"{st.session_state.btc_total:.6f}")

        if st.button("EXECUTE") and top["Alert"]=="SELL":
            gained = top["BTC"]
            st.session_state.btc_total += gained
            st.session_state.executions.append({
                "Coin":top["Coin"],
                "BTC":gained
            })
            st.success(f"Captured {gained:.6f} BTC")

with tabs[2]:
    log = pd.DataFrame(st.session_state.executions)
    st.dataframe(log)
