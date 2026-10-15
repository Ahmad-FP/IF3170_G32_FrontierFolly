import json
import sys
from pathlib import Path

# Mengambil module di luar path parent kode ini
# https://docs.python.org/3.13/tutorial/modules.html
# https://docs.python.org/3.14/library/pathlib.html
sys.path.append(str(Path(__file__).resolve().parent.parent))

from constraint import state_valid
from initial_state import gen_initial_state

# Membaca file packages.json
# https://www.geeksforgeeks.org/python/read-json-file-using-python/
with open("../data/packages.json") as file:
    packages = json.load(file)

# Membaca file truck.json
with open("../data/truck.json") as file:
    truck = json.load(file)

# Mendapatkan total nilai suatu paket di dalam truck
def total_value_in_truck(state, packages):
    total_nilai = 0
    # Melakukan perhitungan total nilai pada suatu state
    for package_id, placement in state.items(): # https://www.geeksforgeeks.org/python/python-accessing-key-value-in-dictionary/
        if placement["position"] is not None:
            total_nilai += packages[package_id]["value"]
    return total_nilai

# print(packages)
# print(truck)

# Representasi awal state untuk ujicoba
state = {
    "A": {
        "position": (0, 0, 0),
        "orientation": (0, 1, 2)
    },
    "B": {
        "position": (3, 0, 0),
        "orientation": (0, 1, 2)
    },
    "C": {
        "position": None,
        "orientation": (0, 1, 2)
    }
}

# print(total_value_in_truck(state, packages))
# print("State valid") if state_valid(state, packages, truck) else print("State tidak valid")
print(gen_initial_state(packages, truck))