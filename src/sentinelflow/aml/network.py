"""NetworkX AML graph analytics"""
import networkx as nx
import pandas as pd
from community import community_louvain

def build_graph(df:pd.DataFrame, min_weight=2):
    # bipartite customer-merchant
    G = nx.Graph()
    agg = df.groupby(["customer_id","merchant_id"]).size().reset_index(name="weight")
    agg = agg[agg["weight"]>=min_weight]
    for _, r in agg.iterrows():
        G.add_edge(f"C_{r.customer_id}", f"M_{r.merchant_id}", weight=int(r.weight))
    return G

def mule_score(df:pd.DataFrame, top_n=200):
    # fan-in/fan-out score
    g = df.groupby("account_id").agg(
        degree=("merchant_id","nunique"),
        volume=("amount","sum"),
        txns=("transaction_id","count")
    )
    g["mule_score"] = (g["degree"]/g["degree"].max()*40 + 
                       g["volume"]/g["volume"].max()*35 +
                       g["txns"]/g["txns"].max()*25).round(1)
    return g.sort_values("mule_score", ascending=False).head(top_n)

def community_detect(df:pd.DataFrame):
    G = build_graph(df, min_weight=1)
    if len(G)==0: return {}
    partition = community_louvain.best_partition(G)
    return partition
