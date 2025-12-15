import json
import pandas as pd

class FileHandler:
    """Handles file imports and exports."""
    
    @staticmethod
    def import_courses_csv(file):
        from models.course import Course
        df = pd.read_csv(file)
        courses = []
        for _, row in df.iterrows():
            course = Course(
                name=row['name'],
                department=row['department'],
                weekly_hours=int(row['weekly_hours']),
                course_type=row.get('type', 'lecture'),
                level=int(row.get('level', 1)),
                group=int(row.get('group', 1))
            )
            courses.append(course)
        return courses
    
    @staticmethod
    def import_lecturers_csv(file):
        from models.lecturer import Lecturer
        df = pd.read_csv(file)
        lecturers = []
        for _, row in df.iterrows():
            # Parse qualified courses
            qualified_courses = []
            if 'qualified_courses' in row and pd.notna(row['qualified_courses']):
                qualified_courses = [course.strip() for course in str(row['qualified_courses']).split(';')]
            
            # Parse availability
            availability = {}
            if 'availability' in row and pd.notna(row['availability']):
                availability_str = str(row['availability'])
                for day_schedule in availability_str.split(';'):
                    if ':' in day_schedule:
                        day, time_range = day_schedule.split(':', 1)
                        day = day.strip()
                        start_time, end_time = time_range.split('-')
                        
                        # Convert time range to list of hours
                        start_hour = int(start_time.split(':')[0])
                        end_hour = int(end_time.split(':')[0])
                        
                        availability[day] = []
                        for hour in range(start_hour, end_hour + 1):
                            availability[day].append(f"{hour:02d}:00")
            
            lecturer = Lecturer(
                name=row['name'],
                email=row['email'],
                qualified_courses=qualified_courses,
                availability=availability
            )
            lecturers.append(lecturer)
        return lecturers
    
    @staticmethod
    def import_rooms_csv(file):
        from models.room import Room
        df = pd.read_csv(file)
        rooms = []
        for _, row in df.iterrows():
            # Parse availability
            availability = {}
            if 'availability' in row and pd.notna(row['availability']):
                availability_str = str(row['availability'])
                for day_schedule in availability_str.split(';'):
                    if ':' in day_schedule:
                        day, time_range = day_schedule.split(':', 1)
                        day = day.strip()
                        start_time, end_time = time_range.split('-')
                        
                        # Convert time range to list of hours
                        start_hour = int(start_time.split(':')[0])
                        end_hour = int(end_time.split(':')[0])
                        
                        availability[day] = []
                        for hour in range(start_hour, end_hour + 1):
                            availability[day].append(f"{hour:02d}:00")
            
            room = Room(
                name=row['name'],
                capacity=int(row['capacity']),
                room_type=row.get('type', 'lecture'),
                availability=availability
            )
            rooms.append(room)
        return rooms
    
    @staticmethod
    def export_timetable_json(timetable, filename='timetable_result.json'):
        data = {
            'timetable': timetable.to_dict_list(),
            'fitness': timetable.fitness
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    @staticmethod
    def export_timetable_csv(timetable, filename='timetable_result.csv'):
        df = pd.DataFrame(timetable.to_dict_list())
        df.to_csv(filename, index=False)