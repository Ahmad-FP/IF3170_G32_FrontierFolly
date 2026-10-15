import json
from initial_state import gen_initial_state
from constraint import state_valid

# Membaca file packages.json
# https://www.geeksforgeeks.org/python/read-json-file-using-python/
with open("data/packages.json") as file:
    packages = json.load(file)

# Membaca file truck.json
with open("data/truck.json") as file:
    truck = json.load(file)

# Mendapatkan total nilai suatu paket di dalam truck
def total_value_in_truck(state, packages):
    total_nilai = 0
    # Melakukan perhitungan total nilai pada suatu state
    for package_id, placement in state.items(): # https://www.geeksforgeeks.org/python/python-accessing-key-value-in-dictionary/
        if placement["position"] is not None:
            total_nilai += packages[package_id]["value"]
    return total_nilai

# Pengetesan sebanyak 10 kali
for i in range(10):
    state = gen_initial_state(packages, truck)

    print(f"\nInitial State {i + 1}")

    for package_id, placement in state.items():
        print(package_id, placement)

    print("Valid:", state_valid(state, packages, truck))

    total_value = sum(
        packages[package_id]["value"]
        for package_id, placement in state.items()
        if placement["position"] is not None
    )

    print("Total Value:", total_value)