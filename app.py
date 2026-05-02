import json
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd
import streamlit as st

st.set_page_config(page_title="SatsCommander Pro Terminal v2", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp{background:#04070D;color:#E5E7EB}.block-container{max-width:1740px;padding-top:1.15rem;padding-left:1rem;padding-right:1rem}
h1,h2,h3{color:#F8FAFC;margin:.25rem 0 .45rem 0}
[data-testid="stMetric"]{background:linear-gradient(180deg,#0C1422,#070B13);border:1px solid #163252;border-radius:10px;padding:10px 12px;box-shadow:0 0 20px rgba(0,209,255,.04)}
[data-testid="stMetricLabel"]{color:#00D1FF!important;font-size:.68rem!important;font-weight:900;text-transform:uppercase}
[data-testid="stMetricValue"]{color:#F8FAFC!important;font-size:1.35rem!important;font-weight:950}
section[data-testid="stSidebar"]{background:#060A12;border-right:1px solid #163252}
.terminal-shell{border:1px solid #163252;background:linear-gradient(180deg,#0B1220,#060A12);border-radius:14px;padding:18px 18px 14px 18px;margin:8px 0 12px 0;box-shadow:0 0 28px rgba(0,209,255,.05)}
.topbar{display:flex;justify-content:space-between;align-items:center;gap:14px}
.brand-title{font-size:32px;line-height:1;font-weight:950;color:white;letter-spacing:.2px}
.brand-sub{color:#F7931A;font-weight:900;font-size:12px;margin-top:5px}
.status-pill{border-radius:999px;padding:5px 9px;font-size:11px;font-weight:900}.online{background:#052E1A;color:#22C55E;border:1px solid #14532D}
.panel-title{color:#CBD5E1;font-size:12px;font-weight:950;text-transform:uppercase;letter-spacing:.05em;margin:8px 0}
.queue-item{border:1px solid #163252;background:linear-gradient(180deg,#0B1220,#070B13);border-radius:10px;padding:9px;margin-bottom:8px}
.queue-coin{font-size:19px;color:white;font-weight:950}.small{color:#94A3B8;font-size:11px}.btc{color:#F7931A;font-weight:950;text-shadow:0 0 12px rgba(247,147,26,.22)}
.badge{padding:4px 7px;border-radius:6px;font-weight:950;font-size:10px;display:inline-block;letter-spacing:.03em}
.exit{background:#EF4444;color:white}.reduce{background:#FB923C;color:#0B0B0B}.trim{background:#FACC15;color:#0B0B0B}.armed{background:#22C55E;color:#0B0B0B}.watch{background:#1E293B;color:#CBD5E1;border:1px solid #475569}.standby{background:#0F172A;color:#64748B;border:1px solid #334155}.executed{background:#06B6D4;color:#001018}
.grid-wrap{border:1px solid #163252;border-radius:12px;overflow:hidden;background:#070B13}
.grid-head,.grid-row{display:grid;grid-template-columns:.7fr .9fr 1fr 1.5fr .9fr .95fr 1.1fr .75fr;gap:0;align-items:center}
.grid-head{background:#0A101A;color:#94A3B8;font-size:11px;font-weight:950;text-transform:uppercase;letter-spacing:.04em}
.grid-head div{padding:9px 10px;border-right:1px solid #14253B}
.grid-row{position:relative;background:#08101D;border-top:1px solid #14253B;transition:all .15s ease}
.grid-row:hover{background:#0D1728;box-shadow:inset 0 0 0 1px rgba(0,209,255,.16)}
.grid-row div{padding:10px;border-right:1px solid #14253B;font-size:13px}
.strip-exit{border-left:4px solid #EF4444}.strip-reduce{border-left:4px solid #FB923C}.strip-trim{border-left:4px solid #FACC15}.strip-armed{border-left:4px solid #22C55E}.strip-watch{border-left:4px solid #64748B}.strip-standby{border-left:4px solid #1E293B}.strip-executed{border-left:4px solid #06B6D4}
.progress-outer{height:7px;background:#162235;border-radius:999px;overflow:hidden}.progress-inner{height:7px;border-radius:999px;background:linear-gradient(90deg,#F7931A,#EF4444)}
.dial{width:190px;height:190px;border-radius:50%;display:grid;place-items:center;margin:auto;background:conic-gradient(var(--dial-color) calc(var(--pct)*1%),#162235 0);box-shadow:0 0 35px rgba(0,209,255,.08)}
.dial-inner{width:138px;height:138px;border-radius:50%;background:#07111F;display:grid;place-items:center;border:1px solid #163252}.dial-num{font-size:40px;font-weight:950;color:white;line-height:1}.dial-label{color:#94A3B8;font-size:11px;text-align:center}
.signal-panel{background:#07111F;border:1px solid #163252;border-radius:12px;padding:14px}
.footer-note{color:#64748B;font-size:11px;text-align:right}.compact-btn button{height:2rem!important}

/* pro polish */
.stTabs [data-baseweb="tab-list"]{gap:18px;border-bottom:1px solid #111827}
.stTabs [data-baseweb="tab"]{color:#64748B;font-weight:900;padding:8px 0}
.stTabs [aria-selected="true"]{color:#FF4B4B!important;border-bottom:2px solid #FF4B4B}
.kpi-sub{font-size:10px;color:#64748B;text-transform:uppercase;letter-spacing:.08em}
.dark-table{border:1px solid #163252;border-radius:12px;overflow:hidden;background:#070B13;margin-top:10px}
.dark-head,.dark-row{display:grid;grid-template-columns:.8fr 1fr 1fr 1fr 1fr 1fr 1fr 1fr;align-items:center}
.dark-head{background:#0A101A;color:#94A3B8;font-size:11px;font-weight:950;text-transform:uppercase}
.dark-head div,.dark-row div{padding:10px;border-right:1px solid #14253B}
.dark-row{border-top:1px solid #14253B;background:#08101D}
.dark-row:hover{background:#0D1728}
.bottom-card{background:linear-gradient(180deg,#0B1220,#070B13);border:1px solid #163252;border-radius:12px;padding:14px;min-height:135px}
.bottom-title{font-size:12px;color:#CBD5E1;text-transform:uppercase;letter-spacing:.05em;font-weight:950;margin-bottom:8px}
.alloc-row{display:flex;align-items:center;justify-content:space-between;margin:7px 0;font-size:12px}
.alloc-bar{height:7px;background:#152238;border-radius:999px;overflow:hidden;margin-left:8px;flex:1}
.alloc-fill{height:7px;background:linear-gradient(90deg,#F7931A,#00D1FF);border-radius:999px}
.feed-row{display:flex;justify-content:space-between;border-bottom:1px solid #14253B;padding:7px 0;font-size:12px}

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

for k,v in {"portfolio":pd.DataFrame(columns=REQUIRED),"executions":[],"dismissed_alerts":[],"missed_snapshots":[],"btc_total":0.0}.items():
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
        for key in ["executions","dismissed_alerts","missed_snapshots"]: st.session_state[key]=restored.get(key,[])
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
def strip_class(alert):
    return {"EXIT FLOW":"strip-exit","REDUCE":"strip-reduce","TRIM ZONE":"strip-trim","ARMED":"strip-armed","WATCH":"strip-watch","EXECUTED":"strip-executed"}.get(alert,"strip-standby")
def dial_color(alert):
    return {"EXIT FLOW":"#EF4444","REDUCE":"#FB923C","TRIM ZONE":"#FACC15","ARMED":"#22C55E","WATCH":"#64748B"}.get(alert,"#334155")

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

st.markdown("""<div class="terminal-shell topbar"><div><div class="brand-title">SatsCommander</div><div class="brand-sub">Pro terminal v2 · execution queue · signal insight · BTC accumulation</div></div><div class="status-pill online">● MARKET DATA LIVE</div></div>""", unsafe_allow_html=True)

captured=float(st.session_state.btc_total); current_stack=starting_btc+captured; goal_progress=min(current_stack/btc_goal,1) if btc_goal else 0
queued_btc=results[results["Alert"].isin(["TRIM ZONE","REDUCE","EXIT FLOW"])]["BTC Gain"].sum(); missed_btc=max(queued_btc-captured,0); score=discipline_score(); total_value=results["Value"].sum()
m1,m2,m3,m4,m5=st.columns(5)
m1.metric("BTC HELD / GOAL",f"{current_stack:.8f}",f"{goal_progress:.1%}")
m2.metric("QUEUED BTC",f"{queued_btc:.8f}")
m3.metric("MISSED BTC",f"{missed_btc:.8f}")
m4.metric("DISCIPLINE",f"{score}%")
m5.metric("PORTFOLIO",f"${total_value:,.0f}")

left,center,right=st.columns([1.08,2.55,1.12],gap="medium")
with left:
    st.markdown('<div class="panel-title">Execution Queue</div>', unsafe_allow_html=True)
    queue=results[(results["Alert"].isin(["EXIT FLOW","REDUCE","TRIM ZONE","ARMED"])) & (~results["Dismissed"]) & (~results["Executed"])].head(5)
    if queue.empty: st.markdown('<div class="queue-item small">No active sell signals. Monitoring trigger levels.</div>', unsafe_allow_html=True)
    for _,r in queue.iterrows():
        st.markdown(f"""<div class="queue-item {strip_class(r['Alert'])}"><div style="display:flex;justify-content:space-between;align-items:center;"><div class="queue-coin">{r['Coin']}</div><span class="badge {badge_class(r['Alert'])}">{r['Alert']}</span></div><div style="font-weight:900;margin-top:6px;">{r['Command']}</div><div class="small">Next {r['Next Level']} @ ${r['Next Level Price']:,.4f}</div><div class="btc">+{r['BTC Gain']:.8f} BTC</div></div>""", unsafe_allow_html=True)
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
    rows_html=[]
    for _,r in results.iterrows():
        rows_html.append(f"""<div class="grid-row {strip_class(r['Alert'])}">
            <div><b>{r['Coin']}</b></div>
            <div>${r['Current Price']:,.4f}</div>
            <div><span class="badge {badge_class(r['Alert'])}">{r['Alert']}</span></div>
            <div><b>{r['Command']}</b><br><span class="small">{r['Next Level']} @ ${r['Next Level Price']:,.4f}</span></div>
            <div>${r['Value']:,.0f}</div>
            <div><span class="btc">+{r['BTC Gain']:.8f}</span></div>
            <div><div class="progress-outer"><div class="progress-inner" style="width:{r['Progress']*100:.0f}%"></div></div><span class="small">{r['Progress']:.0%}</span></div>
            <div>{r['Confidence']}%</div>
        </div>""")
    st.markdown(f"""<div class="grid-wrap">
        <div class="grid-head"><div>Coin</div><div>Price</div><div>Signal</div><div>Action</div><div>Value</div><div>BTC Gain</div><div>Progress</div><div>Status</div></div>
        {''.join(rows_html)}
    </div>""", unsafe_allow_html=True)
    b1,b2,b3=st.columns(3); b1.metric("Active Signals",len(active)); b2.metric("BTC Price",f"${btc_price:,.0f}"); b3.metric("Open Actions",len(executable))

    # Bottom pro panels: BTC accumulation, recent executions, allocation snapshot
    p1,p2,p3 = st.columns(3)
    with p1:
        st.markdown(f'''<div class="bottom-card"><div class="bottom-title">BTC Accumulation</div>
        <div class="small">Current BTC</div><div class="btc">{current_stack:.8f} BTC</div>
        <div class="small" style="margin-top:8px;">Queued Actions</div><div class="btc">+{queued_btc:.8f} BTC</div>
        <div style="margin-top:10px;"></div></div>''', unsafe_allow_html=True)
        st.progress(goal_progress, text=f"{goal_progress:.1%} to goal")
    with p2:
        recent = list(reversed(st.session_state.executions[-3:]))
        if recent:
            rows = ''.join([f'<div class="feed-row"><span>{x.get("Coin","")} · {x.get("Command","")[:18]}</span><span class="btc">+{float(x.get("BTC Captured",0)):.8f}</span></div>' for x in recent])
        else:
            rows = '<div class="small">No executions yet.</div>'
        st.markdown(f'<div class="bottom-card"><div class="bottom-title">Recent Executions</div>{rows}</div>', unsafe_allow_html=True)
    with p3:
        alloc = results[["Coin","Value"]].copy()
        tv = float(alloc["Value"].sum()) if not alloc.empty else 0
        alloc = alloc.sort_values("Value", ascending=False).head(5)
        alloc_rows = ""
        for _,a in alloc.iterrows():
            pct = (float(a["Value"])/tv*100) if tv else 0
            alloc_rows += f'<div class="alloc-row"><span>{a["Coin"]}</span><div class="alloc-bar"><div class="alloc-fill" style="width:{pct:.0f}%"></div></div><span>{pct:.1f}%</span></div>'
        st.markdown(f'<div class="bottom-card"><div class="bottom-title">Portfolio Allocation</div>{alloc_rows}</div>', unsafe_allow_html=True)
with right:
    top=results[(~results["Dismissed"]) & (~results["Executed"])].iloc[0] if not results.empty else None
    st.markdown('<div class="panel-title">Signal Insight</div>', unsafe_allow_html=True)
    if top is not None:
        pct=int(top["Progress"]*100); color=dial_color(top["Alert"])
        st.markdown(f"""<div class="signal-panel"><div style="display:flex;justify-content:space-between;align-items:center;"><div class="queue-coin">{top['Coin']}</div><span class="badge {badge_class(top['Alert'])}">{top['Alert']}</span></div>
        <div class="dial" style="--pct:{pct};--dial-color:{color};margin-top:14px;"><div class="dial-inner"><div><div class="dial-num">{pct}%</div><div class="dial-label">to next trigger</div></div></div></div>
        <hr style="border-color:#18304E;margin:14px 0;"><div class="small">Next Level</div><div style="font-weight:900;">{top['Next Level']} @ ${top['Next Level Price']:,.4f}</div>
        <div class="small" style="margin-top:10px;">Expected BTC Gain</div><div class="btc">+{top['BTC Gain']:.8f} BTC</div>
        <div class="small" style="margin-top:10px;">Confidence</div><div style="font-weight:900;">{top['Confidence']}%</div></div>""", unsafe_allow_html=True)
    st.markdown('<div class="panel-title" style="margin-top:12px;">BTC Accumulation</div>', unsafe_allow_html=True)
    st.progress(goal_progress,text=f"{current_stack:.8f} / {btc_goal:.8f} BTC")
    st.markdown(f'<div class="small">Remaining: {max(btc_goal-current_stack,0):.8f} BTC</div>', unsafe_allow_html=True)

st.markdown("---")
tabs=st.tabs(["Positions","Executions","Performance","Alerts","Backup"])
with tabs[0]:
    st.header("Positions + Sell Levels")
    if mode=="Demo Portfolio":
        rows = []
        for _,r in DEMO.iterrows():
            rows.append(f"""<div class="dark-row"><div><b>{r['Coin']}</b></div><div>{r['Amount']:,.4f}</div><div>${r['Level 1 Price']:,.6f}</div><div>{r['Level 1 Sell %']:.0%}</div><div>${r['Level 2 Price']:,.6f}</div><div>{r['Level 2 Sell %']:.0%}</div><div>${r['Level 3 Price']:,.6f}</div><div>{r['Level 3 Sell %']:.0%}</div></div>""")
        st.markdown(f"""<div class="dark-table">
        <div class="dark-head"><div>Coin</div><div>Amount</div><div>Level 1</div><div>Sell 1</div><div>Level 2</div><div>Sell 2</div><div>Level 3</div><div>Sell 3</div></div>
        {''.join(rows)}
        </div>""", unsafe_allow_html=True)
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
st.markdown('<div class="footer-note">SatsCommander Pro Terminal · data refreshed every 60 seconds · CoinGecko prices</div>', unsafe_allow_html=True)
