from __future__ import annotations

import json
import math
import uuid
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

TEAM_ID = "ROB-POWER"
COURSE = "Precalculus"
PATHWAY_ID = "ROB-2"
CURRENCY = "USD"
STATE_VERSION = 1
DEFAULT_DATE = date(2027, 1, 1)
D = lambda x: Decimal(str(x))
CENT = Decimal("0.01")

def money(x: Any) -> Decimal:
    return D(x).quantize(CENT, rounding=ROUND_HALF_UP)

def dollars(x: Any) -> str:
    return f"${money(x):,.2f}"

def default_state() -> dict:
    return {
        "team_id": TEAM_ID, "course": COURSE, "pathway_id": PATHWAY_ID,
        "snapshot_id": str(uuid.uuid4()), "state_version": STATE_VERSION,
        "simulation_date": DEFAULT_DATE.isoformat(), "base_period": "monthly",
        "working_days": 20, "currency": CURRENCY,
        "level_by_skill": {"ROB-2-cost-model": "Advanced"},
        "assumptions": [
            {"name": "All business figures are fictional teaching assumptions", "value": True},
            {"name": "Supplier disruption scenario", "value": "15% component cost increase; one-week delivery delay"},
        ],
        "sources": [{"name": "Teacher-provided ROB-POWER specification", "type": "user_supplied"}],
        "offerings": [
            {"offering_id": "robot-kit", "name": "Introductory robot kit", "unit": "kit",
             "price": "120.00", "demand_rule": "editable monthly requested demand", "capacity_rule": "normal capacity"},
            {"offering_id": "sensor-upgrade", "name": "Sensor upgrade", "unit": "upgrade",
             "price": "0.00", "demand_rule": "not active in Stage 1", "capacity_rule": "not active in Stage 1"},
            {"offering_id": "repair-service", "name": "Repair service", "unit": "repair",
             "price": "0.00", "demand_rule": "not active in Stage 1", "capacity_rule": "not active in Stage 1"},
        ],
        "funding": [
            {"funding_id": "owner-contribution", "type": "owner_equity", "amount": "12000.00"},
            {"funding_id": "loan", "type": "loan", "amount": "0.00"},
        ],
        "cost_lines": [
            {"cost_id": "components_COGS", "name": "Components", "kind": "variable", "amount": "30.00", "unit": "attempted kit"},
            {"cost_id": "assembly_labor", "name": "Assembly labor", "kind": "variable", "amount": "20.00", "unit": "attempted kit"},
            {"cost_id": "packaging", "name": "Packaging", "kind": "variable", "amount": "10.00", "unit": "attempted kit"},
            {"cost_id": "warranty_consumables", "name": "Warranty consumables", "kind": "variable", "amount": "5.00", "unit": "attempted kit"},
            {"cost_id": "workspace", "name": "Workspace", "kind": "fixed", "amount": "250.00", "unit": "month"},
            {"cost_id": "software", "name": "Software", "kind": "fixed", "amount": "100.00", "unit": "month"},
            {"cost_id": "equipment_maintenance", "name": "Equipment maintenance", "kind": "fixed", "amount": "150.00", "unit": "month"},
            {"cost_id": "admin", "name": "Administration", "kind": "fixed", "amount": "100.00", "unit": "month"},
            {"cost_id": "advertising", "name": "Advertising", "kind": "marketing", "amount": "0.00", "unit": "month"},
        ],
        "capacity": {"staff_hours": 90, "hours_per_unit": 3, "opening_stock_units": 100,
                     "restock_units": 0, "component_unit_cost": "30.00", "defect_rate": 0.0,
                     "capacity_mode": "normal", "capacity_override": None},
        "ledger": [], "campaigns": [], "decisions": [],
        "controls": {"base_price": "120.00", "D0": 40, "opening_cash": "5000.00",
                     "refund_amount": "0.00", "loan_principal": "0.00", "interest": "0.00",
                     "additional_capex": "0.00", "run_id": "", "random_seed": 42},
        "runs": [],
        "opening_balances": {"owner_equity": "12000.00", "equipment_assets": "4000.00",
                             "preopening_expense": "0.00", "inventory_value": "3000.00",
                             "spendable_cash": "5000.00"},
    }

