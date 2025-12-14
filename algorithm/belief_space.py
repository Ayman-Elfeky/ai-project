import numpy as np
from collections import defaultdict

class BeliefSpace:
    """Stores and updates cultural knowledge."""
    
    def __init__(self, rooms, time_slots):
        self.rooms = rooms
        self.time_slots = time_slots
        
        self.normative = {
            'room_preferences': defaultdict(list),
            'time_preferences': defaultdict(list),
            'lecturer_preferences': defaultdict(list)
        }
        
        self.situational = {
            'best_timetable': None,
            'best_fitness': float('-inf')
        }
        
        self.topographical = {
            'good_regions': [],
            'bad_regions': []
        }
        
    def update_normative(self, accepted_individuals):
        """Update normative knowledge from accepted individuals."""
        if not accepted_individuals:
            return
        
        room_usage = defaultdict(int)
        time_usage = defaultdict(int)
        lecturer_usage = defaultdict(int)
        
        for individual in accepted_individuals:
            for entry in individual.entries:
                room_usage[entry.room.name] += 1
                time_key = (entry.time_slot.day, entry.time_slot.hour)
                time_usage[time_key] += 1
                lecturer_usage[entry.lecturer.name] += 1
        
        self.normative['room_preferences'] = room_usage
        self.normative['time_preferences'] = time_usage
        self.normative['lecturer_preferences'] = lecturer_usage
        
    def update_situational(self, population):
        """Update best individual found."""
        for individual in population:
            if individual.fitness > self.situational['best_fitness']:
                self.situational['best_fitness'] = individual.fitness
                self.situational['best_timetable'] = individual.copy()
                
    def update_topographical(self, population):
        """Update knowledge about good/bad regions."""
        fitness_values = [ind.fitness for ind in population]
        median_fitness = np.median(fitness_values)
        
        good = [ind for ind in population if ind.fitness > median_fitness]
        bad = [ind for ind in population if ind.fitness <= median_fitness]
        
        if good:
            self.topographical['good_regions'] = sorted(good, key=lambda x: x.fitness, reverse=True)[:5]
        if bad:
            self.topographical['bad_regions'] = sorted(bad, key=lambda x: x.fitness)[:5]
    
    def get_best_timetable(self):
        return self.situational['best_timetable']