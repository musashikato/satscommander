import streamlit as st
import pandas as pd

st.set_page_config(page_title="Sats Engine", layout="wide")

st.title("Sats Engine — Execution Mode")

st.markdown("## DO THIS NOW")

# Simple demo logic
coin = st.selectbox("Coin", ["LINK", "SOL", "ETH"])
price = st.number_input("Current Price", value=10.0)

if coin == "LINK" and price > 20:
    st.error("🚨 SELL LINK NOW — 25%")
elif coin == "SOL" and price > 150:
    st.warning("⚠️ REDUCE SOL — 25%")
else:
    st.success("STANDBY — NO ACTION")

st.markdown("---")

st.markdown("## Execution Log")

if "log" not in st.session_state:
    st.session_state.log = []

if st.button("Execute Command"):
    st.session_state.log.append({"coin": coin, "price": price})

st.write(pd.DataFrame(st.session_state.log))