def validate_snapshot(s: dict, expected_team: str = TEAM_ID, expected_version: int = STATE_VERSION) -> None:
    required = ["team_id", "course", "pathway_id", "snapshot_id", "state_version", "simulation_date",
                "base_period", "working_days", "currency", "level_by_skill", "assumptions", "sources",
                "offerings", "funding", "cost_lines", "capacity", "ledger", "campaigns", "decisions"]
    missing = [k for k in required if k not in s]
    if missing:
        raise ValueError("Missing required snapshot fields: " + ", ".join(missing))
    if s["team_id"] != expected_team:
        raise ValueError(f"Team mismatch: expected {expected_team}, received {s['team_id']}.")
    if not isinstance(s["state_version"], int) or s["state_version"] != expected_version:
        raise ValueError(f"Unsupported/stale state_version. Expected {expected_version}.")
    try:
        date.fromisoformat(s["simulation_date"])
    except Exception as exc:
        raise ValueError("simulation_date must be a valid ISO date.") from exc
    if s["currency"] != "USD":
        raise ValueError("Only USD is supported in Stage 1.")
    for key in ["assumptions", "sources", "offerings", "funding", "cost_lines", "ledger", "campaigns", "decisions"]:
        if not isinstance(s[key], list):
            raise ValueError(f"{key} must be a list.")
    if not isinstance(s["capacity"], dict) or not isinstance(s["level_by_skill"], dict):
        raise ValueError("capacity and level_by_skill must be objects.")
    seen = set()
    for row in s["ledger"]:
        for field in ["transaction_id", "date", "event_type", "category", "amount", "quantity",
                      "unit_price", "offering_id", "campaign_id", "financing_type", "state_version"]:
            if field not in row:
                raise ValueError(f"Ledger row missing {field}.")
        date.fromisoformat(row["date"])
        if row["transaction_id"] in seen:
            raise ValueError("Duplicate transaction_id in imported ledger.")
        seen.add(row["transaction_id"])
        if D(row["quantity"]) < 0:
            raise ValueError("Ledger quantities cannot be negative.")
    for row in s["offerings"]:
        if not row.get("offering_id") or not row.get("name"):
            raise ValueError("Every offering requires offering_id and name.")
    for collection, field in [(s["offerings"], "offering_id"), (s["funding"], "funding_id"),
                              (s["cost_lines"], "cost_id")]:
        ids = [r.get(field) for r in collection]
        if len(ids) != len(set(ids)) or any(not x for x in ids):
            raise ValueError(f"{field} values must be present and unique.")

def make_transaction(day: str, event_type: str, category: str, amount: Decimal,
                     quantity: int = 0, unit_price: Decimal = Decimal("0"),
                     offering_id: str = "robot-kit", financing_type: str = "none",
                     state_version: int = STATE_VERSION) -> dict:
    return {
        "transaction_id": str(uuid.uuid4()), "date": day, "event_type": event_type,
        "category": category, "amount": str(money(amount)), "quantity": int(quantity),
        "unit_price": str(money(unit_price)), "offering_id": offering_id,
        "campaign_id": "", "financing_type": financing_type, "state_version": state_version,
    }

