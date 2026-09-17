from sentinelflow.generator.transactions import generate

def test_generate_smoke():
    df, masters = generate(n=5000, seed=42)
    assert len(df)==5000
    assert "is_fraud" in df.columns
    assert df["is_fraud"].mean() > 0.005
    assert df["is_fraud"].mean() < 0.02
    assert "aml_flag" in df.columns
    assert "transaction_risk_score" in df.columns

def test_determinism():
    df1,_ = generate(1000, seed=7)
    df2,_ = generate(1000, seed=7)
    assert df1["transaction_id"].tolist() == df2["transaction_id"].tolist()
