import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

def box(x, y, z, w, l, h):
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
        if x["position"] is None:
            continue
        (px, py, pz), (w, l, h) = x["position"], [packages[id]['dimensions'][i] for i in x["orientation"]]
        faces += box(px, py, pz, w, l, h)
        colors += [palette[list(packages).index(id)]] * 6
    a.add_collection3d(Poly3DCollection(faces, facecolor=colors, edgecolor="blue"))
    a.add_collection3d(Poly3DCollection(box(0, 0, 0, W, L, H), facecolor=(0, 0, 0, 0), edgecolor="black"))
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
