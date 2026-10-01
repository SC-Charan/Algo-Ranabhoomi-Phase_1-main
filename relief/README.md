# Relief Loading

Pack aid parcels onto as few trucks as possible when every truck has two limits.

## The scenario

Amara Okafor runs the depot at Kisoro Crossing. Each morning a pile of relief
parcels arrives: tarpaulin rolls that are light but bulky, water cartons that
are small but heavy. Her trucks can carry only so much weight and only so
much volume, and every truck that leaves costs a driver and a day's fuel. She
wants the fewest trucks, and if she must send one nearly empty, she would
rather it be as empty as possible so it can pick up on the way.

## The problem, precisely

- **Parcels:** `instance.size` parcels, ids `0..n-1`, each with an integer
  `instance.weights[p]` and `instance.volumes[p]`.
- **Trucks:** each truck carries at most `instance.max_weight` in total weight
  **and** at most `instance.max_volume` in total volume.
- **Fleet cap:** at most `instance.max_trucks` non-empty trucks.
- **Plan:** `{"trucks": [[p, p, ...], ...]}`. Every parcel exactly once.
  Empty trucks are allowed and ignored.
- **Cost:** `1000 x trucks used + fill of the least-full truck`, where a
  truck's fill is the larger of its weight share and volume share in permille
  (0..1000). Fewer trucks always wins; among plans with the same count, the
  one whose emptiest truck is emptier wins.

## How you're scored

Your best valid cost is read at 5%, 20%, 50% and 100% of the 5-second budget
(weights 0.10, 0.20, 0.30, 0.40). At each checkpoint the cost is placed on a
curve through three anchors: the starter scores 0.25, the published baseline
0.50, the reference 1.00, linearly in between; beating the reference scores
1.00, no valid plan scores 0.

*Example:* baseline 11,241, reference 10,644 at a checkpoint. A cost of
10,943 is halfway between them and scores 0.75 there.

Points: quality 70 (mean instance score), robustness 20 (mean over the
shifted instances, halved if you are strong on one family and weak on
another), engineering 10 (valid plans, no crashes or overruns, a plan by the
first checkpoint).

## Your submission

```python
from adapter import Solver

class MySolver(Solver):
    def solve(self, instance, submit_candidate):
        receipt = submit_candidate({"trucks": [...]})   # any number of times
        # receipt: accepted, reason, cost, best, elapsed_s, remaining_s
        return {"trucks": [...]}                          # counts as one more candidate
```

Put it in `adapters/mine.py`, then:

```
python self_check.py --adapter adapters.mine:MySolver     # 2 instances, ~15 s
python run.py --adapter adapters.mine:MySolver --out report.json
```

## The trap

Read this before you write anything: **two limits at once.** A truck can be
full by weight while half empty by volume. Sorting or filling by one limit
alone produces trucks that are stuck on the other.

## Baselines

| Anchor | Program | Score |
| --- | --- | --- |
| Starter | next-fit in the given order | 0.25 |
| Baseline | first-fit decreasing by the larger share | 0.50 |
| Reference | a stronger search, not published | 1.00 |

## Your head start

`adapters/starter.py` is a working solver: copy it and improve it.
`adapter.py` gives you `shares(instance, p)`, `fits(instance, load, p)`,
`truck_load(instance, truck)` and `truck_fill(instance, truck)`, all computed
exactly as the validator does.

## A hint

Sorting helps; which order depends on which limit is tighter.

## Instance families

| Family | Public | Private | What changes |
| --- | --- | --- | --- |
| independent | 4 | 4 | weight and volume drawn independently, looser packing |
| anticorrelated (shifted) | 2 | 4 | heavy-small against light-bulky parcels, near-perfect packing |

The private suite uses the same generator with unseen seeds and sizes in the
same range (40 to 300 parcels).

## Files

`adapter.py` (interface, helpers), `adapters/starter.py`,
`adapters/baseline.py`, `data.py` (instances, suite, budget),
`validator.py` (the cost), `self_check.py`, `run.py`,
`public_reference.json` (public anchors), `benchkit/` (harness),
`SECURITY.md`.
