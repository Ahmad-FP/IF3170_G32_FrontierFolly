import json
from constraint import *

# Membaca file packages.json
# https://www.geeksforgeeks.org/python/read-json-file-using-python/
with open("../data/packages.json") as file:
    packages = json.load(file)

# Membaca file truck.json
with open("../data/truck.json") as file:
    truck = json.load(file)

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
        "position": (7, 0, 0),
        "orientation": (0, 1, 2)
    }
}

print("State valid  :", state_valid(state, packages, truck)) # Hasil yang diharapkan True

# Tes 1: Semua paket berada di lantai
print("Test 1       :", state_valid(state, packages, truck))
# True

print("Orientation  :", check_orientation(state)) # True
print("Bounds       :", check_bounds(state, packages, truck)) # True
print("Collision    :", check_collision(state, packages)) # True
print("Weight       :", check_weight(state, packages, truck)) # True
print("Support      :", check_support(state, packages)) # True
print("Fragile      :", check_fragile(state, packages)) # True
print("\n")

# Tes 2: Paket B collision dengan A
state["B"]["position"] = (2, 0, 0)
print("Test 2       :", state_valid(state, packages, truck))
# False

print("Orientation  :", check_orientation(state)) # True
print("Bounds       :", check_bounds(state, packages, truck)) # True
print("Collision    :", check_collision(state, packages)) # False
print("Weight       :", check_weight(state, packages, truck)) # True
print("Support      :", check_support(state, packages)) # True
print("Fragile      :", check_fragile(state, packages)) # True
print("\n")

# Tes 3: Paket B melayang
state["B"]["position"] = (3, 0, 2)
print("Test 3       :", state_valid(state, packages, truck))
# False

print("Orientation  :", check_orientation(state)) # True
print("Bounds       :", check_bounds(state, packages, truck)) # True
print("Collision    :", check_collision(state, packages)) # True
print("Weight       :", check_weight(state, packages, truck)) # True
print("Support      :", check_support(state, packages)) # False
print("Fragile      :", check_fragile(state, packages)) # True
print("\n")

# Tes 4: Paket B out of bounds
state["B"]["position"] = (8, 10, 0)
print("Test 4       :", state_valid(state, packages, truck))
# False

print("Orientation  :", check_orientation(state)) # True
print("Bounds       :", check_bounds(state, packages, truck)) # False
print("Collision    :", check_collision(state, packages)) # True
print("Weight       :", check_weight(state, packages, truck)) # True
print("Support      :", check_support(state, packages)) # True
print("Fragile      :", check_fragile(state, packages)) # True
print("\n")

# Tes 5: Paket fragile B menopang paket A
state["A"]["position"] = (0, 0, 2)
state["B"]["position"] = (0, 0, 0)

print("Test 5       :", state_valid(state, packages, truck))
# False

print("Orientation  :", check_orientation(state)) # True
print("Bounds       :", check_bounds(state, packages, truck)) # True
print("Collision    :", check_collision(state, packages)) # True
print("Weight       :", check_weight(state, packages, truck)) # True
print("Support      :", check_support(state, packages)) # True
print("Fragile      :", check_fragile(state, packages)) # False