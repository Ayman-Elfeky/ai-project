
import random
from typing import Dict, List, Optional
from .population import Population
from .evaluation import fitness, fitness_components
from .operators import crossover, mutate_swap, influence_from_belief, repair_hours, mutate_compact
from .belief_space import BeliefSpace

def run_cultural_algorithm(
    course_hours: Dict[str, int],
    population_size: int = 50,
    generations: int = 200,
    slots: int = 40,
    slot_meta: Optional[List[dict]] = None,
    course_room_capacity: Optional[Dict[str, int]] = None,
    class_size: Optional[int] = None,
    elite_fraction: float = 0.2,
) -> dict:
    if slot_meta is None:
        slot_meta = [{} for _ in range(slots)]

    pop = Population(population_size, slots, slot_meta)
    pop.initialize(list(course_hours.keys()), course_hours)
    belief = BeliefSpace()

    best_history: List[float] = []
    comps_history: List[dict] = []
    minus_baseline: List[float] = []
    capacity_baseline: Optional[float] = None

    for gen in range(generations):
        fitnesses = [
            fitness(ind, course_hours, course_room_capacity=course_room_capacity, class_size=class_size)
            for ind in pop.individuals
        ]

        best_ind, best_score = pop.best(fitnesses)
        belief.update(best_ind, best_score)
        comps = fitness_components(best_ind, course_hours, course_room_capacity, class_size)
        best_history.append(float(best_score))
        comps_history.append(comps)

        if gen == 0:
            capacity_baseline = comps.get("capacity", 0.0)
        minus_baseline.append(float(best_score) - float(capacity_baseline or 0.0))

        n_elite = max(1, int(population_size * elite_fraction))
        ranked = sorted(zip(pop.individuals, fitnesses), key=lambda x: x[1])
        elites = [x[0] for x in ranked[:n_elite]]

        new_inds: List = list(elites)
        while len(new_inds) < population_size:
            a = random.choice(elites)
            b = random.choice(pop.individuals)
            c1, c2 = crossover(a, b)
            c1 = mutate_swap(c1, rate=0.02)
            c2 = mutate_swap(c2, rate=0.02)
            c1 = mutate_compact(c1, rate=0.10)
            c2 = mutate_compact(c2, rate=0.10)
            c1 = repair_hours(c1, course_hours)
            c2 = repair_hours(c2, course_hours)
            if belief.situational_best is not None:
                c1 = influence_from_belief(c1, belief.situational_best, influence_rate=0.05)
                c2 = influence_from_belief(c2, belief.situational_best, influence_rate=0.05)
            new_inds.append(c1)
            if len(new_inds) < population_size:
                new_inds.append(c2)

        pop.individuals = new_inds

        if belief.situational_best_score == 0.0:
            break

    return {
        'best_timetable': belief.situational_best,
        'best_score': belief.situational_best_score,
        'history': best_history,
        'history_components': comps_history,
        'history_minus_baseline': minus_baseline,
        'capacity_baseline': capacity_baseline,
    }
