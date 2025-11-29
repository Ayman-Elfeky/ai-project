import random
from typing import List, Dict, Tuple
from src.models.timetable import Timetable


class Population:
	def __init__(self, size: int, slots: int):
		self.size = size
		self.slots = slots
		self.individuals: List[Timetable] = []

	def initialize(self, course_pool: List[str], course_hours: Dict[str, int]):
		"""Randomly initialize individuals by placing course ids into slots according to required hours."""
		self.individuals = []
		required_total = sum(course_hours.values())
		for _ in range(self.size):
			t = Timetable(self.slots)
			# create a flat list of course ids repeated by hours
			pool = []
			for cid, hrs in course_hours.items():
				pool += [cid] * hrs

			# If more slots than required hours, leave remaining None
			random.shuffle(pool)
			for i in range(min(len(pool), self.slots)):
				t.set_assignment(i, pool[i])
			# if pool shorter than slots, some remain None
			self.individuals.append(t)

	def best(self, fitnesses: List[float]):
		best_idx = min(range(len(fitnesses)), key=lambda i: fitnesses[i])
		return self.individuals[best_idx], fitnesses[best_idx]

