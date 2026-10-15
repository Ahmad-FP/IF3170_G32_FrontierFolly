# Cek apakah tidak ada paket yang keluar dari area truck
def check_bounds(state, packages, truck):
    truck_dimensions = truck["dimensions"]

    for package_id, placement in state.items(): # https://www.geeksforgeeks.org/python/python-accessing-key-value-in-dictionary/
        position = placement["position"] # Posisi paket

        if position is None:
            continue

        orientation = placement["orientation"] # Orientasi paket
        dimensions = packages[package_id]["dimensions"] # Dimensi paket (w, l, h)

        rotate_dimensions = [dimensions[i] for i in orientation] # Dimensi yang sudah disesuaikan dengan orientasi nya

        for i in range(3):
            # Jika keluar dari bound
            if position[i] < 0:
                return False

            if position[i] + rotate_dimensions[i] > truck_dimensions[i]:
                return False

    return True

# Cek apakah tidak ada paket yang saling bertabrakan
def check_collision(state, packages):
    list_state_id = list(state.keys()) # Semua list key dari state
    state_len = len(state)
    for i in range(state_len): # https://www.geeksforgeeks.org/python/get-length-of-dictionary-in-python/
        package_1 = list_state_id[i]
        pos_1 = state[package_1]["position"]
        if pos_1 is None:
            continue
        for j in range(i+1, state_len):
            package_2 = list_state_id[j]
            pos_2 = state[package_2]["position"]
            if pos_2 is None:
                continue

            # Dimensi paket
            dims_1 = packages[package_1]["dimensions"]
            dims_2 = packages[package_2]["dimensions"]

            # Orientasi paket
            ori_1 = state[package_1]["orientation"]
            ori_2 = state[package_2]["orientation"]

            # Dimensi setelah rotasi
            rotate_dims_1 = [dims_1[k] for k in ori_1]
            rotate_dims_2 = [dims_2[k] for k in ori_2]

            # Collision di inisialisasi True
            collision = True

            # Melakukan pengecekan apakah ada collision pada ruang 3 dimensi ini
            for k in range(3):
                if ((pos_1[k] + rotate_dims_1[k] <= pos_2[k]) # Jika posisi akhir package 1 (perspektif arah 3 sisi) berada sebelum atau tepat dari posisi awal package 2
                    or
                    (pos_2[k] + rotate_dims_2[k] <= pos_1[k])): # Jika posisi akhir package 2 (perspektif arah 3 sisi) berada sebelum atau tepat dari posisi awal package 1
                    collision = False
                    break

            if collision:
                return False

    return True

# Cek apakah total berat pada paket tidak melebihi batas yang mampu ditampung truck
def check_weight(state, packages, truck):
    total_weight = 0
    for package_id, placement in state.items():
        if placement["position"] is not None: # Jika paket ada di truk
            total_weight += packages[package_id]["weight"]
    
    if total_weight > truck["max_capacity"]: # Apakah berat melebihi batas maksimumnya
        return False

    return True

# Cek apakah ada kontak dari package a (penopang) dan package b (yang ditopang)
def contact(pos_a, pos_b, rotate_dims_a, rotate_dims_b):
    # Apakah permukaan atas package a menyentuh permukaan bawah package b
    z_contact = (pos_a[2] + rotate_dims_a[2] == pos_b[2])

    # Apakah kedua paket beririsan di sumbu x
    x_contact = (
        (pos_a[0] < (pos_b[0] + rotate_dims_b[0])) and
        (pos_b[0] < (pos_a[0] + rotate_dims_a[0])) 
    )

    # Apakah kedua paket beririsan di sumbu x
    y_contact = (
        (pos_a[1] < (pos_b[1] + rotate_dims_b[1])) and
        (pos_b[1] < (pos_a[1] + rotate_dims_a[1])) 
    )

    # Apakah ada contact
    return z_contact and x_contact and y_contact

# Cek apakah tidak ada package yang melayang
def check_support(state, packages):
    list_state_id = list(state.keys()) # Semua list key dari state
    state_len = len(state)
    for i in range(state_len): # https://www.geeksforgeeks.org/python/get-length-of-dictionary-in-python/
        package_1 = list_state_id[i]
        pos_1 = state[package_1]["position"]
        if (pos_1 is None) or (pos_1[2] == 0): # check apakah package 1 tidak di dalam truk atau berada di lantai truk
            continue

        # Dimensi paket
        dims_1 = packages[package_1]["dimensions"]

        # Orientasi paket
        ori_1 = state[package_1]["orientation"]

        # Dimensi setelah rotasi
        rotate_dims_1 = [dims_1[k] for k in ori_1]

        supported = False
        for j in range(state_len):
            package_2 = list_state_id[j]
            pos_2 = state[package_2]["position"]
            if (i == j) or (pos_2 is None): # Jika package 1 dan 2 adalah sama atau package 2 tidak ada di dalam truk
                continue

            # Dimensi paket
            dims_2 = packages[package_2]["dimensions"]

            # Orientasi paket
            ori_2 = state[package_2]["orientation"]

            # Dimensi setelah rotasi
            rotate_dims_2 = [dims_2[k] for k in ori_2]

            if contact(pos_2, pos_1, rotate_dims_2, rotate_dims_1):
                supported = True
                break

        if not supported:
            return False

    return True

# Cek apakah tidak ada kontak antara fragile (yang dibawah) dengan package lain (yang diatas)
def check_fragile(state, packages):
    list_state_id = list(state.keys()) # Semua list key dari state
    state_len = len(state)
    for i in range(state_len): # https://www.geeksforgeeks.org/python/get-length-of-dictionary-in-python/
        package_1 = list_state_id[i]
        pos_1 = state[package_1]["position"]
        if (pos_1 is None) or (not packages[package_1]["is_fragile"]): # check apakah package 1 tidak di dalam truk atau bukan fragile (karena sebagai penopang)
            continue

        # Dimensi paket
        dims_1 = packages[package_1]["dimensions"]

        # Orientasi paket
        ori_1 = state[package_1]["orientation"]

        # Dimensi setelah rotasi
        rotate_dims_1 = [dims_1[k] for k in ori_1]

        for j in range(state_len):
            package_2 = list_state_id[j]
            pos_2 = state[package_2]["position"]
            if (i == j) or (pos_2 is None): # Jika package 1 dan 2 adalah sama atau package 2 tidak ada di dalam truk
                continue

            # Dimensi paket
            dims_2 = packages[package_2]["dimensions"]

            # Orientasi paket
            ori_2 = state[package_2]["orientation"]

            # Dimensi setelah rotasi
            rotate_dims_2 = [dims_2[k] for k in ori_2]

            # Jika ada kontak antara fragile (yang dibawah) dengan package lain (yang diatas) maka False
            if contact(pos_1, pos_2, rotate_dims_1, rotate_dims_2):
                return False

    return True

# Check apakah orientasi valid (element mengandung 0, 1, dan 2 tepat satu kali)
def check_orientation(state):
    for _, placement in state.items():
        if sorted(placement["orientation"]) != [0, 1, 2]:
            return False

    return True

# Apakah state aman dari constraint
def state_valid(state, packages, truck):
    return (check_orientation(state) # Orientasi paket valid
            and check_bounds(state, packages, truck) # Aman dari out of bounds
            and check_collision(state, packages) # Aman dari collision
            and check_weight(state, packages, truck) # Berat tidak melebihi maksimum
            and check_support(state, packages) # Aman dari package melayang
            and check_fragile(state, packages)) # Paket mudah pecah dilarang menjadi base