def simulate_month(*, requested: int, capacity: int, opening_stock_units: int,
                   restock_units: int, price: Any, component_unit_cost: Any = 30,
                   variable_per_unit: Any = 65, fixed_cost: Any = 600,
                   ad_cost: Any = 0, defect_rate: float = 0,
                   opening_cash: Any = 5000, day: str = "2027-01-01",
                   interest: Any = 0, principal: Any = 0, capex: Any = 0,
                   new_owner_cash: Any = 0, loan_cash: Any = 0,
                   run_id: str = "fixture-run", seed: int = 42) -> dict:
    if requested < 0 or capacity < 0 or opening_stock_units < 0 or restock_units < 0:
        raise ValueError("Requested demand, capacity, stock, and restock must be nonnegative.")
    if not 0 <= float(defect_rate) <= 1:
        raise ValueError("defect_rate must be between 0 and 1.")
    if D(price) <= 0 or D(component_unit_cost) < 0:
        raise ValueError("Price must be positive and component cost nonnegative.")
    attempted = min(int(requested), int(capacity), int(opening_stock_units) + int(restock_units))
    failed = math.floor(attempted * float(defect_rate))
    sold = attempted - failed
    component = D(component_unit_cost)
    total_variable = D(variable_per_unit)
    noncomponent = total_variable - component
    if noncomponent < 0:
        raise ValueError("Variable cost per unit cannot be below component cost.")
    revenue = money(D(price) * sold)
    variable_expense = money(total_variable * attempted)
    fixed = money(fixed_cost)
    marketing = money(ad_cost)
    total_expense = money(variable_expense + fixed + marketing)
    profit = money(revenue - total_expense)
    cash = money(D(opening_cash) + revenue - D(restock_units) * component
                 - D(attempted) * noncomponent - fixed - marketing - D(interest)
                 - D(principal) - D(capex) + D(new_owner_cash) + D(loan_cash))
    ending_stock = int(opening_stock_units) + int(restock_units) - attempted
    ledger = [
        make_transaction(day, "revenue", "kit_sales", revenue, sold, D(price)),
        make_transaction(day, "expense", "components_consumed", component * attempted, attempted, component),
        make_transaction(day, "expense", "noncomponent_variable", noncomponent * attempted, attempted, noncomponent),
        make_transaction(day, "expense", "fixed_costs", fixed),
        make_transaction(day, "expense", "marketing", marketing),
    ]
    for name, val, typ in [("interest", interest, "interest"), ("principal", principal, "principal"),
                           ("capex", capex, "capex"), ("owner_cash", new_owner_cash, "owner_contribution"),
                           ("loan_cash", loan_cash, "loan_proceeds")]:
        if D(val) != 0:
            ledger.append(make_transaction(day, typ, name, D(val), financing_type=typ))
    return {
        "run_id": run_id, "seed": int(seed), "requested": int(requested), "capacity": int(capacity),
        "attempted": attempted, "failed": failed, "sold": sold, "revenue": revenue,
        "variable_expense": variable_expense, "fixed_expense": fixed, "marketing_expense": marketing,
        "total_expense": total_expense, "operating_profit": profit, "ending_cash": cash,
        "opening_stock_units": int(opening_stock_units), "restock_units": int(restock_units),
        "ending_stock_units": ending_stock, "ending_inventory_value": money(ending_stock * component),
        "ledger": ledger, "day": day,
    }

def add_run(state: dict, result: dict) -> None:
    run_id = result["run_id"]
    if any(r["run_id"] == run_id for r in state.get("runs", [])):
        raise ValueError(f"Run '{run_id}' has already been accepted; duplicate transactions were prevented.")
    existing = {x["transaction_id"] for x in state["ledger"]}
    if any(x["transaction_id"] in existing for x in result["ledger"]):
        raise ValueError("Transaction ID collision; run was not added.")
    state["ledger"].extend(result["ledger"])
    state.setdefault("runs", []).append({
        "run_id": run_id, "seed": result["seed"], "date": result["day"],
        "sold": result["sold"], "profit": str(result["operating_profit"]),
        "closing_cash": str(result["ending_cash"]),
    })

def load_snapshot_json(raw: str, current_state: dict, replace_ledger: bool = False) -> dict:
    incoming = json.loads(raw)
    validate_snapshot(incoming)
    current_ids = {x["transaction_id"] for x in current_state["ledger"]}
    incoming_ids = {x["transaction_id"] for x in incoming["ledger"]}
    if current_ids and not replace_ledger:
        if current_ids & incoming_ids:
            raise ValueError("Import contains transactions already present. No ledger changes made.")
        raise ValueError("Current ledger is not empty. Explicitly confirm ledger replacement to load this snapshot.")
    return incoming

