# 🛡️ Sprint 10: Risk Management & Position Sizing

> **Status:** Complete ✅  
> **Objective:** Build an institutional-grade position sizing engine to protect account capital, calculate exact pip values across currency conventions, and provide risk-to-reward ratios.

---

## 🏗️ Architecture & Engineering Decisions

1. **Precision Math with `Decimal`:**
   - All balance, pip, and lot calculations use Python's `Decimal` with `ROUND_HALF_UP` to prevent floating-point rounding errors.

2. **Dynamic Pip Scaling:**
   - Standard pairs (EUR/USD, GBP/USD) evaluate pips at the 4th decimal place (`0.0001`).
   - JPY quote pairs (USD/JPY, EUR/JPY) evaluate pips at the 2nd decimal place (`0.01`).

3. **Multi-tier Lot Sizing:**
   - Standard Lots (100,000 units)
   - Mini Lots (10,000 units)
   - Micro Lots (1,000 units)

4. **Risk-to-Reward Ratio (R:R):**
   - Computes potential upside against downside risk: `R:R = |TP - Entry| / |Entry - SL|`

---

## 💻 CLI Commands

```bash
# Calculate sizing using prices on EUR/USD with 1% risk on a $10,000 account
forex risk calc --pair EUR/USD --balance 10000 --risk-pct 1.0 --entry 1.1200 --stop-loss 1.1150 --take-profit 1.1300

# Calculate sizing using pip distances (SL = 30 pips, TP = 60 pips)
forex risk calc --pair EUR/USD --balance 25000 --risk-pct 1.5 --sl-pips 30 --tp-pips 60

# Calculate sizing for JPY pairs
forex risk calc --pair USD/JPY --balance 10000 --risk-pct 1.0 --entry 154.50 --stop-loss 154.00 --take-profit 155.50
```

---

## 🧪 Test Coverage (`tests/test_risk.py`)

- Verification of JPY vs. 4-decimal currency pip resolution.
- Lot sizing formulas across account balances and risk thresholds.
- Input validation against negative balances, identical entry/SL, and >100% risk.
- Service orchestration with pip-derived SL/TP targets.
