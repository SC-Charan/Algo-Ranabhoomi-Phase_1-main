"""The interface every Relief Loading solver implements, plus helpers.

A plan is {"trucks": [[parcel, ...], ...]}. A load is a (weight, volume) pair.
"""

from abc import ABC, abstractmethod


class Solver(ABC):
    @abstractmethod
    def solve(self, instance, submit_candidate):
        """Call submit_candidate(plan) any number of times; each call returns a receipt
        (accepted, reason, cost, best, elapsed_s, remaining_s). The return value is one
        more candidate."""


def shares(instance, parcel) -> tuple:
    """(weight share, volume share) of one parcel, in permille of a truck."""
    return (instance.weights[parcel] * 1000 // instance.max_weight,
            instance.volumes[parcel] * 1000 // instance.max_volume)


def fits(instance, load, parcel) -> bool:
    """Can `parcel` join a truck already carrying `load` = (weight, volume)?"""
    return (load[0] + instance.weights[parcel] <= instance.max_weight
            and load[1] + instance.volumes[parcel] <= instance.max_volume)


def truck_load(instance, truck) -> tuple:
    return (sum(instance.weights[p] for p in truck), sum(instance.volumes[p] for p in truck))


def truck_fill(instance, truck) -> int:
    """Fill of a truck in permille: the larger of its weight and volume shares (as scored)."""
    w, v = truck_load(instance, truck)
    return max(w * 1000 // instance.max_weight, v * 1000 // instance.max_volume)
