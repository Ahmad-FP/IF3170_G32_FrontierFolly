import sys
import random
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from constraint import state_valid
from initial_state import gen_initial_state, possible_height

ORIENTATIONS = [
    (0, 1, 2),
    (0, 2, 1),
    (1, 0, 2),
    (1, 2, 0),
    (2, 0, 1),
    (2, 1, 0)
]

# Mengubah state menjadi array satu dimensi
def encode_state(state, packages):
    chromosome = []

    for package_id in packages:
        placement = state[package_id]
        position = placement["position"]
        orientation = placement["orientation"]

        ori_id = ORIENTATIONS.index(orientation)
        if position is None: 
            chromosome.extend([0, 0, 0, 0, ori_id])

        else:
            chromosome.extend([
                1,
                position[0],
                position[1],
                position[2],
                ori_id]
            )

    return chromosome

# Decode dari chromosome 1 dimensi ke state dictionary
def decode_state(chromosome, packages):
    state = {}

    for i, package_id in enumerate(packages):
        a, x, y, z, ori_id = chromosome[(i*5):(i*5+5)]

        if a == 0: 
            position = None
        elif a == 1: 
            position = (x, y, z)
        else: 
            raise ValueError("Nilai kondisi posisi tidak boleh lebih dari 1") 
        orientation = ORIENTATIONS[ori_id]
        state[package_id] = {
            "position" : position,
            "orientation" : orientation
        }

    return state

# Inisialisasi populasi
def gen_initial_pop(packages, truck, pop_size):
    population = []

    for _ in range(pop_size):
        state = gen_initial_state(packages, truck)
        chromosome = encode_state(state, packages)

        population.append(chromosome)

    inital_chromosome_random = random.choice(population)

    return inital_chromosome_random, population

# Menghitung fitness suatu chromosome
def fitness(chromosome, packages, truck):
    state = decode_state(chromosome, packages)

    if not state_valid(state, packages, truck):
        return float("-inf") 

    total_value = 0

    for package_id, placement in state.items(): 
        if placement["position"] is not None:
            total_value += packages[package_id]["value"]

    return total_value

# Memilih parent dengan sistem roulette
def roulette_selection(population, packages, truck):
    fitness_value = [
        fitness(chromosome, packages, truck)
        for chromosome in population
    ]

    total_fitness = sum(fitness_value)

    if total_fitness == 0:
        return random.choice(population).copy()

    random_number = random.random() * 100

    cum_probability = 0

    for i in range(len(population)):
        # Probability individu
        probability = (fitness_value[i] / total_fitness) * 100

        cum_probability += probability

        # Memilih parent
        if random_number < cum_probability:
            return population[i].copy()

    return population[-1].copy()

# Melakukan perbaikan pada state
def repair_state(state, packages, truck):
    repaired = {}

    # Inisialisasi semua paket
    for package_id in packages:
        repaired[package_id] = {
            "position" : None,
            "orientation" : state[package_id]["orientation"]
        }

    list_package_id = [
        package_id for package_id in packages
        if state[package_id]["position"] is not None
    ]
    
    list_package_id.sort(key=lambda package_id: (
        state[package_id]["position"][2],
        -packages[package_id]["value"]))

    truck_dims = truck["dimensions"]

    for package_id in list_package_id:

        original_position = state[package_id]["position"]
        orientation = state[package_id]["orientation"]
        dimensions = packages[package_id]["dimensions"]
        rotate_dims = [dimensions[i] for i in orientation]

        repaired[package_id]["position"] = original_position # Mencoba posisi awal

        if state_valid(repaired, packages, truck):
            continue

        repaired[package_id]["position"] = None 

        if any(rotate_dims[k] > truck_dims[k] for k in range(3)):
            continue

        # Mengambil ketinggian possible
        heights = [
            h for h in possible_height(repaired, packages)
            if h + rotate_dims[2] <= truck_dims[2]
        ]

        # Mengambil X dan Y pilihan
        x_choices = {0, original_position[0]}
        y_choices = {0, original_position[1]}

        # Menambahkan pilihan berdasarkan posisi paket lain
        for other_id in packages:
            other_position = repaired[other_id]["position"] 
            if other_position is None: 
                continue

            other_orientation = repaired[other_id]["orientation"] 
            other_dimensions = packages[other_id]["dimensions"] 
            other_rotate_dims = [
                other_dimensions[i] for i in other_orientation
            ]

            ox, oy, oz = other_position 
            ow, ol, oh = other_rotate_dims 
            x_choices.update([
                ox, 
                ox + ow, 
                ox - rotate_dims[0], 
                ox + ow - rotate_dims[0] 
            ])
            y_choices.update([
                oy, 
                oy + ol, 
                oy - rotate_dims[1], 
                oy + ol - rotate_dims[1] 
            ])

        # Jika pilihan posisi masih di dalam truk
        x_choices = [
            x for x in x_choices
            if 0 <= x <= truck_dims[0] - rotate_dims[0]
        ]

        y_choices = [
            y for y in y_choices
            if 0 <= y <= truck_dims[1] - rotate_dims[1]
        ]

        # pilihan yang sudah difilter X dan Y
        positions_xy = [
            (x, y)
            for x in x_choices
            for y in y_choices
        ]

        random.shuffle(positions_xy)

        # Cari posisi valid
        found = False
        for z in sorted(heights):
            for x, y in positions_xy:

                repaired[package_id]["position"] = (x, y, z) # Posisi di-repair

                if state_valid(repaired, packages, truck): # Jika state valid
                    found = True
                    break
            if found:
                break
        if not found:
            repaired[package_id]["position"] = None
    return repaired

