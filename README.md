🇬🇧 English · 🇵🇱 [Wersja polska](README.pl.md)

# Production & Transport Optimization — MILP Model

A mixed-integer linear programming (MILP) model that jointly optimizes **production planning** and **distribution/fleet routing** for a two-product manufacturer serving three clients. Built and solved in Excel Solver, cross-validated against an independent open-source solver.

**Optimal result: profit of 213,750 PLN**, achieved by producing to full demand and consolidating shipments into the largest vehicle, with a single mid-size truck trip closing the one load that the big truck cannot fill economically.

---

## Problem

A manufacturer produces two products (P1, P2) on two machines (M1, M2) and delivers them to three clients (C1, C2, C3) using a fleet of three vehicle types. The goal is to choose production volumes, shipment allocations, and the number of trips per vehicle so as to **maximize total profit**:

```
profit = revenue − production cost − machine fixed cost − labour cost − transport cost
```

## Model structure

**Decision variables**
- Production quantity per product: `P1`, `P2`
- Units shipped per (vehicle, client, product): `x[v,c,p]` — integer
- Number of trips per (vehicle, client): `t[v,c]` — integer
- Machine on/off: `y[m]` — binary

**Objective (maximize)** — profit, as defined above.

**Constraints**
- **Production ≤ demand** — each product's output cannot exceed total market demand.
- **Machine capacity** — hours consumed on each machine ≤ 300 h, gated by the machine's on/off binary. Every unit of both products is processed on both machines.
- **Supply** — total units shipped of a product ≤ its production.
- **Demand satisfaction** — units delivered to each client equal that client's demand, per product (equality).
- **Vehicle capacity** — units carried by a vehicle to a client ≤ trips × vehicle capacity.
- **Trip aggregation** — total trips per vehicle = sum of its per-client trips.

## Input data

| Products | Price [PLN] | Prod. cost [PLN] |
|---|---|---|
| P1 | 900 | 500 |
| P2 | 650 | 400 |

| Client | P1 demand | P2 demand | Distance [km] |
|---|---|---|---|
| C1 | 200 | 200 | 40 |
| C2 | 300 | 300 | 110 |
| C3 | 300 | 375 | 240 |

| Machine | P1 [h/unit] | P2 [h/unit] | Limit [h] | Fixed cost [PLN] |
|---|---|---|---|---|
| M1 | 0.10 | 0.15 | 300 | 12,000 |
| M2 | 0.15 | 0.10 | 300 | 9,000 |

| Vehicle | Type | Capacity | Fuel [PLN/km] | Fixed cost [PLN/trip] |
|---|---|---|---|---|
| V1 | small bus | 10 | 1.8 | 180 |
| V2 | mid truck | 22 | 2.0 | 420 |
| V3 | large truck | 34 | 2.1 | 530 |

**Labour:** fixed 120,000 PLN + variable 85 PLN/unit.
**Trip cost** for a vehicle to a client = `distance × fuel + fixed cost`.

## Results

| Component | Value [PLN] |
|---|---|
| Revenue | 1,288,750 |
| − Production cost | 750,000 |
| − Machine fixed cost | 21,000 |
| − Labour | 262,375 |
| − Transport | 41,625 |
| **= Profit (objective)** | **213,750** |

- **Production:** P1 = 800, P2 = 875 units — full demand is met, since every unit is profitable and machine capacity is not binding (M1 uses 211.25 / 300 h, M2 uses 207.5 / 300 h).
- **Fleet:** V3 (large truck) runs **49 trips** (12 → C1, 17 → C2, 20 → C3); V2 (mid truck) runs **1 trip** → C2; V1 is **not used**.
- The single V2 trip carries exactly the 22 units to C2 that remain after the large truck is filled — the one place where a partial mid-truck run beats both an extra full large-truck trip and several small-bus trips.

## Key assumptions

- **Per-trip cost = fixed + variable.** The fixed part (`Fixed cost pln/trip`) bundles driver, loading/handling, dispatch and per-cycle wear — a per-dispatch charge, not a per-period or per-km one. Spread across a larger capacity it lowers cost per unit, giving the economies of scale that drive load consolidation into bigger vehicles while right-sizing the remainder.
- **Both products are processed on both machines** — the machine constraints model total time across both stages.
- **Vehicles carry mixed products** — capacity is measured in units regardless of product.
- **Fleet availability is unlimited** — trips are not capped per vehicle; the model sizes usage purely on cost.

## Methodology notes

The model is linear, so it is solved with the **Simplex LP** engine, which Solver automatically wraps in branch-and-bound because the trip counts and shipment quantities are declared integer — Simplex LP solves the continuous relaxations, and branch-and-bound enforces integrality on top. (`Integer Optimality (%)` is itself a branch-and-bound parameter and would not exist for a pure LP.)

**Critical setting: `Integer Optimality (%) = 0.00001`.**
Excel Solver's default integer tolerance (1–5%) stops at the *first* integer-feasible solution within that gap of the bound and reports it as "Optimal" — without proving optimality. On this problem the default masked a **494 PLN gap (0.23%)** and excluded vehicle V2 from the solution entirely, producing a plausible-but-wrong answer (three small-bus trips instead of one mid-truck trip). Tightening the tolerance to ~0 recovers the true optimum.

A note on engine choice: an early run used **GRG Nonlinear**, which is inappropriate for a linear model and converged to a suboptimal local incumbent. Switching to Simplex LP is required for a global integer optimum.

**Cross-validation:** the optimum was reproduced independently with **HiGHS** (open-source MILP solver) — identical result (213,750 PLN, one V2 trip), confirming the Excel formulation is correct and the solution is globally optimal.

## Python implementation

The model is also implemented in Python (`optimization_production_transport.py`), using PuLP with the bundled CBC solver — a third independent formulation and solver, on top of the HiGHS cross-check above.

**Result: identical profit of 213,750 PLN**, with the same production quantities (P1=800, P2=875) and the same fleet allocation (V3: 49 trips, V2: 1 trip to C2, V1 unused) — confirming the Excel formulation once more, this time via a from-scratch integer program rather than a spreadsheet transcription.

## How to run

1. Open `Optimization_Production_Transport.xlsx` in Excel.
2. `Data → Solver`. The objective cell, decision cells, and constraints are pre-configured.
3. Engine: **Simplex LP**. In `Options → All Methods`, set **Integer Optimality (%) = 0.00001**.
4. `Solve`. The objective should reach **213,750**.
5. Alternatively, run the Python implementation: `pip install pulp`, then `python optimization_production_transport.py`. Expected output: `Status: Optimal`, `Profit: 213750.0`.

---

*Author: [LukaszB-DA](https://github.com/LukaszB-DA) · Portfolio project — production & transport optimization (MILP) / operations research.*
