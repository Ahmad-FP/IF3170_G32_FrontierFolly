import sys
import time
import json
import random
import itertools
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from constraint import state_valid
from initial_state import gen_initial_state, possible_height
from visual import plotState, plotValues

ORIENTATIONS = [
    (0, 1, 2),
    (0, 2, 1),
    (1, 0, 2),
    (1, 2, 0),
    (2, 0, 1),
    (2, 1, 0)
]


def packageScore(package, objective="value"):
    if objective == "value":
        return package["value"]
    if objective == "urgency":
        # Bonus
        return package["value"] / package["eta"]
    raise ValueError(f"Objective '{objective}' tidak dikenali")


def stateScore(state, packages, objective="value"):
    return sum(
        packageScore(packages[k], objective)
        for k, placement in state.items()
        if placement["position"] is not None
    )


def rawValue(state, packages):
    return sum(
        packages[k]["value"]
        for k, placement in state.items()
        if placement["position"] is not None
    )


def fotokopi(state):
    return {k: dict(placement) for k, placement in state.items()}


def rotatedDims(package_id, orientation, packages):
    dimensions = packages[package_id]["dimensions"]
    return [dimensions[i] for i in orientation]


def insideBoxes(state, packages):
    boxes = []
    for package_id, placement in state.items():
        position = placement["position"]
        if position is None:
            continue
        boxes.append((position, rotatedDims(package_id, placement["orientation"], packages),
                      packages[package_id]["is_fragile"]))
    return boxes


def totalWeight(state, packages):
    return sum(
        packages[k]["weight"]
        for k, placement in state.items()
        if placement["position"] is not None
    )


def overlap1D(a, size_a, b, size_b):
    return a < b + size_b and b < a + size_a

# Deterministik
def axisCandidates(boxes, axis, size, limit):
    values = {0, limit - size}
    for position, dims, _ in boxes:
        near = position[axis]
        far = near + dims[axis]
        values.update((near, far, near - size, far - size))
    return sorted(v for v in values if 0 <= v <= limit - size)


def findFeasiblePlacement(state, package_id, packages, truck, exclude=None):
    W, L, H = truck["dimensions"]
    fragile = packages[package_id]["is_fragile"]

    if totalWeight(state, packages) + packages[package_id]["weight"] > truck["max_capacity"]:
        return None

    boxes = insideBoxes(state, packages)
    heights = possible_height(state, packages)

    for orientation in ORIENTATIONS:
        w, l, h = rotatedDims(package_id, orientation, packages)
        if w > W or l > L or h > H:
            continue

        xs = axisCandidates(boxes, 0, w, W)
        ys = axisCandidates(boxes, 1, l, L)
        zs = sorted(z for z in heights if z + h <= H)
        if not xs or not ys or not zs:
            continue

        for z in zs:
            # Overlap z
            rel = [
                (p[0], p[1], p[2], d[0], d[1], d[2], f)
                for p, d, f in boxes
                if (p[2] < z + h and z < p[2] + d[2]) or p[2] + d[2] == z or p[2] == z + h
            ]

            for x in xs:
                for y in ys:
                    if exclude is not None and (x, y, z) == exclude:
                        continue

                    valid = True
                    supported = z == 0
                    for kx, ky, kz, kw, kl, kh, k_fragile in rel:
                        if not (overlap1D(x, w, kx, kw) and overlap1D(y, l, ky, kl)):
                            continue
                        if kz < z + h and z < kz + kh:
                            valid = False
                            break
                        if kz + kh == z:
                            if k_fragile:  # fragile tidak boleh menjadi penopang
                                valid = False
                                break
                            supported = True
                        elif kz == z + h and fragile:
                            valid = False
                            break

                    if valid and supported:
                        return (x, y, z), orientation

    return None


def geometryKey(state, packages):
    inside = [
        (package_id, placement["position"],
         tuple(rotatedDims(package_id, placement["orientation"], packages)))
        for package_id, placement in state.items()
        if placement["position"] is not None
    ]
    return tuple(sorted(inside))


