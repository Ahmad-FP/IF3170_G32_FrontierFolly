from genetic_algorithm import encode_state, decode_state, gen_initial_pop, fitness, roulette_selection, repair_state, repair_chromosome, crossover, mutation
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

## Testing encoder dan decoder
state = {
    "A": {
        "position": (0, 0, 0),
        "orientation": (0, 1, 2)
    },
    "B": {
        "position": (3, 0, 0),
        "orientation": (1, 0, 2)
    },
    "C": {
        "position": None,
        "orientation": (2, 0, 1)
    }
}

chromosome = encode_state(state, packages)
decoded = decode_state(chromosome, packages)

print("Original:", state)
print("Chromosome:", chromosome)
print("Decoded:", decoded)
print("Same State:", state == decoded)
print("\n")

## Testing initial population dan fitness function
population = gen_initial_pop(packages, truck, 10)

fitness_values = []

for i, chromosome in enumerate(population):
    score = fitness(chromosome, packages, truck)
    fitness_values.append(score)

    print(f"Individu {i + 1}: {score}")

print("Best Fitness:", max(fitness_values))
print("Average Fitness:", sum(fitness_values) / len(fitness_values))
print("\n")

## Testing roulette_selection
parent_1 = roulette_selection(population, packages, truck)
parent_2 = roulette_selection(population, packages, truck)

print("Parent 1:", parent_1)
print("Fitness 1:", fitness(parent_1, packages, truck))

print("Parent 2:", parent_2)
print("Fitness 2:", fitness(parent_2, packages, truck))
print("\n")

## Testing repair state
# Test collision
state_invalid = {
    "A": {
        "position": (0, 0, 0),
        "orientation": (0, 1, 2)
    },
    "B": {
        "position": (0, 0, 0),
        "orientation": (0, 1, 2)
    },
    "C": {
        "position": None,
        "orientation": (0, 1, 2)
    }
}

# State sebelum repair
print("Before:", state_valid(state_invalid, packages, truck))

# Repair state
repaired = repair_state(state_invalid, packages, truck)

# State setelah repair
print("After:", state_valid(repaired, packages, truck))
print("Repaired State:", repaired)

## Menguji repair chromosome
chromosome = encode_state(state, packages)
repaired_chromosome = repair_chromosome(chromosome, packages, truck)

decoded = decode_state(repaired_chromosome, packages)

print("Chromosome Valid:", state_valid(decoded, packages, truck))
print("Same Repair:", decoded == repaired)
print("\n")

## Testing Crossover
parent_1 = roulette_selection(population, packages, truck)
parent_2 = roulette_selection(population, packages, truck)

# Crossover
print("Parent 1 State   :", parent_1)
print("Parent 2 State   :", parent_2)
child = crossover(parent_1, parent_2, packages)

# Repair
child = repair_chromosome(child, packages, truck)

# State setelah repair
print("Child State      :", child)

# Decode dari chromosome ke state
child_state = decode_state(child, packages)
print("Child Valid:", state_valid(child_state, packages, truck))
print("Child Fitness:", fitness(child, packages, truck))
print("\n")

## Testing Mutation
# Menguji mutation
chromosome = encode_state(gen_initial_state(packages, truck), packages)

for i in range(100):
    mutated = mutation(chromosome, packages, truck)

    # Apakah panjang chromosome tidak berubah
    assert len(mutated) == len(chromosome) # https://www.geeksforgeeks.org/python/python-assert-keyword/

    # Decode hasil mutasi
    mutated_state = decode_state(mutated, packages)

    # Memperbaiki hasil mutation
    repaired = repair_chromosome(mutated, packages, truck)
    repaired_state = decode_state(repaired, packages)

    # Setelah repair harus valid
    assert state_valid(repaired_state, packages, truck) # https://www.geeksforgeeks.org/python/python-assert-keyword/

print("All mutation tests passed!")