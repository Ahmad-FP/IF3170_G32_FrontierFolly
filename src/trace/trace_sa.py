"""Menghasilkan trace langkah demi langkah untuk eksperimen Simulated Annealing.

Loop mereplikasi `sa.Run()` persis (seed, urutan pemanggilan RNG, dan rumus
penerimaan sama) sehingga nilai akhir trace identik dengan `result.json`.

Jalankan dari root repo:
    MPLBACKEND=Agg ~/.venvs/if3170/bin/python src/trace/trace_sa.py
"""

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "src"))
sys.path.append(str(ROOT / "src" / "simulated_annealing"))

import sa


def traceFrame(state, packages, kind="step", **extra):
    return {
        "kind": kind,
        "value": sa.truckValue(state, packages),
        "inside": {
            package_id: {
                "position": list(placement["position"]),
                "orientation": list(placement["orientation"]),
            }
            for package_id, placement in state.items()
        },
        "outside": [package_id for package_id in packages if package_id not in state],
        **extra,
    }


def runTrace(packages, truck, TStart=250, cooling=0.9999, Tmin=10, t=40000, seed=None):
    random.seed(seed)
    cur = sa.initState(packages, truck)
    curVal = sa.truckValue(cur, packages)
    T = TStart
    frames = [traceFrame(cur, packages, "initial", temp=T)]

    for i in range(t):
        if T < Tmin:
            break
        new = sa.ranbor(cur, packages, truck)
        if new is not None:
            delta = sa.truckValue(new, packages) - curVal
            prob = sa.acc(delta, T) if delta < 0 else None
            if delta >= 0 or random.random() < prob:
                cur, curVal = new, curVal + delta
                frames.append(traceFrame(cur, packages, "step", iter=i, temp=T, delta=delta))
        T *= cooling

    return curVal, frames


def thinFrames(frames, limit=600):
    if len(frames) <= limit:
        return frames
    step = max(1, len(frames) // (limit - 2))
    keep = set(range(0, len(frames), step))
    best = -1
    for index, frame in enumerate(frames):
        if frame["value"] > best:
            best = frame["value"]
            keep.add(index)
    keep.add(len(frames) - 1)
    return [frames[index] for index in sorted(keep)]


def main():
    packages = json.loads((ROOT / "src" / "data" / "packages.json").read_text())
    truck = json.loads((ROOT / "src" / "data" / "truck.json").read_text())

    for run in (1, 2, 3):
        finalVal, frames = runTrace(packages, truck, seed=run)
        frames = thinFrames(frames)
        payload = {
            "algo": "sa",
            "seed": run,
            "objective": "value",
            "finalValue": finalVal,
            "frames": frames,
        }
        out = ROOT / "output" / "simulated_annealing" / f"run{run}" / "trace.json"
        out.write_text(json.dumps(payload, separators=(",", ":")))
        print(f"sa run{run} final={finalVal:5d} frames={len(frames):4d} {out.stat().st_size / 1024:6.0f} KB")


if __name__ == "__main__":
    main()
