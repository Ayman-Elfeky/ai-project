import random
from typing import List

class TimetableEntry:
    def __init__(self, course, lecturer, room, time_slot):
        self.course = course
        self.lecturer = lecturer
        self.room = room
        self.time_slot = time_slot
        
    def __repr__(self):
        return f"Entry({self.course.name}, {self.lecturer.name}, {self.room.name}, {self.time_slot})"
    
    def to_dict(self):
        return {
            'course': self.course.name,
            'lecturer': self.lecturer.name,
            'room': self.room.name,
            'day': self.time_slot.day,
            'hour': self.time_slot.hour
        }

class Timetable:
    def __init__(self, courses, lecturers, rooms, time_slots):
        self.courses = courses
        self.lecturers = lecturers
        self.rooms = rooms
        self.time_slots = time_slots
        self.entries = []
        self.fitness = float('-inf')
        
    def initialize_random(self):
        self.entries = []
        for course in self.courses:
            for _ in range(course.weekly_hours):
                entry = TimetableEntry(
                    course=course,
                    lecturer=random.choice(self.lecturers),
                    room=random.choice(self.rooms),
                    time_slot=random.choice(self.time_slots)
                )
                self.entries.append(entry)
                
    def copy(self):
        new_tt = Timetable(self.courses, self.lecturers, self.rooms, self.time_slots)
        new_tt.entries = [TimetableEntry(e.course, e.lecturer, e.room, e.time_slot) 
                          for e in self.entries]
        new_tt.fitness = self.fitness
        return new_tt
    
    def to_dict_list(self):
        return [entry.to_dict() for entry in self.entries]
