from src.models.timetable import Timetable
from typing import Optional


class BeliefSpace:
	"""Holds situational knowledge (best solution) and can be used to influence population."""

	def __init__(self):
		self.situational_best: Optional[Timetable] = None
		self.situational_best_score: float = float('inf')

	def update(self, candidate: Timetable, score: float):
		if score < self.situational_best_score:
			self.situational_best = candidate.copy()
			self.situational_best_score = score

