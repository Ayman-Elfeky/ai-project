
import csv
import os
from typing import Dict, List, Optional
from src.algorithm.algorithm import run_cultural_algorithm
from src.models.event import Lecturer, Course, Room

def load_time_slots(path: str) -> List[Dict[str, str]]:
    slots: List[Dict[str, str]] = []
    if not os.path.exists(path):
        return slots
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            slots.append({
                'slot_id': row.get('slot_id') or row.get('id') or '',
                'day': row.get('day') or '',
                'period': row.get('period') or row.get('order') or '',
                'start_time': row.get('start_time') or '',
                'end_time': row.get('end_time') or '',
            })
    return slots

def auto_generate_slots(days=None, periods_per_day=8, start_hour=8, slot_minutes=60):
    if days is None:
        days = ['Sunday','Monday','Tuesday','Wednesday','Thursday']
    slots = []
    for d in days:
        for p in range(1, periods_per_day+1):
            start = f"{start_hour + (p-1):02d}:00"
            end = f"{start_hour + p:02d}:00"
            slots.append({
                'slot_id': f"{d[:2]}_{p}",
                'day': d,
                'period': p,
                'start_time': start,
                'end_time': end
            })
    return slots

def load_lecturers(path: str) -> List[Lecturer]:
    lecturers: List[Lecturer] = []
    if not os.path.exists(path):
        return lecturers
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            lecturers.append(
                Lecturer(
                    id=row.get('id') or row.get('Id') or row.get('ID'),
                    name=row.get('name') or row.get('Name') or row.get('name'),
                )
            )
    return lecturers

def load_rooms(path: str) -> Dict[str, Room]:
    rooms: Dict[str, Room] = {}
    if not os.path.exists(path):
        return rooms
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rid = row.get('room_id') or row.get('id') or row.get('Room')
            name = row.get('name') or rid or ''
            cap = row.get('capacity')
            try:
                cap = int(cap) if cap not in (None, '') else None
            except Exception:
                cap = None
            if rid:
                rooms[str(rid)] = Room(id=str(rid), name=name, capacity=cap)
    return rooms

def load_courses(path: str, lecturers: List[Lecturer]) -> List[Course]:
    courses: List[Course] = []
    if not os.path.exists(path):
        for i, lec in enumerate(lecturers):
            courses.append(Course(id=f'C{i+1}', name=f'Course_{i+1}', hours_per_week=3, lecturer_id=lec.id))
        return courses
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row.get('id') or row.get('Id') or row.get('ID') or row.get('course_id')
            name = row.get('name') or row.get('Name') or row.get('course_name') or str(cid)
            hrs = int(row.get('hours') or row.get('hours_per_week') or 3)
            lec_id = row.get('lecturer_id') or row.get('lec_id') or None
            courses.append(Course(id=str(cid), name=name, hours_per_week=hrs, lecturer_id=lec_id))
    return courses

def load_classes(path: str) -> List[Dict[str, str]]:
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def build_course_room_capacity(courses, course_room_map_csv, rooms) -> Dict[str, int]:
    mapping: Dict[str, str] = {}
    capacities: Dict[str, int] = {}
    if course_room_map_csv and os.path.exists(course_room_map_csv):
        with open(course_room_map_csv, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = row.get('course_id') or row.get('id')
                rid = row.get('room_id') or row.get('room')
                if cid and rid:
                    mapping[str(cid)] = str(rid)
    default_capacity = max((r.capacity or 0) for r in rooms.values()) if rooms else 100
    for c in courses:
        assigned_room_id = mapping.get(c.id)
        if assigned_room_id and assigned_room_id in rooms and rooms[assigned_room_id].capacity is not None:
            capacities[c.id] = int(rooms[assigned_room_id].capacity)
        else:
            capacities[c.id] = int(default_capacity)
    return capacities

def main():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
    lecturers = load_lecturers(os.path.join(data_dir, 'lecturers.csv'))
    courses = load_courses(os.path.join(data_dir, 'courses.csv'), lecturers)
    course_hours = {c.id or c.name: c.hours_per_week for c in courses}
    required_total = sum(course_hours.values())

    rooms = load_rooms(os.path.join(data_dir, 'rooms.csv'))
    classes_rows = load_classes(os.path.join(data_dir, 'classes.csv'))
    # Select the first class if multiple; you can change this ID here
    class_size = 30
    if classes_rows:
        try:
            class_size = int(classes_rows[0].get('students') or classes_rows[0].get('size') or 30)
        except Exception:
            class_size = 30

    time_slots = load_time_slots(os.path.join(data_dir, 'time-slots.csv'))
    # Validate slots
    slots_count = len(time_slots)
    if slots_count < required_total or not all(('day' in s and 'period' in s) for s in time_slots):
        print(f"[WARN] time-slots.csv invalid or too few slots ({slots_count}) for required hours ({required_total}). Auto-generating 40 slots.")
        time_slots = auto_generate_slots()
        slots_count = len(time_slots)
    slot_meta = time_slots

    course_room_capacity = build_course_room_capacity(
        courses,
        course_room_map_csv=os.path.join(data_dir, 'course-rooms.csv'),
        rooms=rooms,
    )

    print(f'Loaded {len(lecturers)} lecturers, {len(courses)} courses and {slots_count} time slots')
    print(f'Required total hours: {required_total}, Class size: {class_size}')
    res = run_cultural_algorithm(
        course_hours,
        population_size=60,
        generations=300,
        slots=slots_count,
        slot_meta=slot_meta,
        course_room_capacity=course_room_capacity,
        class_size=class_size,
        elite_fraction=0.2,
    )

    best = res['best_timetable']
    score = res['best_score']
    print(f'Best score: {score:.3f}')

    # Print decomposition every ~20 generations
    comps_hist = res.get('history_components', [])
    if comps_hist:
        for gen in range(0, len(comps_hist), 20):
            c = comps_hist[gen]
            print(f"[gen {gen}] total={c['total']:.3f} | mismatch={c['hours_mismatch']:.3f} "
                  f"| cap={c['capacity']:.3f} | gaps_pen={c['gaps_pen']:.3f} "
                  f"| empties={c['empties']:.3f} | adj_bonus={c['adj_bonus']:.3f} "
                  f"| gaps={c['gaps']} | runs={c['runs']}")

    out_path = os.path.join(data_dir, 'output_timetable.csv')
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['slot_id', 'day', 'period', 'start_time', 'end_time', 'course_id'])
        assignments = best.assignments if best is not None else [None] * slots_count
        for i in range(slots_count):
            meta = time_slots[i] if i < len(time_slots) else {'slot_id': i, 'day': '', 'period': '', 'start_time': '', 'end_time': ''}
            cid = assignments[i] if i < len(assignments) else ''
            writer.writerow([
                meta.get('slot_id', i), meta.get('day', ''), meta.get('period', ''),
                meta.get('start_time', ''), meta.get('end_time', ''), cid or ''
            ])
    print(f'Output written to {out_path}')

if __name__ == '__main__':
    main()
