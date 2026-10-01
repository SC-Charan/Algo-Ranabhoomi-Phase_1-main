"""Feasibility and canonical cost for Relief Loading.

cost = 1000 * trucks_used + fill of the least-full used truck (permille),
where a truck's fill is the larger of its weight share and volume share.
"""


def _fill(w, v, instance):
    return max(w * 1000 // instance.max_weight, v * 1000 // instance.max_volume)


def validate(instance, candidate):
    if not isinstance(candidate, dict):
        return None, "candidate must be a dict"
    trucks = candidate.get("trucks")
    if not isinstance(trucks, list):
        return None, "'trucks' must be a list of lists of parcel ids"
    n = instance.size
    if len(trucks) > n:  # size caps before any per-parcel work
        return None, f"{len(trucks)} trucks listed, more than the {n} parcels"
    total = 0
    for truck in trucks:
        if not isinstance(truck, list):
            return None, "every truck must be a list of parcel ids"
        total += len(truck)
        if total > n:
            return None, f"more than {n} parcel ids in the plan"
    if total < n:
        return None, f"only {total} of {n} parcels are loaded"

    seen = bytearray(n)
    used, least = 0, None
    for k, truck in enumerate(trucks):
        if not truck:
            continue
        w = v = 0
        for p in truck:
            if type(p) is not int or not 0 <= p < n:
                return None, f"parcel id {p!r} is not an integer in 0..{n - 1}"
            if seen[p]:
                return None, f"parcel {p} is loaded twice"
            seen[p] = 1
            w += instance.weights[p]
            v += instance.volumes[p]
        if w > instance.max_weight:
            return None, f"truck {k} carries weight {w} > {instance.max_weight}"
        if v > instance.max_volume:
            return None, f"truck {k} carries volume {v} > {instance.max_volume}"
        used += 1
        fill = _fill(w, v, instance)
        least = fill if least is None else min(least, fill)
    if used > instance.max_trucks:
        return None, f"{used} trucks used, the cap is {instance.max_trucks}"
    return 1000 * used + least, None
