import pulp as pl

# === MODEL PARAMETERS ===
# Parametry 

PRODUCTS = ["P1", "P2"]  # products / produkty
CLIENTS = ["C1", "C2", "C3"]  # clients / klienci
MACHINES = ["M1", "M2"]  # machines / maszyny
VEHICLES = ["V1", "V2", "V3"]  # vehicles: small bus, mid truck, large truck / pojazdy: mały bus, średnia ciężarówka, duża ciężarówka

# Selling price per unit [pln] / Cena sprzedaży za sztukę [pln]
price = {"P1": 900, "P2": 650}

# Production cost per unit [pln] / Koszt produkcji za sztukę [pln]
prod_cost = {"P1": 500, "P2": 400}

# Demand per client and product [units] / Popyt per klient i produkt [szt.]
demand = {
    ("C1", "P1"): 200, ("C1", "P2"): 200,
    ("C2", "P1"): 300, ("C2", "P2"): 300,
    ("C3", "P1"): 300, ("C3", "P2"): 375,
}

# Machine processing time per unit [h/unit] / Czas obróbki maszyny na sztukę [h/szt.]
machine_time = {
    ("M1", "P1"): 0.1, ("M1", "P2"): 0.15,
    ("M2", "P1"): 0.15, ("M2", "P2"): 0.1,
}

# Machine capacity limit [h] / Limit godzin pracy maszyny [h]
machine_limit = {"M1": 300, "M2": 300}

# Machine fixed cost [pln] / Koszt stały maszyny [pln]
machine_fixed_cost = {"M1": 12000, "M2": 9000}

# Vehicle capacity per trip [units] / Pojemność pojazdu na kurs [szt.]
vehicle_capacity = {"V1": 10, "V2": 22, "V3": 34}

# Fuel cost per km [pln/km] / Koszt paliwa za km [pln/km]
vehicle_fuel_cost = {"V1": 1.8, "V2": 2.0, "V3": 2.1}

# Fixed cost per trip [pln/trip] / Koszt stały za kurs [pln/kurs]
vehicle_trip_fixed_cost = {"V1": 180, "V2": 420, "V3": 530}

# Distance to each client [km] / Odległość do klienta [km]
distance = {"C1": 40, "C2": 110, "C3": 240}

# Labour costs / Koszty robocizny
labour_fixed_cost = 120000  # fixed [pln] / stały [pln]
labour_variable_cost = 85   # variable, per unit produced [pln/unit] / zmienny, na wyprodukowaną sztukę [pln/szt.]

# Cost of a single vehicle trip to a client [pln]
# = distance * fuel cost + trip fixed cost
# Koszt jednego kursu pojazdu do klienta [pln]
# = odległość * koszt paliwa + koszt stały kursu
transport_cost = {
    (v, c): distance[c] * vehicle_fuel_cost[v] + vehicle_trip_fixed_cost[v]
    for v in VEHICLES for c in CLIENTS
}

# Define the optimization problem (maximize profit)
# Definiujemy problem optymalizacyjny (maksymalizacja zysku)
model = pl.LpProblem("Production_Transport_Optimization", pl.LpMaximize)

# === DECISION VARIABLES ===
# Decision variable: how many units of P1 to produce (continuous, >= 0)
# Zmienna decyzyjna: ile sztuk P1 wyprodukować (ciągła, >= 0)
qty_produced_P1 = pl.LpVariable("qty_produced_P1", lowBound = 0)

# Decision variable: how many units of P2 to produce (continuous, >= 0)
# Zmienna decyzyjna: ile sztuk P2 wyprodukować (ciągła, >= 0)
qty_produced_P2 = pl.LpVariable("qty_produced_P2", lowBound = 0)

# Shipment quantity of P1 by vehicle to client (integer, >= 0)
# Ilość P1 wysłana danym pojazdem do klienta (całkowita, >= 0)

ship_P1 = {}

for vehicle in VEHICLES:
    for client in CLIENTS:
        ship_P1[(vehicle, client)] = pl.LpVariable(f"ship_P1_{vehicle}_{client}", lowBound = 0, cat="Integer"
        )

# Shipment quantity of P2 by vehicle to client (integer, >= 0)
# Ilość P2 wysłana danym pojazdem do klienta (całkowita, >= 0)

ship_P2 = {}

for vehicle in VEHICLES:
    for client in CLIENTS:
        ship_P2[(vehicle,client)] = pl.LpVariable(f"ship_P2_{vehicle}_{client}", lowBound = 0, cat="Integer"
        )

# Machine usage indicator: 1 if machine is used, 0 otherwise (binary)
# Wskaźnik użycia maszyny: 1 jeśli maszyna jest używana, 0 jeśli nie (binarna)

machine_used = {}

for machine in MACHINES:
    machine_used[machine] = pl.LpVariable(f"machine_used_{machine}", cat="Binary")

# Number of trips a vehicle makes to a client (integer, >= 0)
# Liczba kursów danego pojazdu do klienta (całkowita, >= 0)

trips = {}

for vehicle in VEHICLES:
    for client in CLIENTS:
        trips[(vehicle,client)] = pl.LpVariable(f"trips_{vehicle}_{client}", lowBound = 0, cat="Integer"
        )

# === CONSTRAINTS ===
# Total production of P1 cannot exceed total demand across all clients
# Całkowita produkcja P1 nie może przekroczyć sumy popytu wszystkich klientów

model += qty_produced_P1 <= pl.lpSum(demand[(client, "P1")] for client in CLIENTS)

# Total production of P2 cannot exceed total demand across all clients
# Całkowita produkcja P2 nie może przekroczyć sumy popytu wszystkich klientów