def repair_chromosome(chromosome, packages, truck):
    state = decode_state(chromosome, packages)
    repaired_state = repair_state(state, packages, truck)
    return encode_state(repaired_state, packages)

# Hitung value hilang karena repair
def raw_value(chromosome, packages):
    state = decode_state(chromosome, packages)
    total = 0

    for package_id in packages:
        if state[package_id]["position"] is not None:
            total += packages[package_id]["value"]

    return total

def crossover(parent_1, parent_2, packages):
    num_packages = len(packages)
    if (num_packages < 2):
        return parent_1.copy()
    cut_index = (random.randint(1, num_packages - 1)) * 5
    child = parent_1[:cut_index] + parent_2[cut_index:]
    return child

# Melakukan mutasi
def mutation(chromosome, packages, truck):
    mutated = chromosome.copy()

    if not packages: 
        return mutated

    package_idx = random.randint(0, len(packages) - 1)
    package_id = list(packages.keys())[package_idx]

    start = package_idx * 5
    a, x, y, z, ori_id = mutated[start:start+5]

    dimensions = packages[package_id]["dimensions"]
    truck_dims = truck["dimensions"]

    orientation = ORIENTATIONS[ori_id]
    rotate_dims = [dimensions[i] for i in orientation]

    if a == 0:
        operation = "add"
    else:
        operation = random.choice(["remove", "move", "rotate"])

    if operation == "add": 
        ori_id = random.randint(0, 5)
        orientation = ORIENTATIONS[ori_id]
        rotate_dims = [dimensions[i] for i in orientation]
        if any(rotate_dims[k] > truck_dims[k] for k in range(3)):
            return mutated

        state = decode_state(chromosome, packages)
        heights = [
            h for h in possible_height(state, packages)
            if h + rotate_dims[2] <= truck_dims[2]
        ]
        if not heights:
            return mutated

        position = (
            random.randint(0, truck_dims[0] - rotate_dims[0]),
            random.randint(0, truck_dims[1] - rotate_dims[1]),
            random.choice(heights)
        )
        mutated[start:start+5] = [
            1,
            position[0],
            position[1],
            position[2],
            ori_id
        ]

    elif operation == "remove": 
        mutated[start:start+5] = [0, 0, 0, 0, ori_id]

    elif operation == "move": 
        position = [x, y, z]

        axis = random.randint(0, 2)

        if (axis == 0) or (axis == 1):
            choices = range(truck_dims[axis] - rotate_dims[axis] + 1)
        else:
            state = decode_state(chromosome, packages)
            state[package_id]["position"] = None

            choices = [
                h for h in possible_height(state, packages)
                if h + rotate_dims[2] <= truck_dims[2]
            ]

        choices = [value for value in choices if value != position[axis]]
        if not choices:
            return mutated

        position[axis] = random.choice(choices)
        mutated[start+1:start+4] = position    

    elif operation == "rotate": 
        opt_rotate = [i for i in range(6) if i != ori_id]
        mutated[start+4] = random.choice(opt_rotate)

    return mutated

def genetic_algorithm(packages, truck, pop_size, max_iter, mutation_rate=0.1):
    
    if pop_size < 1 or max_iter < 0:
        raise ValueError("Jumlah populasi dan maksimal iterasi tidak valid")

    if not 0 <= mutation_rate <= 1:
        raise ValueError("Mutation rate tidak valid")

    initial_chromosome_random, population = gen_initial_pop(packages, truck, pop_size) 
    fitness_values = [
        fitness(chromosome, packages, truck)
        for chromosome in population
    ]
    best_idx = fitness_values.index(max(fitness_values))
    best_chromosome = population[best_idx].copy()
    best_fitness = fitness_values[best_idx]

    history_best = [best_fitness]
    history_curr_best = [best_fitness]
    history_avg = [sum(fitness_values) / pop_size]

    for _ in range(max_iter):
        new_population = [best_chromosome.copy()] 
        while len(new_population) < pop_size:

            parent_1 = roulette_selection(population, packages, truck)
            parent_2 = roulette_selection(population, packages, truck)
        
            child = crossover(parent_1, parent_2, packages) 

            value_before = raw_value(child, packages)
            child = repair_chromosome(child, packages, truck) 
            value_after = raw_value(child, packages)

            if random.random() < mutation_rate:
                child = mutation(child, packages, truck)

            child = repair_chromosome(child, packages, truck) 
            new_population.append(child) 

        population = new_population 

        fitness_values = [
            fitness(chromosome, packages, truck)
            for chromosome in population
        ]

        curr_best_idx = fitness_values.index(max(fitness_values))
        curr_best_fitness = fitness_values[curr_best_idx]

        if curr_best_fitness > best_fitness:
            best_fitness = curr_best_fitness
            best_chromosome = population[curr_best_idx].copy()

        history_best.append(best_fitness)
        history_curr_best.append(curr_best_fitness)
        history_avg.append(sum(fitness_values) / pop_size)

    return initial_chromosome_random, best_chromosome, history_best, history_curr_best, history_avg # Mengembalikan kromosom terbaik, history dari fitness terbaik, dan history dari rata-rata fitness