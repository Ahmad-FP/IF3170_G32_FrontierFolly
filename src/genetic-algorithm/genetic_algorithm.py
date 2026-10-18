import sys
import random
from pathlib import Path

# Mengambil module di luar path parent kode ini
# https://docs.python.org/3.13/tutorial/modules.html
# https://docs.python.org/3.14/library/pathlib.html
sys.path.append(str(Path(__file__).resolve().parent.parent))

from constraint import state_valid
from initial_state import gen_initial_state, possible_height

# Pola orientasi
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
        if position is None: # Jika berada di luar truck
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

        if a == 0: # Jika paket di luar truk
            position = None
        elif a == 1: # Jika paket di dalam truk
            position = (x, y, z)
        else: # Jika nilai kondisi posisi lebih dari satu
            raise ValueError("Nilai kondisi posisi tidak boleh lebih dari 1") # https://stackoverflow.com/questions/4393268/how-to-raise-a-valueerror
        
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

    # Jika state tidak valid
    if not state_valid(state, packages, truck):
        return float("-inf") # https://www.geeksforgeeks.org/python/python-infinity/

    total_value = 0

    # Menghitung total value yang di dapat dari paket di dalam truck
    for package_id, placement in state.items(): # https://www.geeksforgeeks.org/python/python-accessing-key-value-in-dictionary/
        if placement["position"] is not None:
            total_value += packages[package_id]["value"]

    return total_value

