"""Baseline: first-fit decreasing by the larger of the two shares."""

from adapter import Solver, fits, shares


class BaselineSolver(Solver):
    def solve(self, instance, submit_candidate):
        order = sorted(range(instance.size), key=lambda p: -max(shares(instance, p)))
        trucks, loads = [], []
        for p in order:
            for j, load in enumerate(loads):
                if fits(instance, load, p):
                    trucks[j].append(p)
                    loads[j] = (load[0] + instance.weights[p], load[1] + instance.volumes[p])
                    break
            else:
                trucks.append([p])
                loads.append((instance.weights[p], instance.volumes[p]))
        return {"trucks": trucks}
