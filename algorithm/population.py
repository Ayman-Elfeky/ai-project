import random
from models.timetable import Timetable

class PopulationManager:
    """Manages population of timetables."""
    
    def __init__(self, size, courses, lecturers, rooms, time_slots):
        self.size = size
        self.courses = courses
        self.lecturers = lecturers
        self.rooms = rooms
        self.time_slots = time_slots
        self.population = []
        
    def initialize(self):
        """Create initial random population."""
        self.population = []
        for _ in range(self.size):
            timetable = Timetable(self.courses, self.lecturers, 
                                 self.rooms, self.time_slots)
            timetable.initialize_random()
            self.population.append(timetable)
        return self.population
    
    def select_accepted(self, acceptance_rate):
        """Select top individuals for acceptance."""
        sorted_pop = sorted(self.population, key=lambda x: x.fitness, reverse=True)
        n_accepted = max(1, int(len(sorted_pop) * acceptance_rate))
        return sorted_pop[:n_accepted]
    
    def mutate(self, timetable, mutation_rate, belief_space):
        """Apply mutation guided by belief space."""
        mutated = timetable.copy()
        
        for i in range(len(mutated.entries)):
            if random.random() < mutation_rate:
                entry = mutated.entries[i]
                
                mutation_type = random.choice(['room', 'time', 'lecturer'])
                
                if mutation_type == 'room':
                    room_prefs = belief_space.normative['room_preferences']
                    if room_prefs:
                        weights = [room_prefs.get(r.name, 1) for r in self.rooms]
                        entry.room = random.choices(self.rooms, weights=weights)[0]
                    else:
                        entry.room = random.choice(self.rooms)
                        
                elif mutation_type == 'time':
                    entry.time_slot = random.choice(self.time_slots)
                    
                elif mutation_type == 'lecturer':
                    entry.lecturer = random.choice(self.lecturers)
        
        return mutated
    
    def crossover(self, parent1, parent2):
        """Combine two timetables."""
        child = parent1.copy()
        crossover_point = len(child.entries) // 2
        
        child.entries[crossover_point:] = [
            parent2.entries[i] for i in range(crossover_point, len(parent2.entries))
        ]
        
        return child