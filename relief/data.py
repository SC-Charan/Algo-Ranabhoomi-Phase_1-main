"""Relief Loading: two-limit bin packing.

Parcels are cut from m trucks filled close to both limits, then shuffled.
Each suite entry names the draw (profile["attempt"]) to use; the organizer's
private/find_attempts.py picks attempts whose starter and baseline fit the
truck cap and whose baseline needs more than m trucks. This file does exactly
one draw. Integer-only and deterministic.
"""

from dataclasses import dataclass
from types import MappingProxyType

from benchkit import SuiteEntry, freeze_profile
from benchkit.rng import Rng, derive_seed, digest_ints

SCHEMA_VERSION = 1

# Truck-cap slack over the witness count. Next-fit (the starter) needs up to ~1.6x
# the witness, and the starter must always be valid.
K_SLACK_NUM, K_SLACK_DEN = 3, 5

INDEPENDENT = {"family": "independent", "shifted": False, "pairing": "independent",
               "fill_lo": 930, "fill_hi": 980, "pieces_lo": 4, "pieces_hi": 9}
ANTICORRELATED = {"family": "anticorrelated", "shifted": True, "pairing": "anti",
                  "fill_lo": 975, "fill_hi": 998, "pieces_lo": 4, "pieces_hi": 9}


@dataclass(frozen=True)
class Instance:
    name: str
    profile: MappingProxyType
    size: int
    digest: str
    weights: tuple
    volumes: tuple
    max_weight: int
    max_volume: int
    max_trucks: int


def compute_digest(instance) -> str:
    return digest_ints((instance.size, instance.max_weight, instance.max_volume,
                        instance.max_trucks, *instance.weights, *instance.volumes), instance.profile)


def _cut(rng, total, pieces):
    """Split `total` into `pieces` positive integers at distinct random cut points."""
    cuts = set()
    while len(cuts) < pieces - 1:
        cuts.add(rng.between(1, total - 1))
    points = [0, *sorted(cuts), total]
    return [b - a for a, b in zip(points, points[1:])]


def draw(seed, profile):
    """One draw: (instance fields, the m truck groups the parcels were cut from)."""
    profile = freeze_profile(profile)
    rng = Rng(derive_seed("relief", SCHEMA_VERSION, seed, profile["attempt"]))
    n = profile["n"]
    W = rng.between(8000, 12000)
    V = rng.between(6000, 14000)
    parcels, groups = [], []
    while len(parcels) < n:
        pieces = min(rng.between(profile["pieces_lo"], profile["pieces_hi"]), n - len(parcels))
        wt = W * rng.between(profile["fill_lo"], profile["fill_hi"]) // 1000
        vt = V * rng.between(profile["fill_lo"], profile["fill_hi"]) // 1000
        ws = _cut(rng, wt, pieces) if pieces > 1 else [wt]
        vs = _cut(rng, vt, pieces) if pieces > 1 else [vt]
        if profile["pairing"] == "anti":
            ws.sort()
            vs.sort(reverse=True)
        groups.append(list(range(len(parcels), len(parcels) + pieces)))
        parcels.extend(zip(ws, vs))
    order = list(range(n))
    rng.shuffle(order)  # parcel order[k] becomes id k
    new_id = {old: k for k, old in enumerate(order)}
    weights = tuple(parcels[old][0] for old in order)
    volumes = tuple(parcels[old][1] for old in order)
    groups = [[new_id[i] for i in truck] for truck in groups]
    m = len(groups)
    K = m + (K_SLACK_NUM * m + K_SLACK_DEN - 1) // K_SLACK_DEN
    fields = dict(profile=profile, size=n, weights=weights, volumes=volumes,
                  max_weight=W, max_volume=V, max_trucks=K)
    return fields, groups


def make_instance(seed, profile, name) -> Instance:
    fields, _ = draw(seed, profile)
    return Instance(name=name, digest=compute_digest(Instance(name=name, digest="", **fields)), **fields)


def _entry(name, seed, family, n, attempt):
    return SuiteEntry(name, seed, {**family, "n": n, "attempt": attempt})


PUBLIC_SUITE = (
    _entry("relief-01", 1101, INDEPENDENT, 60, 4),
    _entry("relief-02", 1102, INDEPENDENT, 140, 6),
    _entry("relief-03", 1103, INDEPENDENT, 220, 6),
    _entry("relief-04", 1104, INDEPENDENT, 300, 7),
    _entry("relief-05", 1105, ANTICORRELATED, 90, 0),
    _entry("relief-06", 1106, ANTICORRELATED, 240, 0),
)
SELF_CHECK_NAMES = ("relief-01", "relief-05")


def budget_for(instance) -> float:
    return 5.0
