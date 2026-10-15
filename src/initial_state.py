import random
from constraint import state_valid

# Mendapatkan ketinggian yang mungkin bisa ditempati
def possible_height(state, packages):
    height = [0]

    for package_id, placement in state.items():
        pos = placement["position"]

        if ((pos is None) or (packages[package_id]["is_fragile"])): # Jika paket berada di luar atau paket base nya adalah fragile
            continue

        dimensions = packages[package_id]["dimensions"]
        orientation = placement["orientation"]
        rotate_dims = [dimensions[k] for k in orientation]

        top_z = pos[2] + rotate_dims[2] # Ketinggian paket
        height.append(top_z)

    return list(set(height))    

# Generate inisialisasi state secara random
def gen_initial_state(packages, truck):
    # Inisialisasi state
    state = {}

    # State di inisialisasi di luar truck
    for package_id in packages:
        state[package_id] = {
            "position" : None,
            "orientation" : (0, 1, 2)
        }

    # Mengacak package_id
    list_package_id = list(packages.keys())
    random.shuffle(list_package_id) # https://www.w3schools.com/python/ref_random_shuffle.asp

    # Randomize jumlah paket yang masuk ke truk
    num_packages = random.randint(1, len(list_package_id))

    truck_dims = truck["dimensions"]

    for package_id in list_package_id[:num_packages]:
        dimensions = packages[package_id]["dimensions"]

        for _ in range(50): # 50 kali pengulangan jika gagal maka paket tidak dimasukkan
            # https://www.w3schools.com/python/ref_random_sample.asp
            orientation = tuple(random.sample([0, 1, 2], k=3)) # Mengacak orientasi
            rotate_dims = [dimensions[i] for i in orientation]

            # https://www.w3schools.com/python/ref_func_any.asp
            if any(rotate_dims[k] > truck_dims[k] for k in range(3)): # Jika ukuran paket lebih besar dari dimensi truck nya
                continue

            # Ambil ketinggian yang tidak melebihi batas dimensi truck
            heights = [
                z for z in possible_height(state, packages)
                if z + rotate_dims[2] <= truck_dims[2]
            ]

            # Jika possible ketinggian tidak ditemukan
            if not heights:
                continue

            # Mengacak koordinat x, y, dan z
            position = (
                random.randint(0, truck_dims[0] - rotate_dims[0]),  # X
                random.randint(0, truck_dims[1] - rotate_dims[1]),  # Y
                random.choice(heights)                              # Z
            )

            state[package_id] = {
                "position": position,
                "orientation": orientation
            }

            # Jika seluruh constraint valid
            if state_valid(state, packages, truck):
                break

            # Jika tidak valid, paket dikembalikan ke luar
            state[package_id]["position"] = None

    return state