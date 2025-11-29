import random
from typing import Dict, List
from .population import Population
from .evaluation import fitness
from .operators import crossover, mutate_swap, influence_from_belief
from .belief_space import BeliefSpace


def run_cultural_algorithm(course_hours: Dict[str, int], population_size: int = 50, generations: int = 200,
						   slots: int = 40, elite_fraction: float = 0.2) -> dict:
	"""Run a simple Cultural Algorithm to allocate course hours into `slots`.

	Returns a dictionary with best timetable and metadata.
	"""
	pop = Population(population_size, slots)
	pop.initialize(list(course_hours.keys()), course_hours)
	belief = BeliefSpace()

	best_history = []

	for gen in range(generations):
		fitnesses = [fitness(ind, course_hours) for ind in pop.individuals]
		# update belief with best
		best_ind, best_score = pop.best(fitnesses)
		belief.update(best_ind, best_score)
		best_history.append(best_score)

		# selection: keep elites
		n_elite = max(1, int(population_size * elite_fraction))
		ranked = sorted(zip(pop.individuals, fitnesses), key=lambda x: x[1])
		elites = [x[0] for x in ranked[:n_elite]]

		# create next generation
		new_inds = list(elites)
		while len(new_inds) < population_size:
			a = random.choice(elites)
			b = random.choice(pop.individuals)
			c1, c2 = crossover(a, b)
			c1 = mutate_swap(c1, rate=0.02)
			c2 = mutate_swap(c2, rate=0.02)
			# influence from belief
			if belief.situational_best is not None:
				c1 = influence_from_belief(c1, belief.situational_best, influence_rate=0.05)
				c2 = influence_from_belief(c2, belief.situational_best, influence_rate=0.05)
			new_inds.append(c1)
			if len(new_inds) < population_size:
				new_inds.append(c2)

		pop.individuals = new_inds

		# early stop
		if belief.situational_best_score == 0.0:
			break

	return {
		'best_timetable': belief.situational_best,
		'best_score': belief.situational_best_score,
		'history': best_history,
	}

