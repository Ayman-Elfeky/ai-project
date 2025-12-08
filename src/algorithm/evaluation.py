
from typing import Dict, Optional
from src.models.timetable import Timetable

def fitness(
    t: Timetable,
    course_hours_required: Dict[str, int],
    course_room_capacity: Optional[Dict[str, int]] = None,
    class_size: Optional[int] = None,
    gap_penalty_weight: float = 10.0,
    capacity_penalty_base: float = 300.0,
    capacity_penalty_per_student: float = 5.0,
    adjacency_bonus_weight: float = 0.5,
) -> float:
    comps = fitness_components(
        t, course_hours_required, course_room_capacity, class_size,
        gap_penalty_weight, capacity_penalty_base, capacity_penalty_per_student, adjacency_bonus_weight
    )
    return comps["total"]

def fitness_components(
    t: Timetable,
    course_hours_required: Dict[str, int],
    course_room_capacity: Optional[Dict[str, int]] = None,
    class_size: Optional[int] = None,
    gap_penalty_weight: float = 10.0,
    capacity_penalty_base: float = 300.0,
    capacity_penalty_per_student: float = 5.0,
    adjacency_bonus_weight: float = 0.5,
):
    hours_mismatch = 0.0
    assigned_counts = t.count_course_hours()
    for cid, req in course_hours_required.items():
        assigned = assigned_counts.get(cid, 0)
        hours_mismatch += abs(req - assigned) * 100.0

    empties = t.empty_slots() * 0.5

    cap_pen = 0.0
    if class_size is not None and course_room_capacity is not None:
        for cid in t.assignments:
            if cid is None:
                continue
            capacity = course_room_capacity.get(cid)
            if capacity is not None and class_size > capacity:
                overflow = class_size - capacity
                cap_pen += capacity_penalty_base + capacity_penalty_per_student * overflow

    gaps = t.internal_day_gaps()
    gaps_pen = gaps * gap_penalty_weight

    runs = t.adjacency_runs()
    adj_bonus = -adjacency_bonus_weight * runs

    total = hours_mismatch + empties + cap_pen + gaps_pen + adj_bonus
    return {
        "total": float(total),
        "hours_mismatch": float(hours_mismatch),
        "empties": float(empties),
        "capacity": float(cap_pen),
        "gaps_pen": float(gaps_pen),
        "adj_bonus": float(adj_bonus),
        "gaps": int(gaps),
        "runs": int(runs),
    }
