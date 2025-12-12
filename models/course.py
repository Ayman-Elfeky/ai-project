class Course:
    """Represents a course in the timetable."""
    
    def __init__(self, name, department, weekly_hours, course_type='lecture', group=None):
        self.name = name
        self.department = department
        self.weekly_hours = weekly_hours
        self.course_type = course_type
        self.group = group or department
        
    def __repr__(self):
        return f"Course({self.name}, {self.department}, {self.weekly_hours}h)"
    
    def to_dict(self):
        return {
            'name': self.name,
            'department': self.department,
            'weekly_hours': self.weekly_hours,
            'type': self.course_type,
            'group': self.group
        }