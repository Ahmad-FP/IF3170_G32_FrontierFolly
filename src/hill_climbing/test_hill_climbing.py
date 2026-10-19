import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

import hill_climbing as hc
from constraint import state_valid

# Small dataset
packages = {
    "a": {"id": "a", "dimensions": [2, 2, 1], "orientation": [0, 1, 2], "value": 10, "weight": 2, "is_fragile": False, "eta": 2},
    "b": {"id": "b", "dimensions": [2, 2, 2], "orientation": [0, 1, 2], "value": 30, "weight": 4, "is_fragile": False, "eta": 1},
    "c": {"id": "c", "dimensions": [1, 1, 1], "orientation": [0, 1, 2], "value": 5, "weight": 1, "is_fragile": True, "eta": 3},
    "d": {"id": "d", "dimensions": [4, 4, 1], "orientation": [0, 1, 2], "value": 7, "weight": 3, "is_fragile": False, "eta": 1}
}
truck = {"dimensions": [4, 4, 3], "max_capacity": 12}


def cek_naik(values):
    return all(values[i] <= values[i + 1] for i in range(len(values) - 1))


initial = hc.gen_initial_state(packages, truck)
assert state_valid(initial, packages, truck), "initial state tidak valid"
print("1. initial state valid: OK")

res = hc.steepestAscent(packages, truck, seed=1)
assert cek_naik(res["valuesOT"]), "steepest ascent tidak monoton"
assert state_valid(res["final"], packages, truck), "final state steepest ascent tidak valid"
assert hc.bestImprovingMove(res["final"], packages, truck) is None, "masih ada langkah improving"
assert res["finalVal"] == hc.stateScore(res["final"], packages), "finalVal tidak konsisten"
print(f"2. steepest ascent: OK (final {res['finalVal']}, {res['iterations']} iterasi)")

res2 = hc.steepestAscent(packages, truck, seed=1)
assert res["finalVal"] == res2["finalVal"], "hasil steepest ascent tidak deterministik"
print("3. determinisme steepest ascent: OK")

res = hc.stochastic(packages, truck, trials=20, seed=1)
assert cek_naik(res["valuesOT"]), "stochastic tidak monoton"
assert state_valid(res["final"], packages, truck), "final state stochastic tidak valid"
print(f"4. stochastic: OK (final {res['finalVal']}, {res['iterations']} iterasi, "
      f"{res['total_attempts']} percobaan)")

res = hc.sidewaysMove(packages, truck, maxSideways=10, seed=1)
assert cek_naik(res["valuesOT"]), "sideways move menurunkan nilai"
assert res["sideways_moves"] <= 10, "sideways melebihi max_sideways"
assert state_valid(res["final"], packages, truck), "final state sideways tidak valid"
print(f"5. sideways move: OK (final {res['finalVal']}, {res['sideways_moves']} sideways, "
      f"berhenti karena {res['stopped_by']})")

res = hc.randomRestart(packages, truck, maxRestart=3, seed=1)
assert res["restarts"] == 3, "jumlah restart salah"
assert len(res["iterations_per_restart"]) == 3, "iterasi per restart tidak lengkap"
assert res["finalVal"] == max(res["restart_final_values"]), "final bukan solusi terbaik"
assert state_valid(res["final"], packages, truck), "final state random restart tidak valid"
print(f"6. random restart: OK (final {res['finalVal']}, restart terbaik "
      f"{res['restart_final_values']})")

res = hc.steepestAscent(packages, truck, objective="urgency", seed=1)
assert state_valid(res["final"], packages, truck), "final state objective urgency tidak valid"
assert abs(res["finalVal"] - hc.stateScore(res["final"], packages, "urgency")) < 1e-9
print(f"7. objective urgency: OK (skor {res['finalVal']:.2f}, real value {res['realValue']})")

state = hc.gen_initial_state(packages, truck)
state["c"] = {"position": (0, 0, 0), "orientation": (0, 1, 2)}   # fragile di lantai
state["a"] = {"position": (0, 0, 1), "orientation": (0, 1, 2)}   # a di atas c -> invalid
state["b"] = {"position": None, "orientation": (0, 1, 2)}
state["d"] = {"position": None, "orientation": (0, 1, 2)}
assert not state_valid(state, packages, truck), "fragile seharusnya tidak boleh jadi penopang"
print("8. constraint fragile: OK")

print("\nSEMUA TEST LULUS")
