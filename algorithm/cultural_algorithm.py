import random

class CulturalAlgorithm:
    """Cultural Algorithm for timetable scheduling."""
    
    def __init__(self, courses, lecturers, rooms, time_slots, 
                 population_size=50, generations=100, 
                 acceptance_rate=0.3, mutation_rate=0.1):
        
        from algorithm.belief_space import BeliefSpace
        from algorithm.population import PopulationManager
        from algorithm.fitness import FitnessEvaluator
        
        self.courses = courses
        self.lecturers = lecturers
        self.rooms = rooms
        self.time_slots = time_slots
        
        self.population_size = population_size
        self.generations = generations
        self.acceptance_rate = acceptance_rate
        self.mutation_rate = mutation_rate
        
        self.belief_space = BeliefSpace(rooms, time_slots)
        self.population_manager = PopulationManager(
            population_size, courses, lecturers, rooms, time_slots
        )
        self.fitness_evaluator = FitnessEvaluator()
        
        self.history = {
            'best_fitness': [],
            'avg_fitness': [],
            'hard_violations': [],
            'soft_violations': [],
            'diversity': [],
            'belief_space_updates': []
        }
        
    def run(self, callback=None):
        """Execute the Cultural Algorithm."""
        population = self.population_manager.initialize()
        
        for generation in range(self.generations):
            # Evaluate fitness for all individuals
            for individual in population:
                fitness, hard_v, soft_v = self.fitness_evaluator.evaluate(individual)
                individual.fitness = fitness
            
            # Select accepted individuals for belief space
            accepted = self.population_manager.select_accepted(population, self.acceptance_rate)
            self.belief_space.update_normative(accepted)
            self.belief_space.update_situational(population)
            self.belief_space.update_topographical(population)
            
            # Calculate statistics
            best_fit = max(ind.fitness for ind in population)
            avg_fit = sum(ind.fitness for ind in population) / len(population)
            best_ind = max(population, key=lambda x: x.fitness)
            _, hard_v, soft_v = self.fitness_evaluator.evaluate(best_ind)
            
            # Calculate diversity (average pairwise distance)
            diversity = self._calculate_diversity(population)
            
            # Track belief space influence
            bs_updates = len(self.belief_space.normative['room_preferences'])
            
            # Update history
            self.history['best_fitness'].append(best_fit)
            self.history['avg_fitness'].append(avg_fit)
            self.history['hard_violations'].append(hard_v)
            self.history['soft_violations'].append(soft_v)
            self.history['diversity'].append(diversity)
            self.history['belief_space_updates'].append(bs_updates)
            
            if callback:
                callback(generation + 1, self.generations, best_fit, hard_v, soft_v)
            
            new_population = []
            
            elites = sorted(population, key=lambda x: x.fitness, reverse=True)[:2]
            new_population.extend([e.copy() for e in elites])
            
            while len(new_population) < self.population_size:
                parent = random.choice(accepted)
                
                offspring = self.population_manager.mutate(
                    parent, self.mutation_rate, self.belief_space
                )
                
                if random.random() < 0.3 and self.belief_space.situational['best_timetable']:
                    offspring = self.population_manager.crossover(
                        offspring, self.belief_space.situational['best_timetable']
                    )
                
                new_population.append(offspring)
            
            population = new_population
        
        return self.belief_space.get_best_timetable(), self.history
    
    def _calculate_diversity(self, population):
        """Calculate population diversity as average Hamming distance."""
        if len(population) < 2:
            return 0
            
        total_distance = 0
        comparisons = 0
        
        for i in range(len(population)):
            for j in range(i + 1, len(population)):
                distance = self._hamming_distance(population[i], population[j])
                total_distance += distance
                comparisons += 1
                
        return total_distance / comparisons if comparisons > 0 else 0
    
    def _hamming_distance(self, timetable1, timetable2):
        """Calculate normalized Hamming distance between two timetables."""
        if len(timetable1.entries) != len(timetable2.entries):
            return 1.0
            
        differences = 0
        total_genes = len(timetable1.entries) * 4  # 4 components per entry
        
        for i in range(len(timetable1.entries)):
            entry1, entry2 = timetable1.entries[i], timetable2.entries[i]
            
            if entry1.course.name != entry2.course.name:
                differences += 1
            if entry1.lecturer.name != entry2.lecturer.name:
                differences += 1  
            if entry1.room.name != entry2.room.name:
                differences += 1
            if (entry1.time_slot.day != entry2.time_slot.day or 
                entry1.time_slot.hour != entry2.time_slot.hour):
                differences += 1
                
        return differences / total_genes
