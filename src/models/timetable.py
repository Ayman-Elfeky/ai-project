
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class Assignment:
    slot: int
    course_id: Optional[str]

class Timetable:
    """
    Timetable for one batch/class.
    Representation: list of length S (total slots) where each entry is a course id or None.
    Each slot may carry metadata: {'day': <str or int>, 'period': <int or str>, ...}
    """
    def __init__(self, slots: int, slot_meta: Optional[List[Dict[str, Any]]] = None):
        self.slots = slots
        self.assignments: List[Optional[str]] = [None] * slots
        self.slot_meta: List[Dict[str, Any]] = slot_meta if slot_meta is not None else [{} for _ in range(slots)]

    def copy(self) -> "Timetable":
        t = Timetable(self.slots, slot_meta=list(self.slot_meta))
        t.assignments = list(self.assignments)
        return t

    def set_assignment(self, slot: int, course_id: Optional[str]):
        self.assignments[slot] = course_id

    def count_course_hours(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for cid in self.assignments:
            if cid is None:
                continue
            counts[cid] = counts.get(cid, 0) + 1
        return counts

    def empty_slots(self) -> int:
        return sum(1 for s in self.assignments if s is None)

    def _day_key(self, i: int):
        meta = self.slot_meta[i] if i < len(self.slot_meta) else {}
        day = meta.get('day')
        return str(day) if day is not None else ""

    def _period_key(self, i: int):
        meta = self.slot_meta[i] if i < len(self.slot_meta) else {}
        period = meta.get('period')
        try:
            return int(period)
        except Exception:
            return i

    def daily_indices(self) -> Dict[str, List[int]]:
        by_day: Dict[str, List[int]] = {}
        for i in range(self.slots):
            day = self._day_key(i)
            by_day.setdefault(day, []).append(i)
        for day, idxs in by_day.items():
            idxs.sort(key=lambda k: self._period_key(k))
        return by_day

    def internal_day_gaps(self) -> int:
        gaps = 0
        by_day = self.daily_indices()
        for day, idxs in by_day.items():
            if not idxs:
                continue
            scheduled = [i for i in idxs if self.assignments[i] is not None]
            if not scheduled:
                continue
            first_i, last_i = scheduled[0], scheduled[-1]
            for i in idxs:
                if i <= first_i or i >= last_i:
                    continue
                if self.assignments[i] is None:
                    gaps += 1
        return gaps

    def adjacency_runs(self) -> int:
        runs = 0
        by_day = self.daily_indices()
        for _, idxs in by_day.items():
            for a, b in zip(idxs, idxs[1:]):
                if self.assignments[a] is not None and self.assignments[b] is not None:
                    runs += 1
        return runs