def snapshot_for_export(state: dict) -> dict:
    keys = ["team_id", "course", "pathway_id", "snapshot_id", "state_version", "simulation_date",
            "base_period", "working_days", "currency", "level_by_skill", "assumptions", "sources",
            "offerings", "funding", "cost_lines", "capacity", "ledger", "campaigns", "decisions"]
    out = {k: state[k] for k in keys}
    out["controls"] = state.get("controls", {})
    out["opening_balances"] = state.get("opening_balances", {})
    out["runs"] = state.get("runs", [])
    return out

def cost_line_total(state: dict, kind: str) -> Decimal:
    return sum((D(x["amount"]) for x in state["cost_lines"] if x["kind"] == kind), D(0))

def render_math_panel(state: dict):
    import streamlit as st
    st.subheader("Precalculus Math Skills · ROB-2")
    level = st.selectbox("Analysis level", ["Foundation", "Applied", "Advanced"],
                         index=["Foundation", "Applied", "Advanced"].index(
                             state["level_by_skill"].get("ROB-2-cost-model", "Advanced")))
    state["level_by_skill"]["ROB-2-cost-model"] = level
    st.caption("Course skill: function modeling, composition, transformations, domain/range, and trigonometric modeling.")
    st.caption("Units: q and s are kits/month; p is USD/kit; cost and revenue are USD/month.")
    if level == "Foundation":
        q = st.slider("Production quantity s (kits/month)", 1, 100, 30)
        total = 600 + 65*q
        avg = total/q
        st.latex(r"C(q)=600+65q")
        st.latex(r"A(s)=\frac{C(s)}{s}=\frac{600}{s}+65,\quad 0<s\leq \text{capacity}")
        st.write(f"At {q} kits: total cost C({q}) = **{dollars(total)} per month**; average cost A({q}) = **{dollars(avg)} per kit**.")
        st.info("C(30) is the total monthly cost of producing 30 kits ($2,550). A(30) is the average cost per kit ($85). They have different units.")
        st.warning("A(0) is undefined. Vertical asymptote: s = 0. Horizontal asymptote: y = 65 USD/kit. The model is practical only for positive production within capacity.")
        xs = np.linspace(0.5, 100, 400)
        fig, ax = plt.subplots()
        ax.plot(xs, 600/xs + 65, label="Average cost A(s)")
        ax.axvline(0, linestyle="--", label="Vertical asymptote s=0")
        ax.axhline(65, linestyle=":", label="Horizontal asymptote y=65")
        ax.set(xlabel="Production s (kits/month)", ylabel="Average cost (USD/kit)", title="Average cost and asymptotes")
        ax.legend()
        st.pyplot(fig)
    elif level == "Applied":
        p0 = float(D(state["controls"]["base_price"]))
        d0 = int(state["controls"]["D0"])
        cap = int(state["capacity"]["staff_hours"] // state["capacity"]["hours_per_unit"])
        cap = max(0, cap)
        st.latex(r"q(p)=\max(0,\,2D_0-(D_0/p_0)p)")
        st.latex(r"s(p)=\min(\mathrm{capacity},q(p)),\quad R(p)=p\,s(p)")
        st.latex(r"P(p)=R(p)-[600+65s(p)]")
        if d0 > 0:
            bp = p0*(2-cap/d0)
            st.write(f"Input-output mapping: price p → requested demand q(p) → completed sales s(p) → revenue R(p) → profit P(p).")
            st.write(f"Capacity = **{cap} kits/month**; breakpoint p = p₀(2 − capacity/D₀) = **${bp:,.2f} per kit**.")
            prices = np.linspace(0, 2*p0, 241)
            demand = np.maximum(0, 2*d0-(d0/p0)*prices)
            sales = np.minimum(cap, demand)
            revenue = prices*sales
            costs = 600+65*sales
            profits = revenue-costs
            fig, ax = plt.subplots()
            ax.plot(prices, demand, label="Requested demand q(p)")
            ax.plot(prices, sales, label="Completed sales s(p)")
            ax.axhline(cap, linestyle=":", label="Capacity")
            ax.set(xlabel="Price (USD/kit)", ylabel="Units/month", title="Demand composed with capacity")
            ax.legend()
            st.pyplot(fig)
            fig2, ax2 = plt.subplots()
            ax2.plot(prices, revenue, label="Revenue R(p)")
            ax2.plot(prices, costs, label="Cost C(s(p))")
            ax2.plot(prices, profits, label="Profit P(p)")
            ax2.axhline(0, color="black", linewidth=0.8, label="Zero line")
            ax2.set(xlabel="Price (USD/kit)", ylabel="USD/month", title="Composed revenue, cost, and profit")
            ax2.legend()
            st.pyplot(fig2)
            idxs = np.linspace(0, 240, 9).astype(int)
            st.dataframe(pd.DataFrame({"Price (USD/kit)": prices[idxs], "Demand (continuous)": demand[idxs],
                                       "Sales (continuous)": sales[idxs], "Revenue (USD)": revenue[idxs],
                                       "Cost (USD)": costs[idxs], "Profit (USD)": profits[idxs]}),
                         use_container_width=True)
            st.caption("Graphs use continuous-valued analysis. Actual transactions round completed builds to whole kits.")
        else:
            st.warning("Set D0 above zero to evaluate the demand composition.")
        st.caption("Assumptions: linear demand reaches zero at 2p₀; no price response beyond the specified domain 0 ≤ p ≤ 2p₀.")
    else:
        st.warning("Advanced seasonal model is locked until explicitly enabled and approved. No teacher-approved skills were supplied.")
        enabled = st.checkbox("Enable fictional seasonal model for this working scenario")
        approved = st.checkbox("I have teacher approval to use this model")
        if enabled and approved:
            d0 = int(state["controls"]["D0"])
            months = np.arange(1, 13)
            demand = d0*(1+0.20*np.sin(2*np.pi*(months-1)/12))
            capacity = max(0, int(state["capacity"]["staff_hours"] // state["capacity"]["hours_per_unit"]))
            sales = np.minimum(capacity, demand)
            st.latex(r"D(t)=D_0\left(1+0.20\sin\left(\frac{2\pi(t-1)}{12}\right)\right)")
            st.write("Month index t has period 12; peak at t=4 (1.2D₀), minimum at t=10 (0.8D₀).")
            fig, ax = plt.subplots()
            ax.plot(months, demand, marker="o", label="Original seasonal demand")
            ax.plot(months, sales, marker="s", label="Capacity-limited sales")
            ax.set(xlabel="Month index t", ylabel="Kits/month", title="Assumed seasonal demand vs realized sales")
            ax.legend()
            st.pyplot(fig)
            st.caption("This is a fictional assumed seasonal pattern, not measured market data. Do not extrapolate beyond the modeled 12-month cycle without justification.")
        else:
            st.info("Advanced model remains locked. Enabling it here does not change the approved business snapshot or ledger.")

def main():
    import streamlit as st
    st.set_page_config(page_title="Career Venture Lab · ROB-POWER", layout="wide")
    if "state" not in st.session_state:
        st.session_state.state = default_state()
    state = st.session_state.state
    st.title("Career Venture Lab")
    st.caption("ROB-POWER · Robotics kit and repair studio · Precalculus / ROB-2 · Advanced")
    pages = ["Overview", "Inputs and Funding", "Math Skills", "Ledger and Simulation", "Save / Load / Export",
             "Cross-Course Connections", "Customers", "Operations", "Finance", "AI Recommendations",
             "Marketing Studio", "Report Center", "Assessment", "Decisions", "Storefront"]
    page = st.sidebar.radio("Stage 1 workspace", pages)
    st.sidebar.success("Stage 1 active")
    st.sidebar.caption("Stage 2–4 modules are not yet implemented.")
    if page == "Overview":
        st.header("Venture overview")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Spendable opening cash", dollars(state["opening_balances"]["spendable_cash"]))
        c2.metric("Opening inventory", "100 sets")
        c3.metric("Equipment assets", dollars(state["opening_balances"]["equipment_assets"]))
        c4.metric("Owner equity", dollars(state["opening_balances"]["owner_equity"]))
        st.write("Opening assets reconcile to owner equity: $4,000 equipment + $3,000 inventory + $5,000 cash = $12,000.")
        st.info("Stage 1 is deterministic and uses fictional teaching data. No paid AI service, live payment, or automatic deployment is used.")
        if state["ledger"]:
            df = pd.DataFrame(state["ledger"])
            st.metric("Ledger transactions", len(df))
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No monthly simulation has been accepted yet.")
    elif page == "Inputs and Funding":
        st.header("Inputs and startup funding")
        st.subheader("Startup balances")
        st.write("Owner contribution: $12,000 · Tools: $2,500 · Test equipment: $1,500 · Opening inventory: 100 sets × $30 = $3,000 · Post-startup cash: $5,000.")
        st.caption("Equipment and opening inventory are assets. Neither is expensed again at startup.")
        ctrl = state["controls"]; cap = state["capacity"]
        a,b,c = st.columns(3)
        ctrl["base_price"] = str(money(a.number_input("Base kit price (USD)", min_value=0.01, value=float(ctrl["base_price"]), step=1.0)))
        ctrl["D0"] = int(b.number_input("Requested demand D₀ (kits/month)", min_value=0, value=int(ctrl["D0"]), step=1))
        cap["staff_hours"] = float(c.number_input("Productive staff hours/month", min_value=0.0, value=float(cap["staff_hours"]), step=1.0))
        a,b,c = st.columns(3)
        cap["hours_per_unit"] = float(a.number_input("Productive hours per attempted kit", min_value=0.01, value=float(cap["hours_per_unit"]), step=0.25))
        cap["opening_stock_units"] = int(b.number_input("Opening component sets", min_value=0, value=int(cap["opening_stock_units"]), step=1))
        cap["restock_units"] = int(c.number_input("Paid restock sets this month", min_value=0, value=int(cap["restock_units"]), step=1))
        a,b,c = st.columns(3)
        cap["component_unit_cost"] = str(money(a.number_input("Component cost per set (USD)", min_value=0.0, value=float(cap["component_unit_cost"]), step=1.0)))
        cap["defect_rate"] = b.number_input("Failed-build rate", min_value=0.0, max_value=1.0, value=float(cap["defect_rate"]), step=0.01)
        st.metric("Normal capacity", f"{int(cap['staff_hours'] // cap['hours_per_unit'])} kits/month")
        st.subheader("Cost lines")
        cost_df = pd.DataFrame(state["cost_lines"])
        edited = st.data_editor(cost_df, disabled=["cost_id", "name", "kind", "unit"], use_container_width=True,
                                column_config={"amount": st.column_config.NumberColumn("Amount", min_value=0.0, format="%.2f")})
        for row in edited.to_dict("records"):
            match = next(x for x in state["cost_lines"] if x["cost_id"] == row["cost_id"])
            match["amount"] = str(money(row["amount"]))
        st.write(f"Variable cost per attempted kit: **{dollars(cost_line_total(state, 'variable'))}**")
        st.write(f"Monthly fixed costs: **{dollars(cost_line_total(state, 'fixed'))}**")
        st.caption("Baseline variable rows are components $30, assembly labor $20, packaging $10, warranty consumables $5. Fixed rows total $600.")
        state["simulation_date"] = st.date_input("Simulation date", date.fromisoformat(state["simulation_date"])).isoformat()
    elif page == "Math Skills":
        render_math_panel(state)
    elif page == "Ledger and Simulation":
        st.header("Deterministic monthly simulation")
        st.caption("Normal mode derives capacity from staff hours. Fixture-test mode is reserved for the supplied fixture and is never mixed with normal mode.")
        c1,c2 = st.columns(2)
        requested = int(c1.number_input("Requested units this month", min_value=0, value=int(state["controls"]["D0"]), step=1))
        run_id = c2.text_input("Unique run ID", value=f"ROB-POWER-{state['simulation_date']}")
        seed = st.number_input("Random seed (recorded for reproducibility)", min_value=0, value=int(state["controls"]["random_seed"]), step=1)
        state["controls"]["run_id"] = run_id
        state["controls"]["random_seed"] = int(seed)
        capacity = int(state["capacity"]["staff_hours"] // state["capacity"]["hours_per_unit"])
        restock = int(state["capacity"]["restock_units"])
        comp = D(state["capacity"]["component_unit_cost"])
        variable = cost_line_total(state, "variable")
        fixed = cost_line_total(state, "fixed")
        ad = next(D(x["amount"]) for x in state["cost_lines"] if x["cost_id"] == "advertising")
        if st.button("Calculate and accept this monthly run", type="primary"):
            try:
                result = simulate_month(requested=requested, capacity=capacity,
                    opening_stock_units=int(state["capacity"]["opening_stock_units"]), restock_units=restock,
                    price=state["controls"]["base_price"], component_unit_cost=comp,
                    variable_per_unit=variable, fixed_cost=fixed, ad_cost=ad,
                    defect_rate=state["capacity"]["defect_rate"], opening_cash=state["controls"]["opening_cash"],
                    day=state["simulation_date"], interest=state["controls"]["interest"],
                    principal=state["controls"]["loan_principal"], capex=state["controls"]["additional_capex"],
                    run_id=run_id, seed=int(seed))
                add_run(state, result)
                state["controls"]["opening_cash"] = str(result["ending_cash"])
                state["capacity"]["opening_stock_units"] = result["ending_stock_units"]
                state["capacity"]["restock_units"] = 0
                st.session_state.last_result = result
                st.success("Run accepted once. Ledger, cash, and inventory updated.")
            except Exception as e:
                st.error(str(e))
        if "last_result" in st.session_state:
            r = st.session_state.last_result
            cols = st.columns(4)
            cols[0].metric("Attempted", r["attempted"]); cols[1].metric("Failed", r["failed"])
            cols[2].metric("Sold", r["sold"]); cols[3].metric("Operating profit", dollars(r["operating_profit"]))
            st.write(f"Revenue {dollars(r['revenue'])} · Total expense {dollars(r['total_expense'])} · Closing cash {dollars(r['ending_cash'])} · Closing inventory {r['ending_stock_units']} sets ({dollars(r['ending_inventory_value'])}).")
        if state["ledger"]:
            st.dataframe(pd.DataFrame(state["ledger"]), use_container_width=True)
    elif page == "Save / Load / Export":
        st.header("Snapshot management")
        snapshot = snapshot_for_export(state)
        raw = json.dumps(snapshot, indent=2)
        st.download_button("Download snapshot JSON", raw, file_name="ROB-POWER_snapshot.json", mime="application/json")
        csv = pd.DataFrame(state["ledger"]).to_csv(index=False)
        st.download_button("Download ledger CSV", csv, file_name="ROB-POWER_ledger.csv", mime="text/csv")
        upload = st.file_uploader("Load a JSON snapshot", type=["json"])
        replace = st.checkbox("I explicitly authorize replacing the current ledger with the imported snapshot")
        if upload is not None and st.button("Validate and load snapshot"):
            try:
                loaded = load_snapshot_json(upload.getvalue().decode("utf-8"), state, replace_ledger=replace)
                st.session_state.state = loaded
                st.success("Snapshot validated and loaded.")
                st.rerun()
            except Exception as e:
                st.error(f"Import rejected: {e}")
        st.caption("Imports must match team_id ROB-POWER and state_version 1. Existing ledgers are never silently overwritten.")
    else:
        st.header(page)
        st.warning("Not Yet Implemented")
        st.write("This module is reserved for a later Career Venture Lab stage. Stage 1 does not claim this functionality is active.")
    st.sidebar.divider()
    st.sidebar.caption("Fictional educational simulation · No real payments")

if __name__ == "__main__":
    main()