def trySwapPositions(state, id_a, id_b, packages, truck, orientation_combos=12):
    pos_a = state[id_a]["position"]
    pos_b = state[id_b]["position"]
    if pos_a is None and pos_b is None:
        return None

    ori_a = state[id_a]["orientation"]
    ori_b = state[id_b]["orientation"]

    if pos_b is None:
        combos = [(ori_a, o) for o in ORIENTATIONS if o != ori_b]
        combos += [(o, ori_b) for o in ORIENTATIONS if o != ori_a]
    else:
        combos = [(o, ori_b) for o in ORIENTATIONS if o != ori_a]
        combos += [(ori_a, o) for o in ORIENTATIONS if o != ori_b]
    combos = [(ori_a, ori_b)] + combos
    combos += [(o1, o2) for o1 in ORIENTATIONS for o2 in ORIENTATIONS
               if o1 != ori_a and o2 != ori_b]

    for new_ori_a, new_ori_b in combos[:orientation_combos]:
        new = fotokopi(state)
        new[id_a]["position"], new[id_a]["orientation"] = pos_b, new_ori_a
        new[id_b]["position"], new[id_b]["orientation"] = pos_a, new_ori_b
        if state_valid(new, packages, truck):
            return new
    return None

# move
def bestImprovingMove(state, packages, truck, objective="value"):
    scores = {k: packageScore(packages[k], objective) for k in packages}
    inside = [k for k, placement in state.items() if placement["position"] is not None]
    outside = [k for k, placement in state.items() if placement["position"] is None]

    best = None

    # highest delta
    for j in sorted(outside, key=lambda k: (-scores[k], k)):
        if scores[j] <= 0:
            break
        placement = findFeasiblePlacement(state, j, packages, truck)
        if placement is None:
            continue
        position, orientation = placement
        new = fotokopi(state)
        new[j] = {"position": position, "orientation": orientation}
        if state_valid(new, packages, truck):
            best = (scores[j], new, f"tambah paket {j} ke {position} orientasi {orientation}")
            break

    pairs = [
        (scores[j] - scores[i], i, j)
        for i in inside
        for j in outside
        if scores[j] > scores[i]
    ]
    pairs.sort(key=lambda pair: (-pair[0], pair[1], pair[2]))

    for delta, i, j in pairs:
        if best is not None and delta <= best[0]:
            break
        slot = state[i]["position"]
        reduced = fotokopi(state)
        reduced[i] = {"position": None, "orientation": state[i]["orientation"]}
        for orientation in ORIENTATIONS:
            new = fotokopi(reduced)
            new[j] = {"position": slot, "orientation": orientation}
            if state_valid(new, packages, truck):
                best = (delta, new, f"swap paket dalam {i} dengan paket luar {j}")
                break

    return best


def findSidewaysMove(state, packages, truck, objective="value", prev_key=None):
    scores = {k: packageScore(packages[k], objective) for k in packages}
    inside = sorted(k for k, placement in state.items() if placement["position"] is not None)
    outside = sorted(k for k, placement in state.items() if placement["position"] is None)
    current_key = geometryKey(state, packages)

    def acceptable(candidate):
        if candidate is None:
            return False
        key = geometryKey(candidate, packages)
        return key != current_key and (prev_key is None or key != prev_key)

    for a, b in itertools.combinations(inside, 2):
        candidate = trySwapPositions(state, a, b, packages, truck)
        if acceptable(candidate):
            return candidate, f"swap posisi {a} <-> {b}"

    for i in inside:
        for j in outside:
            if scores[j] != scores[i]:
                continue
            candidate = trySwapPositions(state, i, j, packages, truck)
            if acceptable(candidate):
                return candidate, f"swap posisi {i} <-> {j}"

    for k in inside:
        current_ori = state[k]["orientation"]
        current_dims = tuple(rotatedDims(k, current_ori, packages))
        for orientation in ORIENTATIONS:
            if orientation == current_ori:
                continue
            if tuple(rotatedDims(k, orientation, packages)) == current_dims:
                continue  # rotasi yang tidak mengubah dimensi efektif
            candidate = fotokopi(state)
            candidate[k] = {"position": state[k]["position"], "orientation": orientation}
            if state_valid(candidate, packages, truck) and acceptable(candidate):
                return candidate, f"rotasi paket {k} ke orientasi {orientation}"

    for k in inside:
        current_pos = state[k]["position"]
        reduced = fotokopi(state)
        reduced[k] = {"position": None, "orientation": state[k]["orientation"]}
        placement = findFeasiblePlacement(reduced, k, packages, truck, exclude=current_pos)
        if placement is None:
            continue
        position, orientation = placement
        candidate = fotokopi(reduced)
        candidate[k] = {"position": position, "orientation": orientation}
        if state_valid(candidate, packages, truck) and acceptable(candidate):
            return candidate, f"pindah paket {k} ke {position}"

    return None, None


