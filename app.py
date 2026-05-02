import json
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd
import streamlit as st

st.set_page_config(page_title="SatsCommander Terminal", layout="wide")

st.markdown("""
<style>
.stApp{background:#05080F;color:#E5E7EB}.block-container{max-width:1700px;padding-top:.65rem;padding-left:1.2rem;padding-right:1.2rem}
h1,h2,h3{color:#F8FAFC;margin-top:.4rem;margin-bottom:.5rem}
[data-testid="stMetric"]{background:#0B1220;border:1px solid #18304E;border-radius:10px;padding:10px 12px}
[data-testid="stMetricLabel"]{color:#00D1FF!important;font-size:.72rem!important;font-weight:800}
[data-testid="stMetricValue"]{color:#F8FAFC!important;font-size:1.45rem!important;font-weight:900}
section[data-testid="stSidebar"]{background:#070B13;border-right:1px solid #18304E}
.terminal-shell{border:1px solid #18304E;background:linear-gradient(180deg,#0B1220,#070B13);border-radius:14px;padding:14px 16px;margin-bottom:12px}
.topbar{display:flex;justify-content:space-between;align-items:center;gap:14px}
.brand-title{font-size:30px;line-height:1;font-weight:950;color:white}.brand-sub{color:#F7931A;font-weight:900;font-size:13px;margin-top:5px}
.status-pill{border-radius:999px;padding:5px 9px;font-size:12px;font-weight:900}.online{background:#052E1A;color:#22C55E;border:1px solid #14532D}
.panel{background:#07111F;border:1px solid #18304E;border-radius:12px;padding:12px;min-height:120px}
.panel-title{color:#CBD5E1;font-size:13px;font-weight:950;text-transform:uppercase;letter-spacing:.04em;margin-bottom:10px}
.queue-item{border:1px solid #18304E;background:#0B1220;border-radius:10px;padding:10px;margin-bottom:8px}
.queue-coin{font-size:20px;color:white;font-weight:950}.small{color:#94A3B8;font-size:12px}.btc{color:#F7931A;font-weight:950}
.badge{padding:4px 7px;border-radius:6px;font-weight:950;font-size:11px;display:inline-block}
.exit{background:#EF4444;color:white}.reduce{background:#FB923C;color:#0B0B0B}.trim{background:#FACC15;color:#0B0B0B}.armed{background:#22C55E;color:#0B0B0B}.watch{background:#334155;color:#CBD5E1;border:1px solid #475569}.standby{background:#0F172A;color:#64748B;border:1px solid #334155}.executed{background:#06B6D4;color:#001018}
.insight-big{font-size:42px;font-weight:950;color:white;line-height:1}.insight-label{color:#94A3B8;font-size:12px;margin-top:4px}
.footer-note{color:#64748B;font-size:11px;text-align:right}div[data-testid="stDataFrame"]{border:1px solid #18304E;border-radius:10px;overflow:hidden}
</style>
""", unsafe_allow_html=True)

COINGECKO_IDS={"BTC":"bitcoin","ETH":"ethereum","LINK":"chainlink","SOL":"solana","ADA":"cardano","XRP":"ripple","SUI":"sui","RENDER":"render-token","TAO":"bittensor","AVAX":"avalanche-2","DOT":"polkadot","MATIC":"matic-network","POL":"polygon-ecosystem-token","GRT":"the-graph","AIOZ":"aioz-network","STX":"blockstack","QNT":"quant-network","CRO":"crypto-com-chain","ENJ":"enjincoin","CELO":"celo"}
REQUIRED=["Coin","Amount","Level 1 Price","Level 1 Sell %","Level 2 Price","Level 2 Sell %","Level 3 Price","Level 3 Sell %"]
DEMO=pd.DataFrame([
{"Coin":"LINK","Amount":150.0,"Level 1 Price":20.00,"Level 1 Sell %":0.25,"Level 2 Price":30.00,"Level 2 Sell %":0.35,"Level 3 Price":45.00,"Level 3 Sell %":0.40},
{"Coin":"SOL","Amount":12.0,"Level 1 Price":150.00,"Level 1 Sell %":0.25,"Level 2 Price":220.00,"Level 2 Sell %":0.35,"Level 3 Price":300.00,"Level 3 Sell %":0.40},
{"Coin":"ETH","Amount":2.0,"Level 1 Price":3500.00,"Level 1 Sell %":0.15,"Level 2 Price":5000.00,"Level 2 Sell %":0.25,"Level 3 Price":6500.00,"Level 3 Sell %":0.25},
{"Coin":"ADA","Amount":5000.0,"Level 1 Price":0.50,"Level 1 Sell %":0.30,"Level 2 Price":0.80,"Level 2 Sell %":0.50,"Level 3 Price":1.20,"Level 3 Sell %":0.80},
{"Coin":"XRP","Amount":520.0,"Level 1 Price":2.50,"Level 1 Sell %":0.25,"Level 2 Price":3.50,"Level 2 Sell %":0.50,"Level 3 Price":5.00,"Level 3 Sell %":0.80}])

