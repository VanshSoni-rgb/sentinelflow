"""AML typology definitions"""
AML_TYPOLOGIES = [
 "structuring","smurfing","rapid_movement","layering","mule_account",
 "round_trip","high_risk_jurisdiction","tbml","pep_proximity"
]

RULES_YAML = """
R001_structuring_near_10k:
  description: Cash structured just below CTR threshold
  threshold: 9500
  window: 24h
R007_rapid_movement_24h:
  description: Fan-out >5 counterparties in 24h
"""