def randomNeighbor(state, packages, truck, t=50):
    W, L, H = truck["dimensions"]
    inside = [k for k, placement in state.items() if placement["position"] is not None]
    outside = [k for k, placement in state.items() if placement["position"] is None]
    if not inside and not outside:
        return None

    move = random.choice(["swap", "add", "remove", "move", "rotate"])

    if move == "swap":
        if len(packages) < 2:
            return None
        a, b = random.sample(list(packages), 2)
        if state[a]["position"] is None and state[b]["position"] is None:
            return None
        new = fotokopi(state)
        new[a]["position"], new[b]["position"] = state[b]["position"], state[a]["position"]
        if state_valid(new, packages, truck):
            return new
        return None

    if move == "add" and outside:
        j = random.choice(outside)
        for _ in range(t):
            orientation = random.choice(ORIENTATIONS)
            w, l, h = rotatedDims(j, orientation, packages)
            if w > W or l > L or h > H:
                continue
            heights = [z for z in possible_height(state, packages) if z + h <= H]
            if not heights:
                continue
            position = (random.randint(0, W - w), random.randint(0, L - l), random.choice(heights))
            new = fotokopi(state)
            new[j] = {"position": position, "orientation": orientation}
            if state_valid(new, packages, truck):
                return new
        return None

    if move == "remove" and inside:
        i = random.choice(inside)
        new = fotokopi(state)
        new[i]["position"] = None
        if state_valid(new, packages, truck):
            return new
        return None

    if move == "move" and inside:
        j = random.choice(inside)
        orientation = state[j]["orientation"]
        w, l, h = rotatedDims(j, orientation, packages)
        reduced = fotokopi(state)
        reduced[j]["position"] = None
        for _ in range(t):
            heights = [z for z in possible_height(reduced, packages) if z + h <= H]
            if not heights:
                continue
            position = (random.randint(0, W - w), random.randint(0, L - l), random.choice(heights))
            if position == state[j]["position"]:
                continue
            new = fotokopi(reduced)
            new[j] = {"position": position, "orientation": orientation}
            if state_valid(new, packages, truck):
                return new
        return None

    if move == "rotate" and inside:
        j = random.choice(inside)
        current_ori = state[j]["orientation"]
        others = [o for o in ORIENTATIONS if o != current_ori]
        random.shuffle(others)
        for orientation in others:
            new = fotokopi(state)
            new[j]["orientation"] = orientation
            if state_valid(new, packages, truck):
                return new
        return None

    return None


def steepestAscent(packages, truck, objective="value", maxIter=2000, seed=None):
    if seed is not None:
        random.seed(seed)

    start = time.perf_counter()
    initial = gen_initial_state(packages, truck)
    current = fotokopi(initial)
    current_value = stateScore(current, packages, objective)

    values = [current_value]
    iterations = 0

    while iterations < maxIter:
        best = bestImprovingMove(current, packages, truck, objective)
        if best is None:
            break
        _, new_state, _ = best
        current = new_state
        current_value = stateScore(current, packages, objective)
        values.append(current_value)
        iterations += 1

    return {
        "variant": "steepest_ascent",
        "objective": objective,
        "seed": seed,
        "initial": initial,
        "final": current,
        "finalVal": current_value,
        "realValue": rawValue(current, packages),
        "duration": time.perf_counter() - start,
        "valuesOT": values,
        "iterations": iterations,
        "max_iter": maxIter
    }


