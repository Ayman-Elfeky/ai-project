class Room:
    """Represents a room in the facility."""
    
    def __init__(self, name, capacity, room_type='lecture', availability=None):
        self.name = name
        self.capacity = capacity
        self.room_type = room_type
        self.availability = availability or {}
        
    def is_available(self, day, hour):
        if not self.availability:
            return True
        return day in self.availability and hour in self.availability[day]
    
    def __repr__(self):
        return f"Room({self.name}, {self.capacity})"
    
    def to_dict(self):
        return {
            'name': self.name,
            'capacity': self.capacity,
            'type': self.room_type,
            'availability': self.availability
        }
