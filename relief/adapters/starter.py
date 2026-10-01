"""Starter: next-fit in the given order. One truck open at a time."""

from adapter import Solver, fits


class StarterSolver(Solver):
    def solve(self, instance, submit_candidate):
        trucks, load = [], (0, 0)
        for p in range(instance.size):
            if not trucks or not fits(instance, load, p):
                trucks.append([])
                load = (0, 0)
            trucks[-1].append(p)
            load = (load[0] + instance.weights[p], load[1] + instance.volumes[p])
        return {"trucks": trucks}