def stochastic(packages, truck, objective="value", trials=100, maxIter=2000, seed=None):
    if seed is not None:
        random.seed(seed)

    start = time.perf_counter()
    initial = gen_initial_state(packages, truck)
    current = fotokopi(initial)
    current_value = stateScore(current, packages, objective)

    values = [current_value]
    iterations = 0
    total_attempts = 0

    while iterations < maxIter:
        improved = False
        for _ in range(trials):
            total_attempts += 1
            new_state = randomNeighbor(current, packages, truck)
            if new_state is None:
                continue
            new_value = stateScore(new_state, packages, objective)
            if new_value > current_value:
                current, current_value = new_state, new_value
                values.append(current_value)
                iterations += 1
                improved = True
                break
        if not improved:
            break

    return {
        "variant": "stochastic",
        "objective": objective,
        "seed": seed,
        "initial": initial,
        "final": current,
        "finalVal": current_value,
        "realValue": rawValue(current, packages),
        "duration": time.perf_counter() - start,
        "valuesOT": values,
        "iterations": iterations,
        "max_iter": maxIter,
        "trials_per_iteration": trials,
        "total_attempts": total_attempts
    }


def sidewaysMove(packages, truck, objective="value", maxSideways=100, maxIter=2000, seed=None):
    if seed is not None:
        random.seed(seed)

    start = time.perf_counter()
    initial = gen_initial_state(packages, truck)
    current = fotokopi(initial)
    current_value = stateScore(current, packages, objective)

    values = [current_value]
    iterations = 0
    sideways_total = 0
    previous_key = None
    stopped_by = "no_move"

    while iterations < maxIter:
        best = bestImprovingMove(current, packages, truck, objective)
        if best is not None:
            _, new_state, _ = best
            previous_key = geometryKey(current, packages)
            current = new_state
            current_value = stateScore(current, packages, objective)
            values.append(current_value)
            iterations += 1
            continue

        if sideways_total >= maxSideways:
            stopped_by = "max_sideways"
            break

        new_state, _ = findSidewaysMove(current, packages, truck, objective, previous_key)
        if new_state is None:
            stopped_by = "no_move"
            break

        previous_key = geometryKey(current, packages)
        current = new_state
        values.append(current_value)
        iterations += 1
        sideways_total += 1

    return {
        "variant": "sideways_move",
        "objective": objective,
        "seed": seed,
        "initial": initial,
        "final": current,
        "finalVal": current_value,
        "realValue": rawValue(current, packages),
        "duration": time.perf_counter() - start,
        "valuesOT": values,
        "iterations": iterations,
        "max_iter": maxIter,
        "max_sideways": maxSideways,
        "sideways_moves": sideways_total,
        "stopped_by": stopped_by
    }


def randomRestart(packages, truck, objective="value", maxRestart=5, maxIterPerRestart=2000, seed=None):
    if seed is not None:
        random.seed(seed)

    start = time.perf_counter()
    best_state = None
    best_value = None
    first_initial = None
    iterations_per_restart = []
    restart_values = []
    values = []
    restarts = 0

    while restarts < maxRestart:
        # seed=None: tiap restart mengambil initial state random baru dari RNG global
        result = steepestAscent(packages, truck, objective, maxIter=maxIterPerRestart, seed=None)
        if first_initial is None:
            first_initial = result["initial"]
        restarts += 1
        iterations_per_restart.append(result["iterations"])
        restart_values.append(result["finalVal"])
        values.extend(result["valuesOT"])
        if best_value is None or result["finalVal"] > best_value:
            best_value = result["finalVal"]
            best_state = result["final"]

    return {
        "variant": "random_restart",
        "objective": objective,
        "seed": seed,
        "initial": first_initial,
        "final": best_state,
        "finalVal": best_value,
        "realValue": rawValue(best_state, packages),
        "duration": time.perf_counter() - start,
        "valuesOT": values,
        "iterations": sum(iterations_per_restart),
        "max_iter": maxIterPerRestart,
        "max_restart": maxRestart,
        "restarts": restarts,
        "iterations_per_restart": iterations_per_restart,
        "restart_final_values": restart_values
    }