# Memilih parent dengan sistem roulette
def roulette_selection(population, packages, truck):
    # Mengambil semua nilai fitness value dari chromosome di populasi
    fitness_value = [
        fitness(chromosome, packages, truck)
        for chromosome in population
    ]

    total_fitness = sum(fitness_value)

    # Jika semua fitness bernilai nol
    if total_fitness == 0:
        return random.choice(population).copy()

    # Menghasilkan angka acak dari 0 sampai 100
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

    # Inisialisasi semua paket yang terdaftar di state itu di luar truck
    for package_id in packages:
        repaired[package_id] = {
            "position" : None,
            "orientation" : state[package_id]["orientation"]
        }

    # List id paket yang berada di dalam truck
    list_package_id = [
        package_id for package_id in packages
        if state[package_id]["position"] is not None
    ]
    
    # Sorting berdasarkan ketinggian paket dan value tertinggi
    # https://www.w3schools.com/python/ref_list_sort.asp
    # https://www.w3schools.com/python/python_lambda.asp
    list_package_id.sort(key=lambda package_id: (
        state[package_id]["position"][2],
        -packages[package_id]["value"]))

    truck_dims = truck["dimensions"]

    for package_id in list_package_id:

        # Mengambil posisi dan orientasi awal paket
        original_position = state[package_id]["position"]
        orientation = state[package_id]["orientation"]
        dimensions = packages[package_id]["dimensions"]
        rotate_dims = [dimensions[i] for i in orientation]

        repaired[package_id]["position"] = original_position # Mencoba posisi awal

        if state_valid(repaired, packages, truck):
            continue

        repaired[package_id]["position"] = None # Jika posisi awal tidak valid, dikosongkan terlebih dahulu

        # Memeriksa apakah dimensi paket muat di truk
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
            other_position = repaired[other_id]["position"] # Posisi paket lain

            if other_position is None: # Jika paket lain ini masih di luar
                continue

            other_orientation = repaired[other_id]["orientation"] # Orientasi paket lain
            other_dimensions = packages[other_id]["dimensions"] # Ukuran paket lain

            # Dimensi setelah di rotasi kan
            other_rotate_dims = [
                other_dimensions[i] for i in other_orientation
            ]

            ox, oy, oz = other_position # Pemecahan posisi paket lain
            ow, ol, oh = other_rotate_dims # Pemecahan dimensi paket lain

            x_choices.update([
                ox, # Posisi kiri paket lain sejajar dengan paket saat ini
                ox + ow, # Posisi kanan paket lain bersebelahan dengan posisi kiri paket saat ini
                ox - rotate_dims[0], # Posisi kiri paket lain bersebelahan dengan posisi kanan paket saat ini
                ox + ow - rotate_dims[0] # Posisi kanan paket lain sejajar dengan paket saat ini
            ])

            y_choices.update([
                oy, # Posisi belakang paket lain sejajar dengan paket saat ini
                oy + ol, # Posisi depan paket lain bersebelahan dengan posisi belakang paket saat ini
                oy - rotate_dims[1], # Posisi belakang paket lain bersebelahan dengan posisi depan paket saat ini
                oy + ol - rotate_dims[1] # Posisi depan paket lain sejajar dengan paket saat ini
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

        # Membentuk kombinasi pilihan yang sudah difilter X dan Y
        positions_xy = [
            (x, y)
            for x in x_choices
            for y in y_choices
        ]

        random.shuffle(positions_xy)

        # Mencari posisi baru yang valid
        found = False

        for z in sorted(heights):
            for x, y in positions_xy:

                repaired[package_id]["position"] = (x, y, z) # Posisi di-repair

                if state_valid(repaired, packages, truck): # Jika state valid
                    found = True
                    break

            if found:
                break

        # Jika tidak ditemukan posisi valid, keluarkan paket
        if not found:
            repaired[package_id]["position"] = None

    return repaired

# Melakukan repair kromosom
def repair_chromosome(chromosome, packages, truck):
    
    # Mengubah kromosom menjadi state
    state = decode_state(chromosome, packages)

    # Merepair state
    repaired_state = repair_state(state, packages, truck)

    return encode_state(repaired_state, packages)

# Menghitung value yang hilang saat di repair
def raw_value(chromosome, packages):
    state = decode_state(chromosome, packages)
    total = 0

    for package_id in packages:
        if state[package_id]["position"] is not None:
            total += packages[package_id]["value"]

    return total

# Melakukan crossover
def crossover(parent_1, parent_2, packages):
    num_packages = len(packages)

    # Jika paket kurang dari dua, crossover tidak bisa dilakukan
    if (num_packages < 2):
        return parent_1.copy()

    # Randomize titik potong crossover
    cut_index = (random.randint(1, num_packages - 1)) * 5

    # Child hasil crossover
    child = parent_1[:cut_index] + parent_2[cut_index:]

    return child

# Melakukan mutasi
def mutation(chromosome, packages, truck):
    mutated = chromosome.copy()

    if not packages: # Jika packages kosong
        return mutated

    # Memilih index secara acak
    package_idx = random.randint(0, len(packages) - 1)
    package_id = list(packages.keys())[package_idx]

    start = package_idx * 5
    a, x, y, z, ori_id = mutated[start:start+5]

    # Mengambil dimensi paket dan truk
    dimensions = packages[package_id]["dimensions"]
    truck_dims = truck["dimensions"]

    orientation = ORIENTATIONS[ori_id]
    rotate_dims = [dimensions[i] for i in orientation]

    # Menentukan jenis operasi
    if a == 0:
        operation = "add"
    else:
        operation = random.choice(["remove", "move", "rotate"])

    if operation == "add": # Kondisi operasi ketika menambahkan paket ke truk
        # Mengacak orientasi
        ori_id = random.randint(0, 5)
        orientation = ORIENTATIONS[ori_id]
        rotate_dims = [dimensions[i] for i in orientation]

        # Memeriksa apakah dimensi paket lebih besar daripada dimensi truk
        if any(rotate_dims[k] > truck_dims[k] for k in range(3)):
            return mutated

        # Mengambil hanya pada ketinggian yang mungkin
        state = decode_state(chromosome, packages)

        heights = [
            h for h in possible_height(state, packages)
            if h + rotate_dims[2] <= truck_dims[2]
        ]

        if not heights:
            return mutated

        # Mengacak posisi paket
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

    elif operation == "remove": # Jika operasi yang dilakukan adalah mengeluarkan paket dari truck
        mutated[start:start+5] = [0, 0, 0, 0, ori_id]

    elif operation == "move": # Jika operasi yang dilakukan adalah memindahkan posisi paket di truck
        position = [x, y, z]

        # Memilih axis manakah yang diubah
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

        # Mengubah satu posisi koordinat
        position[axis] = random.choice(choices)
        mutated[start+1:start+4] = position    

    elif operation == "rotate": # Jika operasi yang dilakukan adalah melakukan rotasi paket dari truck
        opt_rotate = [i for i in range(6) if i != ori_id]
        mutated[start+4] = random.choice(opt_rotate)

    return mutated

# Melakukan genetic algorithm
def genetic_algorithm(packages, truck, pop_size, max_iter, mutation_rate=0.1):
    
    if pop_size < 1 or max_iter < 0:
        raise ValueError("Jumlah populasi dan maksimal iterasi tidak valid")

    if not 0 <= mutation_rate <= 1:
        raise ValueError("Mutation rate tidak valid")

    initial_chromosome_random, population = gen_initial_pop(packages, truck, pop_size) # Membentuk populasi awal

    # Menghitung nilai fitness dari populasi awal
    fitness_values = [
        fitness(chromosome, packages, truck)
        for chromosome in population
    ]

    # Menyimpan individu terbaik
    best_idx = fitness_values.index(max(fitness_values))
    best_chromosome = population[best_idx].copy()
    best_fitness = fitness_values[best_idx]

    # History terbaik tiap iterasi
    history_best = [best_fitness]
    history_curr_best = [best_fitness]
    history_avg = [sum(fitness_values) / pop_size]

    # Pengulangan proses evolusi
    for _ in range(max_iter):
        new_population = [best_chromosome.copy()] # Inisialisasi awal
        while len(new_population) < pop_size:

            # Memilih dua parent
            parent_1 = roulette_selection(population, packages, truck)
            parent_2 = roulette_selection(population, packages, truck)
        
            child = crossover(parent_1, parent_2, packages) # Crossover

            value_before = raw_value(child, packages)
            child = repair_chromosome(child, packages, truck) # Perbaiki jika ada child yang tidak valid
            value_after = raw_value(child, packages)

            # Mutasi jika probabilitas terpenuhi
            if random.random() < mutation_rate:
                child = mutation(child, packages, truck)

            child = repair_chromosome(child, packages, truck) # Perbaiki jika mutasi membuat tidak valid

            new_population.append(child) # Memasukkan child ke populasi baru

        population = new_population # Mengganti populasi ke yang baru

        # Menghitung fitness generasi baru
        fitness_values = [
            fitness(chromosome, packages, truck)
            for chromosome in population
        ]

        # Memperbarui solusi terbaik saat ini
        curr_best_idx = fitness_values.index(max(fitness_values))
        curr_best_fitness = fitness_values[curr_best_idx]

        if curr_best_fitness > best_fitness:
            best_fitness = curr_best_fitness
            best_chromosome = population[curr_best_idx].copy()

        # Menyimpan history fitness
        history_best.append(best_fitness)
        history_curr_best.append(curr_best_fitness)
        history_avg.append(sum(fitness_values) / pop_size)

    return initial_chromosome_random, best_chromosome, history_best, history_curr_best, history_avg # Mengembalikan kromosom terbaik, history dari fitness terbaik, dan history dari rata-rata fitness