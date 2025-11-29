import io
import os
import sys
import pandas as pd
import streamlit as st

# Ensure project root is on sys.path so `import src.algorithm` works when Streamlit runs this file.
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


def main():
	st.title('Timetable Scheduler — Cultural Algorithm')

	st.sidebar.header('Inputs')
	up_lect = st.sidebar.file_uploader('Upload `lecturers.csv`', type=['csv'], key='lect')
	up_courses = st.sidebar.file_uploader('Upload `courses.csv`', type=['csv'], key='courses')
	up_rooms = st.sidebar.file_uploader('Upload `rooms.csv`', type=['csv'], key='rooms')
	up_classes = st.sidebar.file_uploader('Upload `classes.csv`', type=['csv'], key='classes')
	up_slots = st.sidebar.file_uploader('Upload `time-slots.csv`', type=['csv'], key='slots')

	st.sidebar.markdown('---')
	population_size = st.sidebar.number_input('Population size', min_value=4, max_value=1000, value=60)
	generations = st.sidebar.number_input('Generations', min_value=1, max_value=5000, value=300)
	elite_fraction = st.sidebar.slider('Elite fraction', 0.0, 0.9, 0.2)

	# Load dataframes (uploaded or defaults)
	df_lecturers = load_df(up_lect, 'lecturers.csv')
	df_courses = load_df(up_courses, 'courses.csv')
	df_rooms = load_df(up_rooms, 'rooms.csv')
	df_classes = load_df(up_classes, 'classes.csv')
	df_slots = load_df(up_slots, 'time-slots.csv')

	st.header('Data Preview (editable)')
	st.subheader('Lecturers')
	df_lecturers = st.data_editor(df_lecturers, num_rows='dynamic')

	st.subheader('Courses')
	df_courses = st.data_editor(df_courses, num_rows='dynamic')

	st.subheader('Rooms')
	df_rooms = st.data_editor(df_rooms, num_rows='dynamic')

	st.subheader('Classes')
	df_classes = st.data_editor(df_classes, num_rows='dynamic')

	st.subheader('Time Slots')
	df_slots = st.data_editor(df_slots, num_rows='dynamic')

	run = st.button('Run Cultural Algorithm')

	if run:
		with st.spinner('Running algorithm...'):
			# Build course_hours mapping
			if 'course_id' in df_courses.columns and 'hours_per_week' in df_courses.columns:
				ch = {}
				for _, r in df_courses.iterrows():
					cid = r.get('course_id') or r.get('id') or r.get('course')
					try:
						hrs = int(r.get('hours_per_week') or r.get('hours') or 1)
					except Exception:
						hrs = 1
					if pd.isna(cid):
						continue
					ch[str(cid)] = hrs
			else:
				st.error('`courses.csv` must contain `course_id` and `hours_per_week` columns')
				st.stop()

			slots_count = len(df_slots) if len(df_slots) > 0 else st.sidebar.number_input('Slots (fallback)', min_value=1, value=40)

			res = run_cultural_algorithm(ch, population_size=int(population_size), generations=int(generations), slots=int(slots_count), elite_fraction=float(elite_fraction))
			best = res.get('best_timetable')
			history = res.get('history', [])

			if best is None:
				st.warning('No timetable produced')
				st.stop()

			# Build output dataframe combining slot meta and assignments
			out_rows = []
			for i in range(slots_count):
				meta = df_slots.iloc[i].to_dict() if i < len(df_slots) else {}
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

			st.download_button('Download timetable CSV', data=to_csv_bytes(df_out), file_name='output_timetable.csv', mime='text/csv')

			if history:
				st.subheader('Fitness History (best per generation)')
				st.line_chart(history)


if __name__ == '__main__':
	main()

