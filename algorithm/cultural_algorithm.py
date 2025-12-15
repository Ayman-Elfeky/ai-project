import random
from collections import defaultdict
from algorithm.global_constraints import GlobalConstraintChecker

class MultiTimetableCulturalAlgorithm:
    """Cultural Algorithm for generating multiple timetables based on level-group combinations."""
    
    def __init__(self, courses, lecturers, rooms, time_slots, 
                 population_size=50, generations=100, 
                 acceptance_rate=0.3, mutation_rate=0.1):
        
        self.courses = courses
        self.lecturers = lecturers
        self.rooms = rooms
        self.time_slots = time_slots
        
        self.population_size = population_size
        self.generations = generations
        self.acceptance_rate = acceptance_rate
        self.mutation_rate = mutation_rate
        
        # Group courses by level and group
        self.level_group_courses = self._group_courses_by_level_group()
        
        # Initialize global constraint checker
        self.global_checker = GlobalConstraintChecker()
        
        self.results = {}
        self.history = {}
        
    def _group_courses_by_level_group(self):
        """Group courses by their level and group combination."""
        grouped = defaultdict(list)
        
        for course in self.courses:
            level_group_id = course.get_level_group_id()
            grouped[level_group_id].append(course)
            
        return dict(grouped)
    
    def run(self, callback=None):
        """Execute the Cultural Algorithm for all level-group combinations with global constraint optimization."""
        all_results = {}
        all_histories = {}
        
        total_combinations = len(self.level_group_courses)
        
        # Step 1: Generate initial timetables for each level-group independently
        if callback:
            callback("Phase 1: Generating initial timetables...", 0, total_combinations)
        
        for i, (level_group_id, courses) in enumerate(self.level_group_courses.items()):
            if callback:
                callback(f"Processing {level_group_id}...", i, total_combinations)
            
            # Create individual Cultural Algorithm for this level-group
            ca = CulturalAlgorithm(
                courses=courses,
                lecturers=self.lecturers,
                rooms=self.rooms,
                time_slots=self.time_slots,
                population_size=self.population_size,
                generations=self.generations,
                acceptance_rate=self.acceptance_rate,
                mutation_rate=self.mutation_rate
            )
            
            # Run algorithm for this specific level-group
            best_timetable, history = ca.run()
            
            all_results[level_group_id] = best_timetable
            all_histories[level_group_id] = history
        
        # Step 2: Apply global constraint optimization
        if callback:
            callback("Phase 2: Optimizing global constraints...", total_combinations, total_combinations)
        
        # Perform iterative improvement to resolve global conflicts
        max_global_iterations = 5
        for iteration in range(max_global_iterations):
            # Check global constraints
            global_violations = self.global_checker.evaluate_global_constraints(all_results)
            
            # If no global violations, we're done
            if all(violations == 0 for violations in global_violations.values()):
                break
            
            # Find the most problematic timetable and regenerate it
            worst_level_group = max(global_violations.keys(), key=lambda x: global_violations[x])
            
            if global_violations[worst_level_group] > 0:
                # Regenerate the most problematic timetable with modified parameters
                courses = self.level_group_courses[worst_level_group]
                
                ca = CulturalAlgorithm(
                    courses=courses,
                    lecturers=self.lecturers,
                    rooms=self.rooms,
                    time_slots=self.time_slots,
                    population_size=self.population_size // 2,  # Smaller population for faster execution
                    generations=self.generations // 2,          # Fewer generations
                    acceptance_rate=self.acceptance_rate,
                    mutation_rate=self.mutation_rate * 1.5      # Higher mutation for more diversity
                )
                
                # Re-run for the problematic level-group
                best_timetable, history = ca.run()
                all_results[worst_level_group] = best_timetable
                
                # Update history with additional iteration info
                if worst_level_group in all_histories:
                    all_histories[worst_level_group]['global_optimization_iterations'] = iteration + 1
        
        self.results = all_results
        self.history = all_histories
        
        return all_results, all_histories

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
                # Tournament selection from accepted individuals
                if len(accepted) > 1:
                    tournament_size = min(3, len(accepted))
                    tournament = random.sample(accepted, tournament_size)
                    parent = max(tournament, key=lambda x: x.fitness)
                else:
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
