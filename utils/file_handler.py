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
            lecturer = Lecturer(
                name=row['name'],
                email=row['email']
            )
            lecturers.append(lecturer)
        return lecturers
    
    @staticmethod
    def import_rooms_csv(file):
        from models.room import Room
        df = pd.read_csv(file)
        rooms = []
        for _, row in df.iterrows():
            room = Room(
                name=row['name'],
                capacity=int(row['capacity']),
                room_type=row.get('type', 'lecture')
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