defaults={"portfolio":pd.DataFrame(columns=REQUIRED),"executions":[],"dismissed_alerts":[],"missed_snapshots":[],"btc_total":0.0}
for k,v in defaults.items():
    if k not in st.session_state: st.session_state[k]=v

st.sidebar.header("Operator Controls")
mode=st.sidebar.radio("Data Mode",["Demo Portfolio","Private Session Portfolio"])
price_mode=st.sidebar.radio("Price Mode",["Live CoinGecko Prices","Manual Prices"])
starting_btc=st.sidebar.number_input("Starting BTC Stack",value=0.0,min_value=0.0,format="%.8f")
btc_goal=st.sidebar.number_input("BTC Goal",value=1.0,min_value=0.00000001,format="%.8f")
enable_visual_alerts=st.sidebar.checkbox("Visual alerts",value=True)
backup=st.sidebar.file_uploader("Restore backup JSON",type=["json"])
if backup:
    try:
        restored=json.load(backup)
        for key in ["executions","dismissed_alerts","missed_snapshots"]:
            st.session_state[key]=restored.get(key,[])
        st.session_state.btc_total=float(restored.get("btc_total",0.0))
        if restored.get("portfolio"): st.session_state.portfolio=pd.DataFrame(restored["portfolio"])
        st.sidebar.success("Backup restored.")
    except Exception as e: st.sidebar.error(f"Restore failed: {e}")

@st.cache_data(ttl=60)
def fetch_prices(symbols):
    ids=[]; symbol_to_id={}
    for sym in symbols:
        sym=str(sym).upper().strip(); cg=COINGECKO_IDS.get(sym)
        if cg: ids.append(cg); symbol_to_id[sym]=cg
    ids.append("bitcoin"); symbol_to_id["BTC"]="bitcoin"
    params=urlencode({"ids":",".join(sorted(set(ids))),"vs_currencies":"usd","include_24hr_change":"true"})
    try:
        req=Request(f"https://api.coingecko.com/api/v3/simple/price?{params}",headers={"User-Agent":"SatsCommander/1.0"})
        with urlopen(req,timeout=10) as response: data=json.loads(response.read().decode("utf-8"))
        return {"prices":{s:data.get(i,{}).get("usd",0) for s,i in symbol_to_id.items()},"changes":{s:data.get(i,{}).get("usd_24h_change",None) for s,i in symbol_to_id.items()}},None
    except Exception as e: return {},str(e)

def normalize(df):
    for col in REQUIRED:
        if col not in df.columns: df[col]="" if col=="Coin" else 0
    df=df[REQUIRED].copy(); df["Coin"]=df["Coin"].astype(str).str.upper().str.strip()
    for col in REQUIRED:
        if col!="Coin": df[col]=pd.to_numeric(df[col],errors="coerce").fillna(0)
    return df

def choose_level(row,price):
    levels=[("Level 1",float(row["Level 1 Price"]),float(row["Level 1 Sell %"]),"TRIM ZONE",70),("Level 2",float(row["Level 2 Price"]),float(row["Level 2 Sell %"]),"REDUCE",85),("Level 3",float(row["Level 3 Price"]),float(row["Level 3 Sell %"]),"EXIT FLOW",100)]
    if levels[2][1]>0 and price>=levels[2][1]: return levels[2]
    if levels[1][1]>0 and price>=levels[1][1]: return levels[1]
    if levels[0][1]>0 and price>=levels[0][1]: return levels[0]
    nxt=next((x for x in levels if x[1]>price and x[1]>0),levels[0])
    progress=price/nxt[1] if nxt[1] else 0
    if progress>=.8: return (nxt[0],nxt[1],0.0,"ARMED",55)
    if progress>=.6: return (nxt[0],nxt[1],0.0,"WATCH",35)
    return (nxt[0],nxt[1],0.0,"STANDBY",10)

def badge_class(alert):
    return {"EXIT FLOW":"exit","REDUCE":"reduce","TRIM ZONE":"trim","ARMED":"armed","WATCH":"watch","EXECUTED":"executed"}.get(alert,"standby")

