import random
from src.models.timetable import Timetable
from typing import Tuple


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


def influence_from_belief(ind: Timetable, belief_best: Timetable, influence_rate: float = 0.1) -> Timetable:
	"""Bias an individual toward the belief best: copy some slots from belief_best."""
	t = ind.copy()
	for i in range(t.slots):
		if belief_best.assignments[i] is not None and random.random() < influence_rate:
			t.assignments[i] = belief_best.assignments[i]
	return t

