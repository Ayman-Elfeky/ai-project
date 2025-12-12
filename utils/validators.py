class Validator:
    """Validates user inputs."""
    
    @staticmethod
    def validate_courses(courses):
        if not courses:
            return False, "At least one course is required"
        
        for course in courses:
            if not course.name or not course.department:
                return False, "Course name and department are required"
            if course.weekly_hours <= 0:
                return False, "Weekly hours must be positive"
        
        return True, "Valid"
    
    @staticmethod
    def validate_lecturers(lecturers):
        if not lecturers:
            return False, "At least one lecturer is required"
        
        for lecturer in lecturers:
            if not lecturer.name:
                return False, "Lecturer name is required"
        
        return True, "Valid"
    
    @staticmethod
    def validate_rooms(rooms):
        if not rooms:
            return False, "At least one room is required"
        
        for room in rooms:
            if not room.name:
                return False, "Room name is required"
            if room.capacity <= 0:
                return False, "Room capacity must be positive"
        
        return True, "Valid"
    
    @staticmethod
    def validate_all(courses, lecturers, rooms, time_slots):
        valid, msg = Validator.validate_courses(courses)
        if not valid:
            return False, msg
        
        valid, msg = Validator.validate_lecturers(lecturers)
        if not valid:
            return False, msg
        
        valid, msg = Validator.validate_rooms(rooms)
        if not valid:
            return False, msg
        
        if not time_slots:
            return False, "Time slots must be generated"
        
        return True, "All inputs valid"