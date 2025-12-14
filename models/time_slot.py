class TimeSlot:
    def __init__(self, day, hour):
        self.day = day
        self.hour = hour
        
    def __eq__(self, other):
        return self.day == other.day and self.hour == other.hour
    
    def __hash__(self):
        return hash((self.day, self.hour))
    
    def __repr__(self):
        return f"TimeSlot({self.day}, {self.hour})"
    
    def to_dict(self):
        return {'day': self.day, 'hour': self.hour}