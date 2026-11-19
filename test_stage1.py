import sys
from pathlib import Path
from decimal import Decimal
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import default_state, simulate_month, add_run, validate_snapshot, snapshot_for_export, load_snapshot_json
import json

FIXTURE = Path(__file__).resolve().parents[1] / "sample_data" / "monthly_fixture.csv"

def run_fixture():
    rows = pd.read_csv(FIXTURE)
    cash, stock = Decimal("5000"), 100
    outputs = []
    for i, row in rows.iterrows():
        result = simulate_month(
            requested=int(row.requested), capacity=int(row.capacity_override),
            opening_stock_units=stock, restock_units=0, price=120,
            component_unit_cost=30, variable_per_unit=65, fixed_cost=600,
            ad_cost=int(row.ad_cost), opening_cash=cash, day=f"{row.month}-01",
            run_id=f"fixture-{row.month}", seed=42
        )
        outputs.append(result)
        cash, stock = result["ending_cash"], result["ending_stock_units"]
    return outputs

def test_fixture_all_months_expected():
    results = run_fixture()
    expected = [
        (30, "3600.00", "2550.00", "1050.00", "6950.00", 70, "2100.00"),
        (30, "3600.00", "2650.00", "950.00", "8800.00", 40, "1200.00"),
        (22, "2640.00", "2030.00", "610.00", "10070.00", 18, "540.00"),
    ]
    for r, e in zip(results, expected):
        assert (r["sold"], str(r["revenue"]), str(r["total_expense"]),
                str(r["operating_profit"]), str(r["ending_cash"]),
                r["ending_stock_units"], str(r["ending_inventory_value"])) == e

def test_failed_builds_consume_attempted_unit_cost_but_not_revenue():
    r = simulate_month(requested=10, capacity=10, opening_stock_units=20, restock_units=0,
                       price=120, defect_rate=0.2, opening_cash=5000)
    assert r["attempted"] == 10 and r["failed"] == 2 and r["sold"] == 8
    assert r["variable_expense"] == Decimal("650.00")
    assert r["revenue"] == Decimal("960.00")

def test_duplicate_run_id_rejected():
    s = default_state()
    r = simulate_month(requested=1, capacity=1, opening_stock_units=2, restock_units=0,
                       price=120, run_id="same")
    add_run(s, r)
    with pytest.raises(ValueError, match="already been accepted"):
        add_run(s, r)

def test_snapshot_round_trip_and_restart_reload():
    s = default_state()
    r = simulate_month(requested=3, capacity=3, opening_stock_units=10, restock_units=0,
                       price=120, run_id="reload-test")
    add_run(s, r)
    exported = snapshot_for_export(s)
    validate_snapshot(exported)
    loaded = load_snapshot_json(json.dumps(exported), default_state(), replace_ledger=True)
    assert loaded["ledger"] == s["ledger"]
    assert loaded["team_id"] == "ROB-POWER"

def test_wrong_team_and_stale_version_rejected():
    s = snapshot_for_export(default_state())
    s["team_id"] = "OTHER"
    with pytest.raises(ValueError, match="Team mismatch"):
        validate_snapshot(s)
    s["team_id"] = "ROB-POWER"
    s["state_version"] = 0
    with pytest.raises(ValueError, match="state_version"):
        validate_snapshot(s)

def test_nonempty_ledger_not_silently_overwritten():
    current = default_state()
    current["ledger"] = [{"transaction_id": "existing"}]
    incoming = snapshot_for_export(default_state())
    with pytest.raises(ValueError, match="Explicitly confirm"):
        load_snapshot_json(json.dumps(incoming), current, replace_ledger=False)

def test_invalid_defect_rate_and_negative_quantity_rejected():
    with pytest.raises(ValueError, match="defect_rate"):
        simulate_month(requested=1, capacity=1, opening_stock_units=1, restock_units=0,
                       price=120, defect_rate=1.1)
    with pytest.raises(ValueError, match="nonnegative"):
        simulate_month(requested=-1, capacity=1, opening_stock_units=1, restock_units=0, price=120)
