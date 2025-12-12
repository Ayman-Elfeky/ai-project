class Lecturer:
    """Represents a lecturer in the system."""
    
    def __init__(self, name, email, qualified_courses=None, availability=None):
        self.name = name
        self.email = email
        self.qualified_courses = qualified_courses or []
        self.availability = availability or {}
        
    def is_available(self, day, hour):
        if not self.availability:
            return True
        return day in self.availability and hour in self.availability[day]
    
    def __repr__(self):
        return f"Lecturer({self.name})"
    
    def to_dict(self):
        return {
            'name': self.name,
            'email': self.email,
            'qualified_courses': self.qualified_courses,
            'availability': self.availability
        }