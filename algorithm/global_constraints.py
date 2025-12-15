from collections import defaultdict

class GlobalConstraintChecker:
    """Checks constraints across multiple timetables for shared resources."""
    
    def __init__(self):
        self.hard_weight = 1000
        self.soft_weight = 1
        
    def evaluate_global_constraints(self, all_timetables):
        """
        Evaluate constraints across all timetables for shared resources.
        
        Args:
            all_timetables: Dictionary of {level_group_id: timetable} pairs
            
        Returns:
            Dictionary of {level_group_id: additional_violations} for each timetable
        """
        global_violations = {lg_id: 0 for lg_id in all_timetables.keys()}
        
        # Create global schedule for shared resources
        lecturer_global_schedule = defaultdict(list)  # {(day, hour): [entries]}
        room_global_schedule = defaultdict(list)      # {(day, hour): [entries]}
        
        # Collect all entries from all timetables with their source timetable
        for level_group_id, timetable in all_timetables.items():
            if hasattr(timetable, 'entries'):
                for entry in timetable.entries:
                    time_key = (entry.time_slot.day, entry.time_slot.hour)
                    
                    # Store entry with its source level-group for tracking
                    entry_with_source = {
                        'entry': entry,
                        'source_lg': level_group_id,
                        'lecturer': entry.lecturer.name,
                        'room': entry.room.name
                    }
                    
                    lecturer_global_schedule[time_key].append(entry_with_source)
                    room_global_schedule[time_key].append(entry_with_source)
        
        # Check lecturer conflicts across timetables
        for time_key, entries in lecturer_global_schedule.items():
            lecturer_conflicts = defaultdict(list)
            
            # Group entries by lecturer
            for entry_info in entries:
                lecturer_name = entry_info['lecturer']
                lecturer_conflicts[lecturer_name].append(entry_info)
            
            # Check for conflicts (same lecturer at same time in different level-groups)
            for lecturer_name, lecturer_entries in lecturer_conflicts.items():
                if len(lecturer_entries) > 1:
                    # Lecturer conflict detected
                    conflict_penalty = len(lecturer_entries) - 1
                    
                    # Distribute penalty among conflicting timetables
                    for entry_info in lecturer_entries:
                        source_lg = entry_info['source_lg']
                        global_violations[source_lg] += conflict_penalty
        
        # Check room conflicts across timetables
        for time_key, entries in room_global_schedule.items():
            room_conflicts = defaultdict(list)
            
            # Group entries by room
            for entry_info in entries:
                room_name = entry_info['room']
                room_conflicts[room_name].append(entry_info)
            
            # Check for conflicts (same room at same time in different level-groups)
            for room_name, room_entries in room_conflicts.items():
                if len(room_entries) > 1:
                    # Room conflict detected
                    conflict_penalty = len(room_entries) - 1
                    
                    # Distribute penalty among conflicting timetables
                    for entry_info in room_entries:
                        source_lg = entry_info['source_lg']
                        global_violations[source_lg] += conflict_penalty
        
        return global_violations
    
    def get_constraint_report(self, all_timetables):
        """
        Generate a detailed report of global constraint violations.
        
        Returns:
            Dictionary with detailed conflict information
        """
        report = {
            'lecturer_conflicts': [],
            'room_conflicts': [],
            'total_conflicts': 0
        }
        
        # Create global schedule for analysis
        lecturer_global_schedule = defaultdict(list)
        room_global_schedule = defaultdict(list)
        
        # Collect all entries
        for level_group_id, timetable in all_timetables.items():
            if hasattr(timetable, 'entries'):
                for entry in timetable.entries:
                    time_key = (entry.time_slot.day, entry.time_slot.hour)
                    
                    entry_with_source = {
                        'entry': entry,
                        'source_lg': level_group_id,
                        'lecturer': entry.lecturer.name,
                        'room': entry.room.name,
                        'course': entry.course.name
                    }
                    
                    lecturer_global_schedule[time_key].append(entry_with_source)
                    room_global_schedule[time_key].append(entry_with_source)
        
        # Analyze lecturer conflicts
        for time_key, entries in lecturer_global_schedule.items():
            lecturer_groups = defaultdict(list)
            
            for entry_info in entries:
                lecturer_name = entry_info['lecturer']
                lecturer_groups[lecturer_name].append(entry_info)
            
            for lecturer_name, lecturer_entries in lecturer_groups.items():
                if len(lecturer_entries) > 1:
                    conflict = {
                        'type': 'lecturer',
                        'resource': lecturer_name,
                        'time': f"{time_key[0]} at {time_key[1]}",
                        'conflicting_assignments': []
                    }
                    
                    for entry_info in lecturer_entries:
                        conflict['conflicting_assignments'].append({
                            'level_group': entry_info['source_lg'],
                            'course': entry_info['course'],
                            'room': entry_info['room']
                        })
                    
                    report['lecturer_conflicts'].append(conflict)
                    report['total_conflicts'] += 1
        
        # Analyze room conflicts
        for time_key, entries in room_global_schedule.items():
            room_groups = defaultdict(list)
            
            for entry_info in entries:
                room_name = entry_info['room']
                room_groups[room_name].append(entry_info)
            
            for room_name, room_entries in room_groups.items():
                if len(room_entries) > 1:
                    conflict = {
                        'type': 'room',
                        'resource': room_name,
                        'time': f"{time_key[0]} at {time_key[1]}",
                        'conflicting_assignments': []
                    }
                    
                    for entry_info in room_entries:
                        conflict['conflicting_assignments'].append({
                            'level_group': entry_info['source_lg'],
                            'course': entry_info['course'],
                            'lecturer': entry_info['lecturer']
                        })
                    
                    report['room_conflicts'].append(conflict)
                    report['total_conflicts'] += 1
        
        return report