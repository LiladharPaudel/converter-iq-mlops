"""Generate small synthetic episodes in the dataset's record format."""
import json
import math
import random

random.seed(7)
N, AMP, F0, FS = 20, 1500 * math.sqrt(2), 50.0, 1000.0


def cycle(amps=(1, 1, 1), harm=0.0, noise=0.01, offset=(0, 0, 0)):
    out = []
    for p in range(3):
        ph = -p * 2 * math.pi / 3
        for n in range(N):
            t = n / FS
            v = math.sin(2 * math.pi * F0 * t + ph) + harm * math.sin(2 * math.pi * 5 * F0 * t + ph)
            out.append(round(AMP * amps[p] * v + AMP * offset[p] + random.gauss(0, noise * AMP), 2))
    return out


def episode(name, cycles):
    recs = [
        {"timestamp": 1778621660.0 + i * 0.02, "device": "test1", "id_mea": 2,
         "mea_value": c, "id_error": e, "experiment_id": "experiment_3"}
        for i, (c, e) in enumerate(cycles)
    ]
    with open(name, "w") as f:
        json.dump(recs, f)


episode("episode_healthy.json", [(cycle(), 0) for _ in range(40)])
episode("episode_phase_c_open.json",
        [(cycle(), 0) for _ in range(8)] + [(cycle(amps=(1, 1, 0)), 1) for _ in range(32)])
episode("episode_harmonics.json",
        [(cycle(), 0) for _ in range(6)] + [(cycle(harm=0.45), 7) for _ in range(34)])
episode("episode_unbalance.json",
        [(cycle(), 0) for _ in range(6)] + [(cycle(amps=(1.3, 0.85, 0.85)), 4) for _ in range(34)])
print("wrote 4 episodes")
