class Course:
    def __init__(self, name, department, weekly_hours, course_type='lecture', level=1, group=1):
        self.name = name
        self.department = department
        self.weekly_hours = weekly_hours
        self.course_type = course_type
        self.level = level
        self.group = group
        
    def __repr__(self):
        return f"Course({self.name}, L{self.level}G{self.group}, {self.weekly_hours}h)"
    
    def get_level_group_id(self):
        """Returns the level-group identifier (e.g., 'L1G1')"""
        return f"L{self.level}G{self.group}"
    
    def to_dict(self):
        return {
            'name': self.name,
            'department': self.department,
            'weekly_hours': self.weekly_hours,
            'type': self.course_type,
            'level': self.level,
            'group': self.group,
            'level_group_id': self.get_level_group_id()
        }