def Run(variant, packages, truck, seed=None, objective="value", **params):
    variants = {
        "steepest_ascent": steepestAscent,
        "stochastic": stochastic,
        "sideways_move": sidewaysMove,
        "random_restart": randomRestart
    }
    if variant not in variants:
        raise ValueError(f"Varian '{variant}' tidak dikenali")
    return variants[variant](packages, truck, objective=objective, seed=seed, **params)


RESULT_EXTRA_KEYS = (
    "max_iter", "max_sideways", "sideways_moves", "stopped_by",
    "trials_per_iteration", "total_attempts",
    "max_restart", "restarts", "iterations_per_restart", "restart_final_values"
)


def saveRun(res, packages, truck, folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)

    for tag, state in (("initial", res["initial"]), ("final", res["final"])):
        inside = {k: placement for k, placement in state.items() if placement["position"] is not None}
        out = {
            "inside": inside,
            "outside": [k for k, placement in state.items() if placement["position"] is None],
            "value": rawValue(state, packages),
            "score": stateScore(state, packages, res["objective"])
        }
        with open(folder / f"{tag}State.json", "w") as f:
            json.dump(out, f, indent=2)
        plotState(state, packages, truck, folder / f"{tag}State.png")

    info = {
        "variant": res["variant"],
        "objective": res["objective"],
        "seed": res["seed"],
        "finalValue": res["finalVal"],
        "realValue": res["realValue"],
        "duration": res["duration"],
        "iterations": res["iterations"]
    }
    for key in RESULT_EXTRA_KEYS:
        if key in res:
            info[key] = res[key]
    with open(folder / "result.json", "w") as f:
        json.dump(info, f, indent=2)

    plotValues(res["valuesOT"], folder / "plotObj.png")


def summaryRow(res):
    row = {
        "variant": res["variant"],
        "seed": res["seed"],
        "finalValue": round(res["finalVal"], 4) if isinstance(res["finalVal"], float) else res["finalVal"],
        "realValue": res["realValue"],
        "duration": round(res["duration"], 3),
        "iterations": res["iterations"]
    }
    for key in ("max_sideways", "sideways_moves", "max_restart", "restarts",
                "iterations_per_restart", "restart_final_values"):
        if key in res:
            row[key] = res[key]
    return row


def saveSummary(rows, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(rows, f, indent=2)


# Eksperimen utama: 3 run per varian (ketentuan spesifikasi)
CONFIGS = [
    ("steepest_ascent", {}),
    ("stochastic", {"trials": 100}),
    ("sideways_move", {"maxSideways": 200}),
    ("random_restart", {"maxRestart": 20})
]


if __name__ == "__main__":
    src = Path(__file__).resolve().parent.parent
    with open(src / "data" / "packages.json") as f:
        packages = json.load(f)
    with open(src / "data" / "truck.json") as f:
        truck = json.load(f)

    rows = []
    for variant, params in CONFIGS:
        for x in (1, 2, 3):
            res = Run(variant, packages, truck, seed=x, **params)
            saveRun(res, packages, truck, src.parent / "output" / "hill_climbing" / variant / f"run{x}")
            rows.append(summaryRow(res))
            print(f"{variant} run {x}: final {res['finalVal']}, "
                  f"real value {res['realValue']}, {res['duration']:.2f} s, "
                  f"iterasi {res['iterations']}")
    saveSummary(rows, src.parent / "output" / "hill_climbing" / "summary.json")
    print("Selesai. Ringkasan tersimpan di output/hill_climbing/summary.json")
