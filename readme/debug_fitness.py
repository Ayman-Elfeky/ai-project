#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.file_handler import FileHandler
from algorithm.fitness import FitnessEvaluator, GlobalAwareFitnessEvaluator
from models.timetable import Timetable
from models.time_slot import TimeSlot

def debug_fitness():
    print("=== Debugging Fitness Function ===")
    
    # Load sample data
    courses = FileHandler.import_courses_csv('data/sample_courses.csv')
    lecturers = FileHandler.import_lecturers_csv('data/sample_lecturers.csv')
    rooms = FileHandler.import_rooms_csv('data/sample_rooms.csv')
    
    print(f"\nLoaded {len(courses)} courses, {len(lecturers)} lecturers, {len(rooms)} rooms")
    
    # Check lecturer availability attributes
    print("\n=== Lecturer Details ===")
    for i, lecturer in enumerate(lecturers[:3]):
        print(f"Lecturer {i+1}: {lecturer.name}")
        print(f"  Has availability method: {hasattr(lecturer, 'is_available')}")
        if hasattr(lecturer, 'availability'):
            print(f"  Availability: {lecturer.availability}")
        else:
            print("  No availability attribute")
        
        # Test availability check
        try:
            available = lecturer.is_available('Monday', '08:00')
            print(f"  Available Monday 08:00: {available}")
        except Exception as e:
            print(f"  Availability check error: {e}")
    
    # Create a simple test timetable with known conflicts
    print("\n=== Creating Test Timetable ===")
    time_slots = [
        TimeSlot('Monday', '08:00'),
        TimeSlot('Monday', '09:00'),
        TimeSlot('Tuesday', '10:00')
    ]
    
    # Get level 1 group 1 courses for testing
    l1g1_courses = [c for c in courses if c.level == 1 and c.group == 1][:3]
    print(f"Using {len(l1g1_courses)} L1G1 courses")
    
    if l1g1_courses:
        timetable = Timetable(l1g1_courses, lecturers, rooms, time_slots)
        
        # Create entries with intentional conflicts
        from models.timetable import TimetableEntry
        
        # Same lecturer, same time - SHOULD CREATE CONFLICT
        entry1 = TimetableEntry(l1g1_courses[0], lecturers[0], rooms[0], time_slots[0])
        entry2 = TimetableEntry(l1g1_courses[1], lecturers[0], rooms[1], time_slots[0])  # Same lecturer, same time
        
        # Same room, same time - SHOULD CREATE CONFLICT  
        entry3 = TimetableEntry(l1g1_courses[2], lecturers[1], rooms[0], time_slots[0])  # Same room as entry1
        
        timetable.entries = [entry1, entry2, entry3]
        
        print("Created 3 entries with intentional conflicts:")
        for i, entry in enumerate(timetable.entries):
            print(f"  Entry {i+1}: {entry.course.name} - {entry.lecturer.name} - {entry.room.name} - {entry.time_slot.day} {entry.time_slot.hour}")
        
        # Evaluate fitness
        print("\n=== Fitness Evaluation ===")
        evaluator = FitnessEvaluator()
        fitness, hard_violations, soft_violations = evaluator.evaluate(timetable)
        
        print(f"Fitness: {fitness}")
        print(f"Hard violations: {hard_violations}")
        print(f"Soft violations: {soft_violations}")
        
        # Test global aware evaluator
        print("\n=== Global Aware Fitness Evaluation ===")
        occupied_resources = {'lecturers': {}, 'rooms': {}}
        global_evaluator = GlobalAwareFitnessEvaluator(occupied_resources)
        fitness2, hard_violations2, soft_violations2 = global_evaluator.evaluate(timetable)
        
        print(f"Global Fitness: {fitness2}")
        print(f"Global Hard violations: {hard_violations2}")
        print(f"Global Soft violations: {soft_violations2}")

if __name__ == "__main__":
    debug_fitness()