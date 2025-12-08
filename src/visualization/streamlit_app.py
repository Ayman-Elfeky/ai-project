
import io
import os
import sys
from typing import Dict
import numpy as np
import pandas as pd
import streamlit as st

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.algorithm.algorithm import run_cultural_algorithm

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))

def load_df(uploaded, default_filename):
    if uploaded is not None:
        try:
            return pd.read_csv(uploaded)
        except Exception:
            uploaded.seek(0)
            return pd.read_csv(io.StringIO(uploaded.getvalue().decode('utf-8')))
    path = os.path.join(DATA_DIR, default_filename)
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode('utf-8')

def auto_generate_slots(days=None, periods_per_day=8, start_hour=8, slot_minutes=60):
    if days is None:
        days = ['Sunday','Monday','Tuesday','Wednesday','Thursday']
    rows = []
    for d in days:
        for p in range(1, periods_per_day+1):
            start = f"{start_hour + (p-1):02d}:00"
            end = f"{start_hour + p:02d}:00"
            rows.append({
                'slot_id': f"{d[:2]}_{p}",
                'day': d,
                'period': p,
                'start_time': start,
                'end_time': end
            })
    return pd.DataFrame(rows)

def main():
    st.title('Timetable Scheduler — Cultural Algorithm')
    st.sidebar.header('Inputs')
    up_lect = st.sidebar.file_uploader('Upload `lecturers.csv`', type=['csv'], key='lect')
    up_courses = st.sidebar.file_uploader('Upload `courses.csv`', type=['csv'], key='courses')
    up_rooms = st.sidebar.file_uploader('Upload `rooms.csv`', type=['csv'], key='rooms')
    up_classes = st.sidebar.file_uploader('Upload `classes.csv`', type=['csv'], key='classes')
    up_slots = st.sidebar.file_uploader('Upload `time-slots.csv`', type=['csv'], key='slots')
    up_course_rooms = st.sidebar.file_uploader('Upload optional `course-rooms.csv` (course_id,room_id)', type=['csv'], key='course_rooms')

    st.sidebar.markdown('---')
    population_size = st.sidebar.number_input('Population size', min_value=4, max_value=1000, value=60)
    generations = st.sidebar.number_input('Generations', min_value=1, max_value=5000, value=300)
    elite_fraction = st.sidebar.slider('Elite fraction', 0.0, 0.9, 0.2)

    df_lecturers = load_df(up_lect, 'lecturers.csv')
    df_courses = load_df(up_courses, 'courses.csv')
    df_rooms = load_df(up_rooms, 'rooms.csv')
    df_classes = load_df(up_classes, 'classes.csv')
    df_slots = load_df(up_slots, 'time-slots.csv')
    df_course_rooms = load_df(up_course_rooms, 'course-rooms.csv')

    st.header('Data Preview (editable)')
    st.subheader('Lecturers'); df_lecturers = st.data_editor(df_lecturers, num_rows='dynamic')
    st.subheader('Courses'); df_courses = st.data_editor(df_courses, num_rows='dynamic')
    st.subheader('Rooms'); df_rooms = st.data_editor(df_rooms, num_rows='dynamic')
    st.subheader('Classes'); df_classes = st.data_editor(df_classes, num_rows='dynamic')
    st.subheader('Time Slots'); df_slots = st.data_editor(df_slots, num_rows='dynamic')
    if not df_course_rooms.empty:
        st.subheader('Course–Room Mapping'); df_course_rooms = st.data_editor(df_course_rooms, num_rows='dynamic')

    # Choose which class to schedule
    class_choice = None
    if not df_classes.empty and 'class_id' in df_classes.columns and 'students' in df_classes.columns:
        ids = list(df_classes['class_id'].astype(str))
        class_choice = st.sidebar.selectbox('Choose class/batch', ids, index=0)
        class_size = int(df_classes[df_classes['class_id'].astype(str) == class_choice].iloc[0]['students'])
    else:
        class_size = st.sidebar.number_input('Class size (fallback)', min_value=1, value=30)

    run = st.button('Run Cultural Algorithm')
    if run:
        with st.spinner('Running algorithm...'):
            # course hours
            if 'hours_per_week' in df_courses.columns:
                ch: Dict[str, int] = {}
                for _, r in df_courses.iterrows():
                    cid = r.get('course_id') or r.get('id') or r.get('course')
                    if pd.isna(cid):
                        continue
                    try:
                        hrs = int(r.get('hours_per_week') or r.get('hours') or 1)
                    except Exception:
                        hrs = 1
                    ch[str(cid)] = hrs
            else:
                st.error('`courses.csv` must contain `course_id` and `hours_per_week` columns')
                st.stop()

            required_total = sum(ch.values())
            st.info(f"Total required course hours: **{required_total}**")

            # slot_meta validation / auto-generate
            if len(df_slots) > 0 and {'day','period'}.issubset(df_slots.columns):
                slot_meta = []
                for _, r in df_slots.iterrows():
                    slot_meta.append({
                        'slot_id': r.get('slot_id') or r.get('id') or '',
                        'day': r.get('day') or '',
                        'period': r.get('period') or r.get('order') or '',
                        'start_time': r.get('start_time') or '',
                        'end_time': r.get('end_time') or '',
                    })
                slots_count = len(slot_meta)
            else:
                st.warning('`time-slots.csv` is missing or invalid; auto-generating a 5×8 grid (40 slots).')
                df_slots = auto_generate_slots()
                slot_meta = df_slots.to_dict(orient='records')
                slots_count = len(slot_meta)

            # If slots too few, stop early (to avoid huge mismatch constant)
            if slots_count < required_total:
                st.error(f"The number of slots ({slots_count}) is less than required hours ({required_total}). "
                         f"Increase slots or reduce course hours.")
                st.stop()

            # class size already computed
            st.info(f"Using class '{class_choice}' size: **{class_size}**" if class_choice else f"Class size: **{class_size}**")

            # rooms and capacities
            room_capacity = {}
            if 'room_id' in df_rooms.columns and 'capacity' in df_rooms.columns:
                for _, r in df_rooms.iterrows():
                    rid = r.get('room_id') or r.get('id')
                    cap = r.get('capacity')
                    try:
                        room_capacity[str(rid)] = int(cap)
                    except Exception:
                        continue

            # course-room mapping
            room_cap = {}
            if not df_course_rooms.empty and {'course_id', 'room_id'}.issubset(df_course_rooms.columns):
                for _, r in df_course_rooms.iterrows():
                    cid = r.get('course_id'); rid = r.get('room_id')
                    if pd.isna(cid) or pd.isna(rid):
                        continue
                    cap = room_capacity.get(str(rid))
                    if cap is not None:
                        room_cap[str(cid)] = cap

            if not room_cap:
                default_capacity = max(room_capacity.values()) if room_capacity else 100
                for cid in ch.keys():
                    room_cap[cid] = default_capacity
                st.info(f"No course-room mapping provided; using default capacity: **{default_capacity}**")

            res = run_cultural_algorithm(
                ch,
                population_size=int(population_size),
                generations=int(generations),
                slots=int(slots_count),
                slot_meta=slot_meta,
                course_room_capacity=room_cap,
                class_size=int(class_size),
                elite_fraction=float(elite_fraction),
            )
            best = res.get('best_timetable')
            history = res.get('history', [])
            comps_history = res.get('history_components', [])
            minus_baseline = res.get('history_minus_baseline', [])
            capacity_baseline = res.get('capacity_baseline', 0.0)

            if best is None:
                st.warning('No timetable produced')
                st.stop()

            # Output timetable
            out_rows = []
            for i in range(slots_count):
                meta = slot_meta[i] if i < len(slot_meta) else {}
                cid = best.assignments[i] if i < len(best.assignments) else None
                out = {
                    'slot_index': i,
                    'slot_id': meta.get('slot_id', ''),
                    'day': meta.get('day', ''),
                    'period': meta.get('period', ''),
                    'start_time': meta.get('start_time', ''),
                    'end_time': meta.get('end_time', ''),
                    'course_id': cid or ''
                }
                out_rows.append(out)
            df_out = pd.DataFrame(out_rows)
            st.header('Resulting Timetable')
            st.dataframe(df_out)
            st.download_button('Download timetable CSV', data=to_csv_bytes(df_out),
                               file_name='output_timetable.csv', mime='text/csv')

            # Fitness visuals
            st.header('Fitness History (best per generation)')
            if history:
                st.write(f"Best (last generation): **{history[-1]:.3f}**")
            st.line_chart(np.array(history, dtype=float))

            if comps_history:
                df_comp = pd.DataFrame(comps_history)
                st.subheader('Component Breakdown (best per generation)')
                st.dataframe(df_comp.round(3))
                st.subheader('Components over generations')
                st.line_chart(df_comp[['hours_mismatch', 'capacity', 'gaps_pen', 'empties', 'adj_bonus']])

            if minus_baseline:
                st.subheader('Total minus capacity baseline (gen 0 best)')
                st.write(f"Capacity baseline (gen 0 best): **{capacity_baseline:.3f}**")
                st.line_chart(np.array(minus_baseline, dtype=float))

if __name__ == '__main__':
    main()
