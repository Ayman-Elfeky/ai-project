
import random
from typing import List, Dict
from src.models.timetable import Timetable

class Population:
    def __init__(self, size: int, slots: int, slot_meta: List[dict]):
        self.size = size
        self.slots = slots
        self.slot_meta = slot_meta
        self.individuals: List[Timetable] = []

    def initialize(self, course_pool: List[str], course_hours: Dict[str, int]):
        self.individuals = []
        for _ in range(self.size):
            t = Timetable(self.slots, slot_meta=self.slot_meta)
            pool: List[str] = []
            for cid, hrs in course_hours.items():
                pool += [cid] * hrs
            random.shuffle(pool)
            all_indices = list(range(self.slots))
            random.shuffle(all_indices)
            for cid in pool:
                if not all_indices:
                    break
                idx = all_indices.pop()
                t.set_assignment(idx, cid)
            self.individuals.append(t)

    def best(self, fitnesses: List[float]):
        best_idx = min(range(len(fitnesses)), key=lambda i: fitnesses[i])
        return self.individuals[best_idx], fitnesses[best_idx]
