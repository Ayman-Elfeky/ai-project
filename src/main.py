import csv
import os
from typing import Dict, List

from algorithm.algorithm import run_cultural_algorithm
from models.event import Lecturer, Course

def load_time_slots(path: str) -> List[Dict[str, str]]:
    slots = []
    if not os.path.exists(path):
        return slots
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize keys and keep as strings
            slots.append({
                'slot_id': row.get('slot_id') or row.get('id') or '',
                'day': row.get('day') or '',
                'period': row.get('period') or '',
                'start_time': row.get('start_time') or '',
                'end_time': row.get('end_time') or '',
            })
    return slots

def load_lecturers(path: str) -> List[Lecturer]:
	lecturers = []
	if not os.path.exists(path):
		return lecturers
	with open(path, newline='', encoding='utf-8') as f:
		reader = csv.DictReader(f)
		for row in reader:
			lecturers.append(Lecturer(id=row.get('id') or row.get('Id') or row.get('ID'), name=row.get('name') or row.get('Name') or row.get('name')))
	return lecturers


def load_courses(path: str, lecturers: List[Lecturer]) -> List[Course]:
	courses = []
	if not os.path.exists(path):
		# create fallback: one course per lecturer
		for i, lec in enumerate(lecturers):
			courses.append(Course(id=f'C{i+1}', name=f'Course_{i+1}', hours_per_week=3, lecturer_id=lec.id))
		return courses



	with open(path, newline='', encoding='utf-8') as f:
		reader = csv.DictReader(f)
		for row in reader:
			cid = row.get('id') or row.get('Id') or row.get('ID') or row.get('course_id')
			name = row.get('name') or row.get('Name') or row.get('course_name')
			hrs = int(row.get('hours') or row.get('hours_per_week') or 3)
			courses.append(Course(id=cid, name=name, hours_per_week=hrs))
	return courses


def main():
	base = os.path.join(os.path.dirname(__file__), '..', 'data')
	data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
	lecturers = load_lecturers(os.path.join(data_dir, 'lecturers.csv'))
	courses = load_courses(os.path.join(data_dir, 'courses.csv'), lecturers)

	# build course_hours mapping
	course_hours = {c.id or c.name: c.hours_per_week for c in courses}

	# load time slots and set slots count from file
	time_slots = load_time_slots(os.path.join(data_dir, 'time-slots.csv'))
	slots_count = len(time_slots) if len(time_slots) > 0 else 40

	print(f'Loaded {len(lecturers)} lecturers, {len(courses)} courses and {slots_count} time slots')

	res = run_cultural_algorithm(course_hours, population_size=60, generations=300, slots=slots_count)
	best = res['best_timetable']
	score = res['best_score']
	print(f'Best score: {score}')

	# write output CSV
	out_path = os.path.join(data_dir, 'output_timetable.csv')
	with open(out_path, 'w', newline='', encoding='utf-8') as f:
		writer = csv.writer(f)
		writer.writerow(['slot_id', 'day', 'period', 'start_time', 'end_time', 'course_id'])
		assignments = best.assignments if best is not None else [None] * slots_count
		for i in range(slots_count):
			meta = time_slots[i] if i < len(time_slots) else {'slot_id': i, 'day': '', 'period': '', 'start_time': '', 'end_time': ''}
			cid = assignments[i] if i < len(assignments) else ''
			writer.writerow([meta.get('slot_id', i), meta.get('day', ''), meta.get('period', ''), meta.get('start_time', ''), meta.get('end_time', ''), cid or ''])

	print(f'Output written to {out_path}')


if __name__ == '__main__':
	main()

