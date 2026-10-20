"""Menghasilkan trace langkah demi langkah untuk eksperimen Hill Climbing.

Jalankan dari root repo:
    MPLBACKEND=Agg ~/.venvs/if3170/bin/python src/trace/trace_hc.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "src"))
sys.path.append(str(ROOT / "src" / "hill_climbing"))

import hill_climbing as hc

CONFIGS = {
    "steepest_ascent": (hc.steepestAscent, {}),
    "stochastic": (hc.stochastic, {"trials": 100}),
    "sideways_move": (hc.sidewaysMove, {"maxSideways": 200}),
    "random_restart": (hc.randomRestart, {"maxRestart": 20}),
}


def main():
    packages = json.loads((ROOT / "src" / "data" / "packages.json").read_text())
    truck = json.loads((ROOT / "src" / "data" / "truck.json").read_text())

    for name, (fn, params) in CONFIGS.items():
        for run in (1, 2, 3):
            trace = []
            res = fn(packages, truck, seed=run, trace=trace, **params)
            payload = {
                "algo": name,
                "seed": run,
                "objective": "value",
                "finalValue": res["finalVal"],
                "frames": trace,
            }
            out = ROOT / "output" / "hill_climbing" / name / f"run{run}" / "trace.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(payload, separators=(",", ":")))
            print(f"{name:16s} run{run} final={res['finalVal']:5d} frames={len(trace):4d} {out.stat().st_size / 1024:6.0f} KB")


if __name__ == "__main__":
    main()
