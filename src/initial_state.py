import random
from constraint import state_valid

# Mendapatkan ketinggian yang mungkin bisa ditempati
def possible_height(state, packages):
    height = [0]

    for package_id, placement in state.items():
        pos = placement["position"]

        if ((pos is None) or (packages[package_id]["is_fragile"])): continue

        dimensions = packages[package_id]["dimensions"]
        orientation = placement["orientation"]
        rotate_dims = [dimensions[k] for k in orientation]

        top_z = pos[2] + rotate_dims[2] 
        height.append(top_z)

    return list(set(height))    

# Generate inisialisasi state secara random
def gen_initial_state(packages, truck):
    state = {}

    for package_id in packages:
        state[package_id] = {
            "position" : None,
            "orientation" : (0, 1, 2)
        }

    list_package_id = list(packages.keys())
    random.shuffle(list_package_id) 
    num_packages = random.randint(1, len(list_package_id))

    truck_dims = truck["dimensions"]

    for package_id in list_package_id[:num_packages]:
        dimensions = packages[package_id]["dimensions"]

        for _ in range(50): 
            orientation = tuple(random.sample([0, 1, 2], k=3)) 
            rotate_dims = [dimensions[i] for i in orientation]

            if any(rotate_dims[k] > truck_dims[k] for k in range(3)): continue

            heights = [
                z for z in possible_height(state, packages)
                if z + rotate_dims[2] <= truck_dims[2]
            ]

            if not heights:
                continue

            position = (
                random.randint(0, truck_dims[0] - rotate_dims[0]),  
                random.randint(0, truck_dims[1] - rotate_dims[1]),  
                random.choice(heights)                              
            )

            state[package_id] = {
                "position": position,
                "orientation": orientation
            }

            if state_valid(state, packages, truck):
                break

            state[package_id]["position"] = None

    return state