from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass


@dataclass
class Assignment:
	slot: int
	course_id: Optional[str]


class Timetable:
	"""Simple timetable representation for one class/batch.

	Representation: list of length S (total slots) where each entry is a course id or None.
	Slot index = day * slots_per_day + slot_in_day
	"""

	def __init__(self, slots: int):
		self.slots = slots
		self.assignments: List[Optional[str]] = [None] * slots

	def copy(self) -> "Timetable":
		t = Timetable(self.slots)
		t.assignments = list(self.assignments)
		return t

	def set_assignment(self, slot: int, course_id: Optional[str]):
		self.assignments[slot] = course_id

	def count_course_hours(self) -> Dict[str, int]:
		counts = {}
		for cid in self.assignments:
			if cid is None:
				continue
			counts[cid] = counts.get(cid, 0) + 1
		return counts

	def empty_slots(self) -> int:
		return sum(1 for s in self.assignments if s is None)