model += qty_produced_P2 <= pl.lpSum(demand[(client, "P2")] for client in CLIENTS)

# Production quantity per product (continuous, >= 0)
# Wyprodukowana ilość na produkt (ciągła, >= 0)

qty_produced = {
    "P1" : qty_produced_P1,
    "P2" : qty_produced_P2
}

# Total processing time on a machine cannot exceed its hour limit,
# but only if the machine is switched on (0 if machine_used = 0)
# Łączny czas obróbki na maszynie nie może przekroczyć limitu godzin,
# ale tylko jeśli maszyna jest włączona (0 gdy machine_used = 0)

for machine in MACHINES:
    model += (
        pl.lpSum(
            qty_produced[product] * machine_time[(machine, product)]
            for product in PRODUCTS
        )
        <= machine_limit[machine] * machine_used[machine]
    )

# For each vehicle-client pair: quantity shipped (P1+P2) cannot exceed
# trips to that specific client times vehicle capacity
# Dla każdej pary pojazd-klient: ilość przewieziona (P1+P2) nie może przekroczyć
# liczby kursów do tego konkretnego klienta razy pojemność pojazdu

for vehicle in VEHICLES:
    for client in CLIENTS:
        model += (
            ship_P1[(vehicle, client)] + ship_P2[(vehicle,client)]
            <= trips[(vehicle,client)] * vehicle_capacity[vehicle]
        )

# Total quantity of P1 delivered to a client (all vehicles) must exactly match its demand
# Łączna ilość P1 dostarczona do klienta (wszystkie pojazdy) musi dokładnie równać się popytowi

for client in CLIENTS:
    model += (
        pl.lpSum(ship_P1[(vehicle, client)] for vehicle in VEHICLES)
        == demand[(client, "P1")]
    )

# Same for P2 / To samo dla P2

for client in CLIENTS:
    model += (
        pl.lpSum(ship_P2[(vehicle,client)] for vehicle in VEHICLES)
        == demand[(client, "P2")]
    )

# Total shipped P1 (all vehicles, all clients) cannot exceed total produced
# Łączna wysyłka P1 (wszystkie pojazdy, wszyscy klienci) nie może przekroczyć wyprodukowanej ilości

model += (
    pl.lpSum(ship_P1[(vehicle, client)] for vehicle in VEHICLES for client in CLIENTS)
    <= qty_produced["P1"]
)

# Same for P2 / To samo dla P2

model += (
    pl.lpSum(ship_P2[(vehicle,client)] for vehicle in VEHICLES for client in CLIENTS)
    <= qty_produced["P2"]
)

# Revenue = production quantity * price, summed over both products
# Przychód = ilość wyprodukowana * cena, zsumowane po obu produktach

income = pl.lpSum(qty_produced[p] * price[p] for p in PRODUCTS)

# Production cost = production quantity * unit cost, summed over both products
# Koszt produkcji = ilość wyprodukowana * koszt jednostkowy, zsumowane po obu produktach

production_cost = pl.lpSum(qty_produced[p] * prod_cost[p] for p in PRODUCTS)

# Fixed machine cost = paid only if the machine is switched on
# Koszt stały maszyny = płacony tylko jeśli maszyna jest włączona

fixed_machine_cost = pl.lpSum(machine_used[m] * machine_fixed_cost[m] for m in MACHINES)

# Transport cost = number of trips * cost per trip, summed over every vehicle-client pair
# Koszt transportu = liczba kursów * koszt jednego kursu, zsumowane po każdej parze pojazd-klient

transport_total = pl.lpSum(trips[(v,c)] * transport_cost[(v,c)] for v in VEHICLES for c in CLIENTS)

# Labour cost = fixed cost + variable cost per unit produced (both products)
# Koszt robocizny = koszt stały + koszt zmienny na wyprodukowaną sztukę (oba produkty)

labour_total =labour_fixed_cost + labour_variable_cost * pl.lpSum(qty_produced[p] for p in PRODUCTS)

# Objective: maximize profit = income - production cost - fixed machine cost - transport - labour
# Cel: maksymalizacja zysku = przychód - koszt produkcji - koszt stały maszyn - transport - robocizna

model += income - production_cost - fixed_machine_cost - transport_total - labour_total

# Solve with explicit zero relative gap, to guarantee a proven optimum
# rather than a solution merely within some tolerance of it
# Rozwiąż z jawnie zerową tolerancją względną, aby zagwarantować
# udowodnione optimum, a nie rozwiązanie jedynie w pewnej jego tolerancji

model.solve(pl.PULP_CBC_CMD(gapRel=0.0))

# Check solver status (should be "Optimal")
# Sprawdź status solvera (powinno być "Optimal")

print("Status:", pl.LpStatus[model.status])

# Read optimal production quantities
# Odczytaj optymalne ilości produkcji
print("P1 produced:", qty_produced["P1"].varValue)
print("P2 produced:", qty_produced["P2"].varValue)

# Read shipments (only print non-zero ones, to avoid clutter)
# Odczytaj wysyłki (tylko niezerowe, żeby nie zaśmiecać wyniku)
for (vehicle, client), var in ship_P1.items():
    if var.varValue > 0:
        print(f"P1: {vehicle} -> {client}: {var.varValue}")

for (vehicle, client), var in ship_P2.items():
    if var.varValue > 0:
        print(f"P2: {vehicle} -> {client}: {var.varValue}")

# Read profit (the objective function value)
# Odczytaj zysk (wartość funkcji celu)
print("Profit:", pl.value(model.objective))
