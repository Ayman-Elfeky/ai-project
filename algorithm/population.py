import random
from models.timetable import Timetable, TimetableEntry

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
    
    def select_accepted(self, population, acceptance_rate):
        """Select top individuals for acceptance."""
        sorted_pop = sorted(population, key=lambda x: x.fitness, reverse=True)
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
                    # Filter rooms by course type compatibility
                    compatible_rooms = [r for r in self.rooms if r.room_type == entry.course.course_type]
                    if not compatible_rooms:
                        compatible_rooms = self.rooms
                        
                    room_prefs = belief_space.normative['room_preferences']
                    if room_prefs:
                        weights = [room_prefs.get(r.name, 1) for r in compatible_rooms]
                        entry.room = random.choices(compatible_rooms, weights=weights)[0]
                    else:
                        entry.room = random.choice(compatible_rooms)
                        
                elif mutation_type == 'time':
                    entry.time_slot = random.choice(self.time_slots)
                    
                elif mutation_type == 'lecturer':
                    # Filter lecturers by qualification if available
                    qualified_lecturers = [l for l in self.lecturers 
                                         if not hasattr(l, 'qualified_courses') or 
                                         not l.qualified_courses or 
                                         entry.course.name in l.qualified_courses]
                    if not qualified_lecturers:
                        qualified_lecturers = self.lecturers
                        
                    lect_prefs = belief_space.normative['lecturer_preferences'] 
                    if lect_prefs:
                        weights = [lect_prefs.get(l.name, 1) for l in qualified_lecturers]
                        entry.lecturer = random.choices(qualified_lecturers, weights=weights)[0]
                    else:
                        entry.lecturer = random.choice(qualified_lecturers)
        
        return mutated
    
    def crossover(self, parent1, parent2):
        """Combine two timetables using uniform crossover."""
        child = parent1.copy()
        
        # Ensure both parents have same length
        min_length = min(len(parent1.entries), len(parent2.entries))
        
        for i in range(min_length):
            if random.random() < 0.5:  # 50% chance to take from parent2
                child.entries[i] = TimetableEntry(
                    parent2.entries[i].course,
                    parent2.entries[i].lecturer, 
                    parent2.entries[i].room,
                    parent2.entries[i].time_slot
                )
        
        return child