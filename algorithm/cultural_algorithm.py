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
        
        # Step 2: Apply aggressive global constraint optimization
        if callback:
            callback("Phase 2: Resolving shared resource conflicts...", total_combinations, total_combinations)
        
        # Perform iterative improvement to resolve ALL global conflicts
        max_global_iterations = 15  # Increased iterations
        for iteration in range(max_global_iterations):
            # Check global constraints
            global_violations = self.global_checker.evaluate_global_constraints(all_results)
            
            # If no global violations, we're done
            if all(violations == 0 for violations in global_violations.values()):
                if callback:
                    callback(f"Global constraints resolved after {iteration + 1} iterations", total_combinations, total_combinations)
                break
            
            # Sort level-groups by violation count (worst first)
            sorted_violations = sorted(global_violations.items(), key=lambda x: x[1], reverse=True)
            
            # Regenerate multiple problematic timetables, starting with the worst
            for level_group_id, violation_count in sorted_violations:
                if violation_count > 0:
                    courses = self.level_group_courses[level_group_id]
                    
                    # Create Global-Aware Cultural Algorithm with restricted resources
                    ca = GlobalAwareCulturalAlgorithm(
                        courses=courses,
                        lecturers=self.lecturers,
                        rooms=self.rooms,
                        time_slots=self.time_slots,
                        existing_timetables={k: v for k, v in all_results.items() if k != level_group_id},
                        population_size=max(20, self.population_size // 3),
                        generations=max(50, self.generations // 2),
                        acceptance_rate=self.acceptance_rate,
                        mutation_rate=min(0.5, self.mutation_rate * 2.0)  # Much higher mutation
                    )
                    
                    # Re-run for the problematic level-group
                    best_timetable, history = ca.run()
                    all_results[level_group_id] = best_timetable
                    
                    # Update history with additional iteration info
                    if level_group_id in all_histories:
                        all_histories[level_group_id]['global_optimization_iterations'] = iteration + 1
                    
                    # Break after regenerating one at a time to check progress
                    break
        
        # Final check and report
        final_violations = self.global_checker.evaluate_global_constraints(all_results)
        total_final_violations = sum(final_violations.values())
        
        if total_final_violations > 0:
            if callback:
                callback(f"Warning: {total_final_violations} conflicts remain after optimization", total_combinations, total_combinations)
        
        self.results = all_results
        self.history = all_histories
        
        return all_results, all_histories

class GlobalAwareCulturalAlgorithm:
    """Cultural Algorithm that avoids conflicts with existing timetables."""
    
    def __init__(self, courses, lecturers, rooms, time_slots, existing_timetables=None,
                 population_size=50, generations=100, 
                 acceptance_rate=0.3, mutation_rate=0.1):
        
        from algorithm.belief_space import BeliefSpace
        from algorithm.population import PopulationManager
        from algorithm.fitness import FitnessEvaluator, GlobalAwareFitnessEvaluator
        
        self.courses = courses
        self.lecturers = lecturers
        self.rooms = rooms
        self.time_slots = time_slots
        self.existing_timetables = existing_timetables or {}
        
        self.population_size = population_size
        self.generations = generations
        self.acceptance_rate = acceptance_rate
        self.mutation_rate = mutation_rate
        
        # Build occupied resource map from existing timetables
        self.occupied_resources = self._build_occupied_resources_map()
        
        self.belief_space = BeliefSpace(rooms, time_slots)
        self.population_manager = PopulationManager(
            population_size, courses, lecturers, rooms, time_slots
        )
        self.fitness_evaluator = GlobalAwareFitnessEvaluator(self.occupied_resources)
        
        self.history = {
            'best_fitness': [],
            'avg_fitness': [],
            'hard_violations': [],
            'soft_violations': [],
            'diversity': [],
            'belief_space_updates': []
        }
    
    def _build_occupied_resources_map(self):
        """Build a map of occupied lecturers and rooms by time slot."""
        occupied = {
            'lecturers': {},  # {(day, hour): {lecturer_name}}
            'rooms': {}       # {(day, hour): {room_name}}
        }
        
        for timetable in self.existing_timetables.values():
            if hasattr(timetable, 'entries'):
                for entry in timetable.entries:
                    time_key = (entry.time_slot.day, entry.time_slot.hour)
                    
                    if time_key not in occupied['lecturers']:
                        occupied['lecturers'][time_key] = set()
                    if time_key not in occupied['rooms']:
                        occupied['rooms'][time_key] = set()
                    
                    occupied['lecturers'][time_key].add(entry.lecturer.name)
                    occupied['rooms'][time_key].add(entry.room.name)
        
        return occupied
    
    def run(self, callback=None):
        """Execute the Global-Aware Cultural Algorithm."""
        population = self.population_manager.initialize()
        
        for generation in range(self.generations):
            # Evaluate fitness for all individuals with global awareness
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
            
            # Calculate diversity
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
            
            # Create new population
            new_population = []
            
            # Keep elites
            elites = sorted(population, key=lambda x: x.fitness, reverse=True)[:2]
            new_population.extend([e.copy() for e in elites])
            
            while len(new_population) < self.population_size:
                # Tournament selection
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
