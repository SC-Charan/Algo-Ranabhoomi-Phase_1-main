import time

from adapter import Solver, dist_table


class MySolver(Solver):
    def solve(self, instance, submit_candidate):
        table = dist_table(instance)
        weights = instance.weights
        k = instance.k
        m = len(instance.sites)
        penalty = instance.penalty

        def objective(sites):
            return sum(w * min(row[s] for s in sites)
                       for w, row in zip(weights, table))

        def greedy_from(start_site):
            sites = [start_site]
            current = [row[start_site] for row in table]
            closed = set(range(m))
            closed.remove(start_site)
            while len(sites) < k:
                best_site = min(
                    closed,
                    key=lambda s: sum(w * min(nearest, row[s])
                                      for w, nearest, row in zip(weights, current, table)),
                )
                sites.append(best_site)
                closed.remove(best_site)
                current = [min(nearest, row[best_site])
                           for nearest, row in zip(current, table)]
            return sites

        # Ensure a valid plan exists before the first checkpoint.
        receipt = submit_candidate({"sites": list(range(k))})

        first_site = min(
            range(m),
            key=lambda s: sum(w * row[s] for w, row in zip(weights, table)),
        )
        opened = greedy_from(first_site)

        receipt = submit_candidate({"sites": list(opened)})
        deadline = time.monotonic() + max(0.0, receipt["remaining_s"] - 1.0)
        best_cost = objective(opened)
        restart_seconds = 1.5 if k <= 8 else 0.45
        restart_deadline = min(deadline, time.monotonic() + restart_seconds)
        for start_site in range(m):
            if time.monotonic() >= restart_deadline:
                break
            candidate = greedy_from(start_site)
            candidate_cost = objective(candidate)
            if candidate_cost < best_cost:
                opened = candidate
                best_cost = candidate_cost
                receipt = submit_candidate({"sites": list(opened)})

        while time.monotonic() < deadline:
            nearest = []
            second = []
            for row in table:
                ranked = sorted((row[s], s) for s in opened)
                nearest.append(ranked[0][0])
                second.append(ranked[1][0] if len(ranked) > 1 else penalty)
            current_cost = sum(w * d for w, d in zip(weights, nearest))
            best_move = None
            best_cost = current_cost
            opened_set = set(opened)
            swap_options = [[] for _ in opened]
            for pos, old_site in enumerate(opened):
                for candidate in range(m):
                    if candidate in opened_set:
                        continue
                    score = sum(
                        w * min(second[i] if nearest[i] == table[i][old_site]
                                else nearest[i], row[candidate])
                        for i, (w, row) in enumerate(zip(weights, table))
                    )
                    swap_options[pos].append((score, candidate))
                    if score < best_cost:
                        best_cost = score
                        best_move = (pos, candidate)
            if best_move is None:
                best_pair = None
                best_pair_cost = current_cost
                shortlist_size = 20 if k <= 8 else 12 if k <= 12 else 6
                timed_out = False
                for pos_a in range(len(opened)):
                    if time.monotonic() >= deadline:
                        timed_out = True
                        break
                    for pos_b in range(pos_a + 1, len(opened)):
                        if time.monotonic() >= deadline:
                            timed_out = True
                            break
                        remaining = [
                            min(
                                (row[s] for i, s in enumerate(opened)
                                 if i != pos_a and i != pos_b),
                                default=penalty,
                            )
                            for row in table
                        ]
                        for _, candidate_a in sorted(swap_options[pos_a])[:shortlist_size]:
                            for _, candidate_b in sorted(swap_options[pos_b])[:shortlist_size]:
                                if time.monotonic() >= deadline:
                                    timed_out = True
                                    break
                                if candidate_a == candidate_b:
                                    continue
                                score = 0
                                for w, base, row in zip(weights, remaining, table):
                                    score += w * min(base, row[candidate_a],
                                                     row[candidate_b])
                                if score < best_pair_cost:
                                    best_pair_cost = score
                                    best_pair = (pos_a, pos_b, candidate_a, candidate_b)
                            if timed_out:
                                break
                        if timed_out:
                            break
                    if timed_out:
                        break
                if best_pair is None:
                    best_triple = None
                    best_triple_cost = current_cost
                    if k <= 8 and not timed_out:
                        triple_options = [
                            sorted(options)[:8] for options in swap_options
                        ]
                        for pos_a in range(len(opened)):
                            if time.monotonic() >= deadline:
                                timed_out = True
                                break
                            for pos_b in range(pos_a + 1, len(opened)):
                                for pos_c in range(pos_b + 1, len(opened)):
                                    if time.monotonic() >= deadline:
                                        timed_out = True
                                        break
                                    remaining = [
                                        min(
                                            (row[s] for i, s in enumerate(opened)
                                             if i not in (pos_a, pos_b, pos_c)),
                                            default=penalty,
                                        )
                                        for row in table
                                    ]
                                    for _, candidate_a in triple_options[pos_a]:
                                        for _, candidate_b in triple_options[pos_b]:
                                            if candidate_a == candidate_b:
                                                continue
                                            for _, candidate_c in triple_options[pos_c]:
                                                if time.monotonic() >= deadline:
                                                    timed_out = True
                                                    break
                                                if candidate_c in (candidate_a, candidate_b):
                                                    continue
                                                score = sum(
                                                    w * min(base, row[candidate_a],
                                                            row[candidate_b], row[candidate_c])
                                                    for w, base, row in zip(weights, remaining, table)
                                                )
                                                if score < best_triple_cost:
                                                    best_triple_cost = score
                                                    best_triple = (
                                                        pos_a, pos_b, pos_c,
                                                        candidate_a, candidate_b, candidate_c,
                                                    )
                                            if timed_out:
                                                break
                                        if timed_out:
                                            break
                                    if timed_out:
                                        break
                                if timed_out:
                                    break
                            if timed_out:
                                break
                    if best_triple is None:
                        break
                    pos_a, pos_b, pos_c, candidate_a, candidate_b, candidate_c = best_triple
                    opened[pos_a] = candidate_a
                    opened[pos_b] = candidate_b
                    opened[pos_c] = candidate_c
                else:
                    pos_a, pos_b, candidate_a, candidate_b = best_pair
                    opened[pos_a] = candidate_a
                    opened[pos_b] = candidate_b
            else:
                opened[best_move[0]] = best_move[1]
            receipt = submit_candidate({"sites": list(opened)})

        return {"sites": list(opened)}