def calculate(df,btc_price,prices,changes,manual_prices,executed_keys,dismissed_keys):
    rows=[]
    for _,r in normalize(df).iterrows():
        coin=r["Coin"]; price=float(prices.get(coin,manual_prices.get(coin,0)) or 0); amount=float(r["Amount"]); value=amount*price
        if not coin or amount<=0: level,level_price,sell_pct,alert,conf="None",0,0,"INCOMPLETE",0
        elif price<=0: level,level_price,sell_pct,alert,conf="None",0,0,"NO PRICE",5
        else: level,level_price,sell_pct,alert,conf=choose_level(r,price)
        progress=min(price/level_price,1) if level_price else 0
        gross=value*sell_pct if alert in ["TRIM ZONE","REDUCE","EXIT FLOW"] else 0
        btc_gain=gross/btc_price if btc_price else 0
        command={"EXIT FLOW":f"EXIT {coin} — SELL {sell_pct:.0%}","REDUCE":f"REDUCE {coin} — SELL {sell_pct:.0%}","TRIM ZONE":f"TRIM {coin} — SELL {sell_pct:.0%}","ARMED":f"{coin} ARMED — PREPARE","WATCH":f"TRACK {coin}","STANDBY":"STANDBY — NO ACTION","NO PRICE":f"ADD PRICE FOR {coin}","INCOMPLETE":"ADD POSITION DETAILS"}.get(alert,"STANDBY")
        key=f"{coin}-{alert}-{level_price:.8f}"; executed=key in executed_keys
        if executed: alert,command,conf,gross,btc_gain="EXECUTED",f"{coin} LEVEL EXECUTED",0,0,0
        rows.append({**r.to_dict(),"Current Price":price,"24h %":changes.get(coin),"Value":value,"Next Level":level,"Next Level Price":level_price,"Progress":progress,"Alert":alert,"Command":command,"Sell Action":sell_pct,"Confidence":conf,"Gross Sell":gross,"BTC Gain":btc_gain,"Missed BTC":btc_gain if alert in ["TRIM ZONE","REDUCE","EXIT FLOW"] else 0,"Alert Key":key,"Executed":executed,"Dismissed":key in dismissed_keys})
    out=pd.DataFrame(rows); score={"EXIT FLOW":100,"REDUCE":85,"TRIM ZONE":70,"ARMED":55,"WATCH":35,"STANDBY":10,"NO PRICE":5,"INCOMPLETE":0,"EXECUTED":-1}
    out["Priority"]=out["Alert"].map(score).fillna(0)
    return out.sort_values(["Priority","BTC Gain"],ascending=[False,False])

