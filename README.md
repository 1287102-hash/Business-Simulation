# Career Venture Lab — ROB-POWER (Stage 1)

A fictional, deterministic Streamlit learning app for the Robotics Kit and Repair Studio, Precalculus pathway ROB-2.

## Stage 1 scope

Implemented:
- Venture inputs, startup balances, staffing-derived capacity, inventory, defect rate, and editable cost rows.
- Foundation, Applied, and gated Advanced Precalculus math panel.
- Deterministic monthly simulation and dated ledger.
- Separate profit, cash, and inventory calculations.
- JSON snapshot export/import and CSV ledger export.
- Team/state-version validation, duplicate-run protection, and tests.

Other requested modules are visible as **Not Yet Implemented**. No paid APIs, live AI, payment processing, or automatic deployment are used.

## Startup balances

Owner contribution: $12,000. Equipment assets: $4,000 (tools $2,500; test equipment $1,500). Opening inventory: $3,000 (100 component sets × $30). Post-startup spendable cash: $5,000. Pre-opening expense and opening retained earnings: $0.

## Run locally

Python 3.10+ is recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## Run tests

```bash
pytest -q
```

Expected result: all Stage 1 tests pass. The monthly fixture test checks all three supplied months.

## Render setup (manual)

1. Push this folder to a GitHub repository.
2. In Render, create a ** new Web Service** and connect that repository.
3. Build command: `pip install -r requirements.txt`
4. Start command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
5. Deploy manually when ready. This project does not deploy or publish automatically.

## Fixture mode

`sample_data/monthly_fixture.csv` is an acceptance fixture. Its capacity_override values (30, 30, 22) are used only by the automated fixture tests. The live app uses normal capacity `floor(staff_hours / hours_per_unit)` and does not read fixture overrides into normal simulations.

## Accounting conventions

- Components are expensed when consumed; cash leaves when restock purchases are made.
- Noncomponent variable costs are paid for every attempted build.
- Failed builds consume attempted-unit costs but earn no sales revenue.
- Opening inventory and equipment are assets, not startup expenses.
- Operating profit = revenue − attempted-unit variable expense − fixed expense − marketing.
- Ending cash follows the specified cash equation and can differ from profit.
- No tax assumption is introduced.

## Data transfer

Snapshot JSON includes the required contract fields plus `controls`, `opening_balances`, and `runs`. Import checks team ID, state version, dates, required fields, unique IDs, and nonnegative quantities. A nonempty current ledger requires explicit replacement confirmation. CSV is for human inspection, not round-trip restoration.

## Manual acceptance checklist

- [ ] App starts with `streamlit run app.py`.
- [ ] Overview opening assets reconcile: $4,000 equipment + $3,000 inventory + $5,000 cash = $12,000 owner equity.
- [ ] Normal capacity equals `floor(staff_hours / hours_per_unit)`.
- [ ] Cost rows total $65 per attempted kit and $600 fixed per month.
- [ ] Foundation shows `A(0)` undefined, vertical asymptote `s=0`, horizontal asymptote `y=65`, and distinguishes `C(30)` from `A(30)`.
- [ ] Applied panel shows the composed demand/sales/revenue/cost/profit mapping and capacity breakpoint.
- [ ] Advanced seasonal model is unavailable unless both enable and approval controls are selected.
- [ ] A normal run updates cash, inventory, and ledger exactly once.
- [ ] Reusing a run ID is rejected.
- [ ] JSON export can be loaded after app restart.
- [ ] Importing a different team or stale version is rejected.
- [ ] Import cannot silently overwrite an existing ledger.
- [ ] CSV export opens as a human-readable ledger.
- [ ] All three fixture months match expected sold units, revenue, expenses, profit, cash, and stock.
- [ ] Stage 2–4 modules display Not Yet Implemented.

## Known Stage 1 boundaries

- Only the primary robot-kit offering is active in monthly calculations. Sensor upgrades and repair services are listed but not separately costed or sold.
- Campaigns, customer analytics, staffing plans beyond productive hours, and decision approval workflow are later-stage work.
- The supplier disruption is identified as a scenario assumption; full delivery-delay/inventory scheduling is not implemented in Stage 1.
- The Advanced model's approval check is a student-facing gate, not a verified teacher authorization system.
- The current ledger is append-only during normal operation; loading a replacement snapshot requires explicit confirmation.
