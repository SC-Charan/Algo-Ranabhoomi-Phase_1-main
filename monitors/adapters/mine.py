import time

from adapter import Solver, dist_table


class MySolver(Solver):
    def solve(self, instance, submit_candidate):
        start_time = time.perf_counter()

        table = dist_table(instance)
        weights = instance.weights
        n = instance.size
        m = len(instance.sites)
        k = instance.k
        penalty = instance.penalty

        best_global_cost = None
        best_global_sites = None

        # ---------------------------------------------------------
        # EXACT COST
        # ---------------------------------------------------------
        def calculate_cost(sites):
            total = 0

            for i in range(n):
                nearest = penalty
                row = table[i]

                for s in sites:
                    d = row[s]

                    if d < nearest:
                        nearest = d

                total += weights[i] * nearest

            return total

        # ---------------------------------------------------------
        # GREEDY CONSTRUCTION
        # ---------------------------------------------------------
        def greedy_from_seed(seed):
            opened = [seed]
            opened_set = {seed}

            best = [table[i][seed] for i in range(n)]

            while len(opened) < k:
                best_site = -1
                best_gain = -1

                for s in range(m):
                    if s in opened_set:
                        continue

                    gain = 0

                    for i in range(n):
                        old = best[i]
                        new = table[i][s]

                        if new < old:
                            gain += weights[i] * (old - new)

                    if gain > best_gain:
                        best_gain = gain
                        best_site = s

                opened.append(best_site)
                opened_set.add(best_site)

                for i in range(n):
                    d = table[i][best_site]

                    if d < best[i]:
                        best[i] = d

            total = sum(weights[i] * best[i] for i in range(n))

            return opened, total

        # ---------------------------------------------------------
        # 1-FOR-1 LOCAL SEARCH
        # ---------------------------------------------------------
        def improve(sites, current_cost):
            sites = list(sites)

            while time.perf_counter() - start_time < 4.70:
                selected = set(sites)

                nearest = [penalty] * n
                second = [penalty] * n
                nearest_site = [-1] * n

                # Find nearest and second nearest facilities.
                for i in range(n):
                    first = penalty
                    second_best = penalty
                    first_site = -1

                    row = table[i]

                    for s in sites:
                        d = row[s]

                        if d < first:
                            second_best = first
                            first = d
                            first_site = s

                        elif d < second_best:
                            second_best = d

                    nearest[i] = first
                    second[i] = second_best
                    nearest_site[i] = first_site

                best_delta = 0
                best_position = -1
                best_new_site = -1

                for pos, old_site in enumerate(sites):
                    for new_site in range(m):
                        if new_site in selected:
                            continue

                        delta = 0

                        for i in range(n):
                            row = table[i]

                            if nearest_site[i] == old_site:
                                old_distance = second[i]
                            else:
                                old_distance = nearest[i]

                            new_distance = row[new_site]

                            if new_distance > old_distance:
                                new_distance = old_distance

                            delta += weights[i] * (new_distance - nearest[i])

                        if delta < best_delta:
                            best_delta = delta
                            best_position = pos
                            best_new_site = new_site

                    if time.perf_counter() - start_time >= 4.70:
                        break

                if best_position == -1:
                    break

                sites[best_position] = best_new_site
                current_cost += best_delta

                yield list(sites), current_cost

        # ---------------------------------------------------------
        # 2-FACILITY DESTROY + REBUILD
        #
        # Removes two selected facilities and greedily rebuilds
        # both. This can escape a 1-swap local optimum.
        # ---------------------------------------------------------
        def rebuild_two(sites):
            original = list(sites)

            best_result = list(sites)
            best_result_cost = calculate_cost(sites)

            for a in range(k):
                if time.perf_counter() - start_time >= 4.70:
                    break

                for b in range(a + 1, k):
                    if time.perf_counter() - start_time >= 4.70:
                        break

                    remaining = []

                    for p in range(k):
                        if p != a and p != b:
                            remaining.append(original[p])

                    used = set(remaining)

                    nearest = [penalty] * n

                    for i in range(n):
                        row = table[i]
                        best_distance = penalty

                        for s in remaining:
                            d = row[s]

                            if d < best_distance:
                                best_distance = d

                        nearest[i] = best_distance

                    for _ in range(2):
                        best_site = -1
                        best_gain = -1

                        for s in range(m):
                            if s in used:
                                continue

                            gain = 0

                            for i in range(n):
                                old = nearest[i]
                                new = table[i][s]

                                if new < old:
                                    gain += weights[i] * (old - new)

                            if gain > best_gain:
                                best_gain = gain
                                best_site = s

                        if best_site == -1:
                            break

                        remaining.append(best_site)
                        used.add(best_site)

                        for i in range(n):
                            d = table[i][best_site]

                            if d < nearest[i]:
                                nearest[i] = d

                    new_cost = sum(weights[i] * nearest[i] for i in range(n))

                    if new_cost < best_result_cost:
                        best_result_cost = new_cost
                        best_result = list(remaining)

            return best_result, best_result_cost

        # ---------------------------------------------------------
        # RANK ALL POSSIBLE SINGLE STARTS
        # ---------------------------------------------------------
        single_scores = []

        for s in range(m):
            single_cost = 0

            for i in range(n):
                single_cost += weights[i] * table[i][s]

            single_scores.append((single_cost, s))

        single_scores.sort()

        # ---------------------------------------------------------
        # FIRST CANDIDATE
        #
        # Submit as early as possible.
        # ---------------------------------------------------------
        initial_sites, initial_cost = greedy_from_seed(single_scores[0][1])

        submit_candidate({"sites": list(initial_sites)})

        best_global_sites = list(initial_sites)
        best_global_cost = calculate_cost(initial_sites)

        # ---------------------------------------------------------
        # DETERMINISTIC DIVERSE SEEDS
        # ---------------------------------------------------------
        seeds = []

        # Best 3
        for i in range(min(3, len(single_scores))):
            seeds.append(single_scores[i][1])

        # 25th percentile
        if len(single_scores) > 3:
            seeds.append(single_scores[len(single_scores) // 4][1])

        # Median
        if len(single_scores) > 6:
            seeds.append(single_scores[len(single_scores) // 2][1])

        # Worst
        if len(single_scores) > 10:
            seeds.append(single_scores[-1][1])

        unique_seeds = []

        for seed in seeds:
            if seed not in unique_seeds:
                unique_seeds.append(seed)

        # ---------------------------------------------------------
        # MULTI-START SEARCH
        # ---------------------------------------------------------
        for seed in unique_seeds:
            if time.perf_counter() - start_time >= 4.70:
                break

            sites, current_cost = greedy_from_seed(seed)

            # -----------------------------------------------------
            # NORMAL 1-SWAP IMPROVEMENT
            # -----------------------------------------------------
            for improved_sites, improved_cost in improve(sites, current_cost):
                if improved_cost < best_global_cost:
                    best_global_cost = improved_cost
                    best_global_sites = list(improved_sites)
                    submit_candidate({"sites": list(best_global_sites)})

                if time.perf_counter() - start_time >= 4.70:
                    break

            if time.perf_counter() - start_time >= 4.70:
                break

            # -----------------------------------------------------
            # CHECK FINAL LOCAL-SEARCH SOLUTION
            # -----------------------------------------------------
            final_cost = calculate_cost(sites)

            if final_cost < best_global_cost:
                best_global_cost = final_cost
                best_global_sites = list(sites)
                submit_candidate({"sites": list(best_global_sites)})

            if time.perf_counter() - start_time >= 4.70:
                break

            # -----------------------------------------------------
            # 2-FACILITY DESTROY + REBUILD
            # -----------------------------------------------------
            rebuilt_sites, rebuilt_cost = rebuild_two(best_global_sites)

            if rebuilt_cost < best_global_cost:
                best_global_cost = rebuilt_cost
                best_global_sites = list(rebuilt_sites)
                submit_candidate({"sites": list(best_global_sites)})

            if time.perf_counter() - start_time >= 4.70:
                break

            # -----------------------------------------------------
            # RUN 1-SWAP AGAIN AFTER REBUILD
            # -----------------------------------------------------
            for improved_sites, improved_cost in improve(rebuilt_sites, rebuilt_cost):
                if improved_cost < best_global_cost:
                    best_global_cost = improved_cost
                    best_global_sites = list(improved_sites)
                    submit_candidate({"sites": list(best_global_sites)})

                if time.perf_counter() - start_time >= 4.70:
                    break

        # ---------------------------------------------------------
        # FINAL
        # ---------------------------------------------------------
        return {"sites": list(best_global_sites)}
