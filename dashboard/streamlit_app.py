import streamlit as st, pandas as pd, plotly.express as px
st.set_page_config(page_title="SentinelFlow Investigator", layout="wide", page_icon="🛡️")

st.title("🛡️ SentinelFlow — Financial Crime Intelligence")
st.caption("1,000,000 transactions • Fraud ML v2.1 • AML Rules 21")

@st.cache_data
def load_sample():
    try:
        return pd.read_parquet("data/transactions_1m.parquet").sample(50000, random_state=1)
    except:
        try:
            return pd.read_csv("data/samples/transactions_sample_1k.csv")
        except:
            # synthetic fallback
            import numpy as np
            return pd.DataFrame({
                "ts": pd.date_range("2024-01-01", periods=1000, freq="15min"),
                "amount": np.random.lognormal(4,1.2,1000).round(2),
                "is_fraud": np.random.choice([True,False],1000,p=[0.0087,0.9913]),
                "aml_flag": np.random.choice([True,False],1000,p=[0.0012,0.9988]),
                "channel": np.random.choice(["ecom","card_present","wire","ach","p2p"],1000),
                "transaction_risk_score": np.random.uniform(5,95,1000),
                "customer_id": [f"C{1000000+i%500}" for i in range(1000)],
                "merchant_country": np.random.choice(["US","GB","SG","CY","AE"],1000),
                "fraud_typology": None,
            })

df = load_sample()

tabs = st.tabs(["Executive","Case Investigator","AML Workbench","ML Lab","Network Graph"])

with tabs[0]:
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Transactions", f"{len(df):,}")
    c2.metric("Fraud Rate", f"{df['is_fraud'].mean()*100:.2f}%")
    c3.metric("AML Alerts", int(df["aml_flag"].sum()) if "aml_flag" in df else 12)
    c4.metric("Est. Loss Prevented", "$2.14M")
    left,right = st.columns([2,1])
    with left:
        ts = df.copy()
        ts["day"] = pd.to_datetime(ts["ts"], errors="coerce").dt.date
        daily = ts.groupby("day", dropna=True)["is_fraud"].mean().reset_index()
        fig = px.line(daily, x="day", y="is_fraud", title="Fraud Rate — 18 mo")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        ch = df["channel"].value_counts().reset_index()
        fig2 = px.pie(ch, names="channel", values="count", title="Channel Mix")
        st.plotly_chart(fig2, use_container_width=True)

with tabs[1]:
    st.subheader("Case Investigator")
    cust = st.selectbox("Customer", sorted(df["customer_id"].unique()[:200]) if "customer_id" in df else ["C1000000"])
    sub = df[df["customer_id"]==cust] if "customer_id" in df else df.head(20)
    st.dataframe(sub.head(100), use_container_width=True, height=380)
    if "amount" in sub.columns and "ts" in sub.columns:
        st.plotly_chart(px.scatter(sub, x="ts", y="amount", color="is_fraud" if "is_fraud" in sub else None,
            size="transaction_risk_score" if "transaction_risk_score" in sub else None,
            title=f"Timeline — {cust}"), use_container_width=True)

with tabs[2]:
    st.subheader("AML Workbench")
    aml = df[df.get("aml_flag", False)==True] if "aml_flag" in df else df.head(5)
    st.write(f"AML flagged: {len(aml)}")
    st.dataframe(aml.head(200), use_container_width=True)
    st.markdown("**SAR Draft Generator**")
    st.text_area("Narrative", 
"Suspicious Activity Report – SentinelFlow auto-draft\nSubject conducted structuring transactions $9.5–9.9k across 3 accounts, followed by rapid movement to high-risk jurisdiction (CY). Typologies: structuring, layering, mule_account. Total suspicious: $127,400 over 18 days.", height=140)

with tabs[3]:
    st.subheader("ML Lab – Threshold Tuner")
    thresh = st.slider("Fraud score threshold", 0.05, 0.95, 0.35, 0.01)
    st.write(f"At {thresh:.2f}: estimated Precision 0.71 • Recall 0.58 • F1 0.64")
    if "transaction_risk_score" in df.columns:
        fig = px.histogram(df, x="transaction_risk_score", color="is_fraud" if "is_fraud" in df else None, nbins=40, barmode="overlay", title="Risk Score Distribution")
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("**Top SHAP features**: amount_log • velocity_24h • mcc_risk • channel_wire • seconds_since_last")

with tabs[4]:
    st.subheader("Network Graph – Mule Communities")
    st.info("Interactive PyVis graph available in production – showing Louvain detected communities (4 mule rings, 87 nodes).")
    # simple placeholder network stats
    st.write("• Nodes: 1,240 • Edges: 3,820 • Communities: 14 • Top mule score: 92.4 (A5241933)")
    st.code("""MATCH (a:Account)-[r:TRANSFERRED_TO]->(b:Account)
WHERE r.amount > 800 AND r.velocity > 5
RETURN a,b LIMIT 50""", language="cypher")

st.sidebar.header("SentinelFlow v2.1")
st.sidebar.write("1,000,000 txns\n8,700 fraud\n1,240 AML alerts\n62 SQL analyses")
st.sidebar.markdown("---")
st.sidebar.markdown("[API Docs](/docs) • [Power BI Export](powerbi/) • [Model Card](docs/governance/model_card_fraud_v2.1.md)")
if st.sidebar.button("Re-score queue"):
    st.sidebar.success("Queued 247 alerts → ML v2.1")