def execute_row(row,btc_price):
    st.session_state.executions.append({"Timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"Coin":row["Coin"],"Command":row["Command"],"Level":row["Next Level"],"Current Price":float(row["Current Price"]),"Gross Sell":float(row["Gross Sell"]),"BTC Captured":float(row["BTC Gain"]),"BTC Price":float(btc_price),"Confidence":int(row["Confidence"]),"Alert Key":row["Alert Key"]})
    st.session_state.btc_total+=float(row["BTC Gain"])

def dismiss_row(row):
    st.session_state.dismissed_alerts.append({"Timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"Coin":row["Coin"],"Command":row["Command"],"BTC Missed":float(row["Missed BTC"]),"Alert Key":row["Alert Key"]})

def discipline_score():
    e,d=len(st.session_state.executions),len(st.session_state.dismissed_alerts)
    return 100 if e+d==0 else round(e/(e+d)*100)

portfolio=DEMO.copy() if mode=="Demo Portfolio" else normalize(st.session_state.portfolio.copy())
symbols=portfolio["Coin"].dropna().astype(str).str.upper().tolist()
payload,err=fetch_prices(symbols) if price_mode=="Live CoinGecko Prices" else ({},None)
prices=payload.get("prices",{}) if isinstance(payload,dict) else {}; changes=payload.get("changes",{}) if isinstance(payload,dict) else {}
btc_price=prices.get("BTC") or st.sidebar.number_input("Manual BTC Price",value=78000.0,min_value=0.0)
manual_prices={}
if price_mode=="Manual Prices":
    for sym in symbols: manual_prices[sym]=st.sidebar.number_input(f"{sym}",value=0.0,min_value=0.0,key=f"manual_{sym}")
executed_keys={str(x.get("Alert Key","")) for x in st.session_state.executions}; dismissed_keys={str(x.get("Alert Key","")) for x in st.session_state.dismissed_alerts}
results=calculate(portfolio,btc_price,prices,changes,manual_prices,executed_keys,dismissed_keys)
active=results[(results["Alert"].isin(["TRIM ZONE","REDUCE","EXIT FLOW","ARMED"])) & (~results["Dismissed"]) & (~results["Executed"])]
if enable_visual_alerts and not active.empty: st.toast(f"{len(active)} active signal(s)",icon="⚡")

st.markdown("""<div class="terminal-shell topbar"><div><div class="brand-title">SatsCommander</div><div class="brand-sub">Terminal-style execution engine for stacking sats</div></div><div class="status-pill online">● MARKET DATA LIVE</div></div>""", unsafe_allow_html=True)

captured=float(st.session_state.btc_total); current_stack=starting_btc+captured; goal_progress=min(current_stack/btc_goal,1) if btc_goal else 0
queued_btc=results[results["Alert"].isin(["TRIM ZONE","REDUCE","EXIT FLOW"])]["BTC Gain"].sum(); missed_btc=max(queued_btc-captured,0); score=discipline_score(); total_value=results["Value"].sum()
m1,m2,m3,m4,m5=st.columns(5)
m1.metric("BTC HELD / GOAL",f"{current_stack:.8f}",f"{goal_progress:.1%}")
m2.metric("QUEUED BTC",f"{queued_btc:.8f}")
m3.metric("MISSED BTC",f"{missed_btc:.8f}")
m4.metric("DISCIPLINE",f"{score}%")
m5.metric("PORTFOLIO",f"${total_value:,.0f}")

left,center,right=st.columns([1.12,2.35,1.15],gap="medium")
with left:
    st.markdown('<div class="panel-title">Execution Queue</div>', unsafe_allow_html=True)
    queue=results[(results["Alert"].isin(["EXIT FLOW","REDUCE","TRIM ZONE","ARMED"])) & (~results["Dismissed"]) & (~results["Executed"])].head(5)
    if queue.empty: st.markdown('<div class="panel small">No active execution signals.</div>', unsafe_allow_html=True)
    for _,r in queue.iterrows():
        st.markdown(f"""<div class="queue-item"><div style="display:flex;justify-content:space-between;align-items:center;"><div class="queue-coin">{r['Coin']}</div><span class="badge {badge_class(r['Alert'])}">{r['Alert']}</span></div><div style="font-weight:900;margin-top:6px;">{r['Command']}</div><div class="small">Next {r['Next Level']} @ ${r['Next Level Price']:,.4f}</div><div class="btc">+{r['BTC Gain']:.8f} BTC</div></div>""", unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Execute Signal</div>', unsafe_allow_html=True)
    executable=results[(results["Alert"].isin(["TRIM ZONE","REDUCE","EXIT FLOW"])) & (~results["Dismissed"]) & (~results["Executed"])].copy()
    if executable.empty: st.info("No executable rows.")
    else:
        labels=executable.apply(lambda r:f"{r['Coin']} · {r['Command']} · {r['BTC Gain']:.8f} BTC",axis=1).tolist()
        selected=st.selectbox("Signal",labels,label_visibility="collapsed"); row=executable.iloc[labels.index(selected)]
        if st.button("EXECUTE",type="primary",use_container_width=True): execute_row(row,btc_price); st.rerun()
        if st.button("DISMISS",use_container_width=True): dismiss_row(row); st.rerun()
with center:
    st.markdown('<div class="panel-title">Execution Grid</div>', unsafe_allow_html=True)
    st.dataframe(results[["Coin","Current Price","Alert","Command","Value","Next Level","Next Level Price","Progress","Sell Action","BTC Gain","Confidence","Executed","Dismissed"]],use_container_width=True,hide_index=True,height=520,column_config={"Current Price":st.column_config.NumberColumn(format="$%.6f"),"Value":st.column_config.NumberColumn(format="$%.2f"),"Next Level Price":st.column_config.NumberColumn(format="$%.6f"),"Progress":st.column_config.ProgressColumn("Progress",min_value=0,max_value=1,format="%d%%"),"Sell Action":st.column_config.NumberColumn(format="%.0%"),"BTC Gain":st.column_config.NumberColumn(format="%.8f BTC"),"Confidence":st.column_config.ProgressColumn("Status",min_value=0,max_value=100,format="%d%%")})
    b1,b2,b3=st.columns(3); b1.metric("Active Signals",len(active)); b2.metric("BTC Price",f"${btc_price:,.0f}"); b3.metric("Open Actions",len(executable))
with right:
    top=results[(~results["Dismissed"]) & (~results["Executed"])].iloc[0] if not results.empty else None
    st.markdown('<div class="panel-title">Signal Insight</div>', unsafe_allow_html=True)
    if top is not None:
        st.markdown(f"""<div class="panel"><div style="display:flex;justify-content:space-between;align-items:center;"><div class="queue-coin">{top['Coin']}</div><span class="badge {badge_class(top['Alert'])}">{top['Alert']}</span></div><div class="insight-big" style="margin-top:18px;">{top['Progress']:.0%}</div><div class="insight-label">to next trigger</div><hr style="border-color:#18304E;margin:16px 0;"><div class="small">Next Level</div><div style="font-weight:900;">{top['Next Level']} @ ${top['Next Level Price']:,.4f}</div><div class="small" style="margin-top:10px;">Expected BTC Gain</div><div class="btc">+{top['BTC Gain']:.8f} BTC</div><div class="small" style="margin-top:10px;">Confidence</div><div style="font-weight:900;">{top['Confidence']}%</div></div>""", unsafe_allow_html=True)
    st.markdown('<div class="panel-title" style="margin-top:14px;">BTC Accumulation</div>', unsafe_allow_html=True)
    st.progress(goal_progress,text=f"{current_stack:.8f} / {btc_goal:.8f} BTC")
    st.markdown(f'<div class="small">Remaining: {max(btc_goal-current_stack,0):.8f} BTC</div>', unsafe_allow_html=True)

st.markdown("---")
tabs=st.tabs(["Positions","Executions","Performance","Alerts","Backup"])
with tabs[0]:
    st.header("Positions + Sell Levels")
    if mode=="Demo Portfolio": st.dataframe(DEMO,use_container_width=True,hide_index=True)
    else:
        uploaded=st.file_uploader("Upload CSV",type=["csv"])
        if uploaded: st.session_state.portfolio=normalize(pd.read_csv(uploaded))
        st.session_state.portfolio=st.data_editor(st.session_state.portfolio,num_rows="dynamic",use_container_width=True)
    st.download_button("Download v2 CSV Template",pd.DataFrame(columns=REQUIRED).to_csv(index=False).encode(),"satscommander_position_engine_v2_template.csv","text/csv")
with tabs[1]:
    log=pd.DataFrame(st.session_state.executions); dismissed=pd.DataFrame(st.session_state.dismissed_alerts)
    c1,c2,c3=st.columns(3); c1.metric("Executed",len(log)); c2.metric("Dismissed",len(dismissed)); c3.metric("Discipline",f"{score}%")
    if not log.empty: st.dataframe(log,use_container_width=True,hide_index=True)
    if not dismissed.empty: st.subheader("Dismissed"); st.dataframe(dismissed,use_container_width=True,hide_index=True)
    if st.button("Clear Logs"): st.session_state.executions=[]; st.session_state.dismissed_alerts=[]; st.session_state.btc_total=0.0; st.rerun()
with tabs[2]:
    st.session_state.missed_snapshots.append({"Timestamp":datetime.now().strftime("%H:%M:%S"),"Captured BTC":captured,"Missed BTC":missed_btc,"Discipline Score":score})
    st.session_state.missed_snapshots=st.session_state.missed_snapshots[-50:]
    chart_df=pd.DataFrame(st.session_state.missed_snapshots)
    st.line_chart(chart_df.set_index("Timestamp")[["Captured BTC","Missed BTC"]]); st.line_chart(chart_df.set_index("Timestamp")[["Discipline Score"]])
with tabs[3]:
    alert_df=active[["Coin","Alert","Command","Current Price","Next Level Price","BTC Gain","Confidence"]].copy()
    st.dataframe(alert_df,use_container_width=True,hide_index=True) if not alert_df.empty else st.info("No active alerts.")
with tabs[4]:
    backup_payload={"portfolio":st.session_state.portfolio.to_dict(orient="records"),"executions":st.session_state.executions,"dismissed_alerts":st.session_state.dismissed_alerts,"btc_total":st.session_state.btc_total,"missed_snapshots":st.session_state.missed_snapshots}
    st.download_button("Download Private Backup JSON",json.dumps(backup_payload,indent=2).encode(),"satscommander_private_backup.json","application/json")
st.markdown('<div class="footer-note">SatsCommander Terminal · data refreshed every 60 seconds · CoinGecko prices</div>', unsafe_allow_html=True)
