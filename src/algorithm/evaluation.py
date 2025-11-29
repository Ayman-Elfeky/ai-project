from typing import Dict
from src.models.timetable import Timetable


def fitness(t: Timetable, course_hours_required: Dict[str, int]) -> float:
	"""Lower is better. Penalize deviation from required hours and reward fewer empty slots."""

	fitness = 0.0
	assigned_counts = t.count_course_hours()
	# Penalize mismatch in hours
	for cid, req in course_hours_required.items():
		assigned = assigned_counts.get(cid, 0)
		fitness += abs(req - assigned) * 100.0

	# small penalty for empty slots (we prefer filling required hours)
	fitness += t.empty_slots() * 1.0

	return fitness

