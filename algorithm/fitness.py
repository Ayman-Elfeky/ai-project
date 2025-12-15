from collections import defaultdict

class FitnessEvaluator:
    def __init__(self, hard_weight=1000, soft_weight=1):
        self.hard_weight = hard_weight
        self.soft_weight = soft_weight
        
    def evaluate(self, timetable):
        hard_violations = self._count_hard_violations(timetable)
        soft_violations = self._count_soft_violations(timetable)
        
        penalty = (hard_violations * self.hard_weight + 
                   soft_violations * self.soft_weight)
            
        fitness = 1 / (1 + penalty)
        
        
        timetable.fitness = fitness
        return fitness, hard_violations, soft_violations
    
    def _count_hard_violations(self, timetable):
        violations = 0
        
        lecturer_schedule = defaultdict(list)
        room_schedule = defaultdict(list)
        group_schedule = defaultdict(list)
        
        for entry in timetable.entries:
            time_key = (entry.time_slot.day, entry.time_slot.hour)
            
            lecturer_schedule[time_key].append(entry.lecturer)
            room_schedule[time_key].append(entry.room)
            # Use level-group ID for scheduling conflicts
            group_key = f"{entry.course.get_level_group_id()}_{entry.course.course_type}"
            group_schedule[time_key].append(group_key)
            
            # Room type compatibility
            if entry.course.course_type != entry.room.room_type:
                violations += 1
            
            # Lecturer availability
            if not entry.lecturer.is_available(entry.time_slot.day, entry.time_slot.hour):
                violations += 1
            
            # Room availability 
            if not entry.room.is_available(entry.time_slot.day, entry.time_slot.hour):
                violations += 1
                
            # Lecturer qualification check
            if (hasattr(entry.lecturer, 'qualified_courses') and 
                entry.lecturer.qualified_courses and 
                entry.course.name not in entry.lecturer.qualified_courses):
                violations += 1
        
        for lecturers in lecturer_schedule.values():
            if len(lecturers) != len(set([l.name for l in lecturers])):
                violations += len(lecturers) - len(set([l.name for l in lecturers]))
        
        for rooms in room_schedule.values():
            if len(rooms) != len(set([r.name for r in rooms])):
                violations += len(rooms) - len(set([r.name for r in rooms]))
        
        for groups in group_schedule.values():
            if len(groups) != len(set(groups)):
                violations += len(groups) - len(set(groups))
        
        # Group courses by name and type to handle duplicates
        course_hours = defaultdict(int)
        for entry in timetable.entries:
            course_key = f"{entry.course.name}_{entry.course.course_type}"
            course_hours[course_key] += 1
        
        # Check each unique course requirement
        unique_courses = {}
        for course in timetable.courses:
            course_key = f"{course.name}_{course.course_type}"
            if course_key not in unique_courses:
                unique_courses[course_key] = course.weekly_hours
            else:
                unique_courses[course_key] += course.weekly_hours
        
        for course_key, required_hours in unique_courses.items():
            actual_hours = course_hours.get(course_key, 0)
            if actual_hours != required_hours:
                violations += abs(actual_hours - required_hours)
        
        return violations
    
    def _count_soft_violations(self, timetable):
        """Count soft constraint violations."""
        violations = 0
        
        daily_schedule = defaultdict(lambda: defaultdict(list))
        
        for entry in timetable.entries:
            daily_schedule[entry.course.name][entry.time_slot.day].append(entry.time_slot.hour)
        
        late_hour_threshold = 16
        for entry in timetable.entries:
            hour = int(entry.time_slot.hour.split(':')[0])
            if hour >= late_hour_threshold:
                violations += 1
        
        for course_name, days in daily_schedule.items():
            for day, hours in days.items():
                sorted_hours = sorted([int(h.split(':')[0]) for h in hours])
                consecutive = 1
                for i in range(1, len(sorted_hours)):
                    if sorted_hours[i] == sorted_hours[i-1] + 1:
                        consecutive += 1
                        if consecutive > 2:
                            violations += 1
                    else:
                        consecutive = 1
        
        for course_name, days in daily_schedule.items():
            if len(days) < 2:
                violations += 2 - len(days)
        
        lecturer_load = defaultdict(int)
        for entry in timetable.entries:
            lecturer_load[entry.lecturer.name] += 1
        
        if lecturer_load:
            avg_load = sum(lecturer_load.values()) / len(lecturer_load)
            for load in lecturer_load.values():
                if abs(load - avg_load) > 3:
                    violations += 1
        
        return violations