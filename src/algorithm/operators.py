
import random
from typing import Tuple, Dict
from src.models.timetable import Timetable

def crossover(a: Timetable, b: Timetable) -> Tuple[Timetable, Timetable]:
    slots = a.slots
    c1 = a.copy()
    c2 = b.copy()
    if slots < 2:
        return c1, c2
    p1 = random.randint(0, slots - 2)
    p2 = random.randint(p1 + 1, slots - 1)
    for i in range(p1, p2):
        c1.assignments[i], c2.assignments[i] = c2.assignments[i], c1.assignments[i]
    return c1, c2

def mutate_swap(ind: Timetable, rate: float = 0.05) -> Timetable:
    t = ind.copy()
    for i in range(t.slots):
        if random.random() < rate:
            j = random.randint(0, t.slots - 1)
            t.assignments[i], t.assignments[j] = t.assignments[j], t.assignments[i]
    return t

def mutate_compact(ind: Timetable, rate: float = 0.05) -> Timetable:
    t = ind.copy()
    by_day = t.daily_indices()
    for day, idxs in by_day.items():
        if random.random() >= rate or len(idxs) < 3:
            continue
        scheduled = [i for i in idxs if t.assignments[i] is not None]
        if len(scheduled) < 2:
            continue
        first_i, last_i = scheduled[0], scheduled[-1]
        internal_gaps = [i for i in idxs if first_i < i < last_i and t.assignments[i] is None]
        edge_empties = [i for i in idxs if (i <= first_i or i >= last_i) and t.assignments[i] is None]
        if internal_gaps and edge_empties:
            neighbors = set()
            for g in internal_gaps:
                pos = idxs.index(g)
                for nb_idx in (pos - 1, pos + 1):
                    if 0 <= nb_idx < len(idxs):
                        neighbors.add(idxs[nb_idx])
            neighbor_classes = [i for i in neighbors if t.assignments[i] is not None]
            if neighbor_classes:
                src = random.choice(neighbor_classes)
                dst = random.choice(edge_empties)
                t.assignments[src], t.assignments[dst] = t.assignments[dst], t.assignments[src]
    return t

def repair_hours(ind: Timetable, course_hours_required: Dict[str, int]) -> Timetable:
    t = ind.copy()
    counts = t.count_course_hours()
    for cid, req in course_hours_required.items():
        have = counts.get(cid, 0)
        while have < req:
            try:
                idx = t.assignments.index(None)
            except ValueError:
                break
            t.assignments[idx] = cid
            have += 1
    for cid, req in course_hours_required.items():
        have = sum(1 for x in t.assignments if x == cid)
        while have > req:
            idxs = [i for i, x in enumerate(t.assignments) if x == cid]
            if not idxs:
                break
            idx = random.choice(idxs)
            t.assignments[idx] = None
            have -= 1
    return t

def influence_from_belief(ind: Timetable, belief_best: Timetable, influence_rate: float = 0.1) -> Timetable:
    t = ind.copy()
    for i in range(t.slots):
        if belief_best.assignments[i] is not None and random.random() < influence_rate:
            t.assignments[i] = belief_best.assignments[i]
    return t
