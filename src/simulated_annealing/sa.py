import sys
import math
import time
import json
import random
from pathlib import Path
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
sys.path.append(str(Path(__file__).resolve().parent.parent))
from constraint import state_valid
from initial_state import gen_initial_state, possible_height

def initState(packages, truck):
    state = gen_initial_state(packages, truck)
    return {id: x for id, x in state.items() if x["position"] is not None}

def truckValue(states, packages):
    totVal = 0
    totVal += sum(packages[x]['value'] for x in states)
    return totVal

def dims(id, orient, packages):
    return [packages[id]['dimensions'][i] for i in orient]

def fotokopi(state):
    newstate = {id: dict(x) for id, x in state.items()}
    return newstate

def ranbor(state, packages, truck, t=50):
    W, L, H = truck["dimensions"]
    aksis = {"x": (1, 2), "y": (0, 2), "z": (0, 1)}  
    for _ in range(t):
        move = random.choice(["swap", "move", "rotate"] if state else ["move"])
        new = fotokopi(state)
        if move == "swap":
            a = random.choice(list(state))
            b = random.choice([id for id in packages if id != a])
            if b in state:
                new[a]['position'], new[b]['position'] = state[b]['position'], state[a]['position']
            else:
                new[b] = state[a]
                del new[a]
        elif move == "move":
            id = random.choice(list(packages))
            if id in state and random.random() < 0.51:
                del new[id]
            else:
                orient = state[id]["orientation"] if id in state else random.sample((0, 1, 2), 3)
                w, l, h = dims(id, orient, packages)
                new.pop(id, None)
                floor = [z for z in possible_height(new, packages) if z + h <= H]
                if not floor or w > W or l > L:
                    continue
                pos = (random.randint(0, W - w), random.randint(0, L - l), random.choice(floor))
                new[id] = {"position": pos, "orientation": orient}
        else:
            id = random.choice(list(state))
            i, j = aksis[random.choice("xyz")]
            orient = list(state[id]["orientation"])
            orient[i], orient[j] = orient[j], orient[i]
            new[id] = {"position": state[id]["position"], "orientation": orient}
        if state_valid(new, packages, truck):
            return new
    return None

def acc(delta, T):
    return math.exp( delta / T)

def Run(packages, truck, TStart=250, cooling=0.9999, Tmin=10, t=40000, seed=None):
    random.seed(seed)
    start = time.perf_counter()
    initial = cur = initState(packages, truck)
    curVal = truckValue(cur, packages)
    T = TStart
    values, probs = [], []
    maxVal, noInc, stuck = curVal, 0,0
    for _ in range(t):
        if T < Tmin:
            break
        new = ranbor(cur, packages, truck)
        prob = None
        if new is not None:
            delta = truckValue(new, packages) - curVal
            prob = acc(delta,T) if delta < 0 else None
            if delta >= 0 or random.random() < prob:
                cur, curVal = new, curVal + delta
        values.append(curVal)
        probs.append(prob)
        T *= cooling
        if curVal> maxVal:
            maxVal, noInc = curVal,0
        else:
            noInc += 1
            if noInc % (t // 50) == 0: stuck +=1
    return {
        "initial": initial, "final": cur, "finalVal": curVal,
        "duration": time.perf_counter() - start,
        "valuesOT": values, "probs": probs, "stuck": stuck
    }

def ngotakin(x, y, z, w, l, h):
    c = [(x + i * w, y + j * l, z + k * h) for i in (0, 1) for j in (0, 1) for k in (0, 1)]
    return [[c[0], c[1], c[3], c[2]], [c[4], c[5], c[7], c[6]],
            [c[0], c[1], c[5], c[4]], [c[2], c[3], c[7], c[6]],
            [c[0], c[2], c[6], c[4]], [c[1], c[3], c[7], c[5]]]

def plotState(state, packages, truck, path):
    W, L, H = truck["dimensions"]
    a = plt.figure(figsize=(4,4)).add_subplot(projection="3d")
    faces, colors = [], []
    palette = plt.cm.tab20.colors + plt.cm.tab20b.colors
    for id, x in state.items():
        (px, py, pz), (w, l, h) = x["position"], dims(id, x["orientation"], packages)
        faces += ngotakin(px, py, pz, w, l, h)
        colors += [palette[list(packages).index(id)]] * 6
    a.add_collection3d(Poly3DCollection(faces, facecolor=colors, edgecolor="blue"))
    a.add_collection3d(Poly3DCollection(ngotakin(0, 0, 0, W, L, H), facecolor=(0, 0, 0, 0), edgecolor="black"))
    a.set(xlim=(0, W), ylim=(0, L), zlim=(0, H), xlabel="x", ylabel="y", zlabel="z")
    a.set_box_aspect((W, L, H), zoom=1)
    a.grid(False)
    for x in (a.xaxis, a.yaxis, a.zaxis):
        x.set_pane_color("white")
    plt.savefig(path, dpi=100)
    plt.close()

def plotValues(values, path):
    plt.plot(values)
    plt.xlabel("Iteration")
    plt.ylabel("Value")
    plt.savefig(path, dpi=100)
    plt.close()

def plotProbs(probs, path):
    steps, ps = zip(*[(i, p) for i, p in enumerate(probs) if p is not None])
    plt.scatter(steps, ps, s=1)
    plt.xlabel("Iteration")
    plt.ylabel(r"$e^{\Delta E / T}$")
    plt.savefig(path, dpi=100)
    plt.close()

def saveRun(r, packages, truck, folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    
    state = r['initial']
    out = {"inside": state, "outside": [id for id in packages if id not in state], "value": truckValue(state, packages)}
    with open(folder / "initialState.json", "w") as f:
        json.dump(out, f, indent=2)
    plotState(state, packages, truck, folder / "initialState.png")
    
    state = r['final']
    out = {"inside": state, "outside": [id for id in packages if id not in state], "value": truckValue(state, packages)}
    with open(folder / "finalState.json", "w") as f:
        json.dump(out, f, indent=2)
    plotState(state, packages, truck, folder / "finalState.png")
    
    with open(folder / "result.json", "w") as f:
        json.dump({"finalValue": r["finalVal"], "duration": r["duration"], "stuck": r["stuck"]}, f, indent=2)
    plotValues(r["valuesOT"], folder / "plotObj.png")
    plotProbs(r["probs"], folder / "plotAcceptance.png")

if __name__ == "__main__":
    src = Path(__file__).resolve().parent.parent
    with open(src / "data" / "packages.json") as f:
        packages = json.load(f)
    with open(src / "data" / "truck.json") as f:
        truck = json.load(f)
    for x in (1, 2, 3):
        r = Run(packages, truck, seed=x)
        saveRun(r, packages, truck, src.parent / "output" / "simulated_annealing" / f"run{x}")
        print(f"run {x}: final {r['finalVal']}, {r['duration']:.2f} s, stuck {r['stuck']}")