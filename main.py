import streamlit as st
import pandas as pd
import json
from io import StringIO
from io import BytesIO
from fpdf import FPDF
import matplotlib.pyplot as plt

# Import all models
from models.course import Course
from models.lecturer import Lecturer
from models.room import Room
from models.time_slot import TimeSlot

# Import algorithm
from algorithm.cultural_algorithm import CulturalAlgorithm

# Import utilities
from utils.validators import Validator
from utils.file_handler import FileHandler
from utils.visualizer import Visualizer
from config.settings import Settings

# PAGE CONFIGURATION
st.set_page_config(
    page_title="Cultural Algorithm Scheduler",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# SESSION STATE INITIALIZATION
if 'courses' not in st.session_state:
    st.session_state.courses = []
if 'lecturers' not in st.session_state:
    st.session_state.lecturers = []
if 'rooms' not in st.session_state:
    st.session_state.rooms = []
if 'time_slots' not in st.session_state:
    st.session_state.time_slots = []
if 'results' not in st.session_state:
    st.session_state.results = None
if 'history' not in st.session_state:
    st.session_state.history = None
if "courses_uploaded" not in st.session_state:
    st.session_state.courses_uploaded = False
if "lecturers_uploaded" not in st.session_state:
    st.session_state.lecturers_uploaded = False
if "rooms_uploaded" not in st.session_state:
    st.session_state.rooms_uploaded = False
if "time_slots_uploaded" not in st.session_state:
    st.session_state.time_slots_uploaded = False

# CUSTOM CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        padding: 1rem;
        border-radius: 0.3rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 1rem;
        border-radius: 0.3rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
        padding: 1rem;
        border-radius: 0.3rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# HEADER
st.markdown('<div class="main-header">Faculty Timetable Scheduler</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Using Cultural Algorithm with Belief Space Optimization</div>', unsafe_allow_html=True)

# SIDEBAR - ALGORITHM PARAMETERS
with st.sidebar:
    st.header("Algorithm Configuration")
    
    with st.expander("Algorithm Parameters", expanded=True):
        pop_size = st.number_input(
            "Population Size",
            min_value=10,
            max_value=200,
            value=Settings.DEFAULT_POPULATION_SIZE,
            help="Number of candidate solutions in each generation"
        )
        
        generations = st.number_input(
            "Max Generations",
            min_value=10,
            max_value=500,
            value=Settings.DEFAULT_GENERATIONS,
            help="Maximum number of iterations"
        )
        
        acceptance_rate = st.slider(
            "Acceptance Rate",
            min_value=0.1,
            max_value=0.5,
            value=Settings.DEFAULT_ACCEPTANCE_RATE,
            step=0.05,
            help="Proportion of population accepted to belief space"
        )
        
        mutation_rate = st.slider(
            "Mutation Rate",
            min_value=0.01,
            max_value=0.5,
            value=Settings.DEFAULT_MUTATION_RATE,
            step=0.01,
            help="Probability of mutation per gene"
        )
    
    st.divider()
    
    # Summary
    st.subheader("Data Summary")
    st.metric("Courses", len(st.session_state.courses))
    st.metric("Lecturers", len(st.session_state.lecturers))
    st.metric("Rooms", len(st.session_state.rooms))
    st.metric("Time Slots", len(st.session_state.time_slots))
    
    st.divider()
    
    # Quick Actions
    st.subheader("Quick Actions")
    if st.button("Clear All Data", use_container_width=True):
        st.session_state.courses = []
        st.session_state.lecturers = [] 
        st.session_state.rooms = []
        st.session_state.time_slots = []
        st.session_state.results = None
        st.session_state.history = None
        st.rerun()

# MAIN CONTENT TABS
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Courses", 
    "Lecturers", 
    "Rooms", 
    "Time Slots", 
    "Results"
])

# TAB 1: COURSES
with tab1:
    st.header("Course Management")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Add New Course")
        
        with st.form("course_form", clear_on_submit=True):
            course_name = st.text_input("Course Name *", placeholder="e.g., Data Structures")
            course_dept = st.text_input("Department *", placeholder="e.g., Computer Science")
            course_hours = st.number_input("Weekly Hours *", min_value=1, max_value=10, value=2)
            course_type = st.selectbox("Type", ["lecture", "lab"])
            course_group = st.text_input("Group", placeholder="Optional, defaults to department")
            
            submitted = st.form_submit_button("Add Course", use_container_width=True)
            
            if submitted:
                if course_name and course_dept:
                    new_course = Course(
                        name=course_name,
                        department=course_dept,
                        weekly_hours=course_hours,
                        course_type=course_type,
                        group=course_group if course_group else course_dept
                    )
                    st.session_state.courses.append(new_course)
                    st.success(f"Added course: {course_name}")
                    st.rerun()
                else:
                    st.error("Please fill all required fields")
        
        st.divider()
        
        # File upload
        st.subheader("Import from File")
        uploaded_file = st.file_uploader("Upload CSV", type=['csv'], key="courses_file")
        
        if uploaded_file and not st.session_state.courses_uploaded:
            try:
                imported_courses = FileHandler.import_courses_csv(uploaded_file)
                # print("===========================",imported_courses)
                # st.session_state.courses.extend(imported_courses)
                st.session_state.courses = imported_courses
                st.session_state.courses_uploaded = True
                st.success(f"Imported {len(imported_courses)} courses")
                # st.rerun()
            except Exception as e:
                st.error(f"Error importing file: {str(e)}")
        
        with st.expander("CSV Format Example"):
            st.code("""name,department,weekly_hours,type
Data Structures,CS,3,lecture
Database Lab,CS,2,lab
Algorithms,CS,4,lecture""")
    
    with col2:
        st.subheader(f"Current Courses ({len(st.session_state.courses)})")
        
        if st.session_state.courses:
            # Display as table
            # print(st.session_state.courses)
            courses_data = [c.to_dict() for c in st.session_state.courses]
            df = pd.DataFrame(courses_data)
            
            st.dataframe(df, use_container_width=True, height=400)
            
            # Delete functionality
            st.subheader("Remove Course")
            course_to_delete = st.selectbox(
                "Select course to remove",
                options=range(len(st.session_state.courses)),
                format_func=lambda x: st.session_state.courses[x].name
            )
            
            if st.button("Remove Selected Course", type="secondary"):
                print("Are You Crazy Before:",len(st.session_state.courses))
                deleted = st.session_state.courses.pop(course_to_delete)
                print("============ HHEEHEEHEE:", deleted)
                st.success(f"Removed: {deleted.name}")
                print("Are You Crazy After:",len(st.session_state.courses))
                # st.session_state.courses = None
                st.rerun()
            
            # Export
            if st.button("Export Courses to CSV"):
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    "courses.csv",
                    "text/csv"
                )
        else:
            st.info("No courses added yet. Add courses manually or import from CSV.")

# TAB 2: LECTURERS
with tab2:
    st.header("Lecturer Management")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Add New Lecturer")
        
        with st.form("lecturer_form", clear_on_submit=True):
            lect_name = st.text_input("Lecturer Name *", placeholder="Dr. John Smith")
            lect_email = st.text_input("Email *", placeholder="john.smith@university.edu")
            
            submitted = st.form_submit_button("Add Lecturer", use_container_width=True)
            
            if submitted:
                if lect_name and lect_email:
                    new_lecturer = Lecturer(
                        name=lect_name,
                        email=lect_email
                    )
                    st.session_state.lecturers.append(new_lecturer)
                    st.success(f"Added lecturer: {lect_name}")
                    st.rerun()
                else:
                    st.error("Please fill all required fields")
        
        st.divider()
        
        # File upload
        st.subheader("Import from File")
        uploaded_file = st.file_uploader("Upload CSV", type=['csv'], key="lecturers_file")
        
        if uploaded_file and not st.session_state.lecturers_uploaded:
            try:
                imported_lecturers = FileHandler.import_lecturers_csv(uploaded_file)
                # st.session_state.lecturers.extend(imported_lecturers)
                st.session_state.lecturers = imported_lecturers
                st.session_state.lecturers_uploaded = True
                st.success(f"Imported {len(imported_lecturers)} lecturers")
                # st.rerun()
            except Exception as e:
                st.error(f"Error importing file: {str(e)}")
        
        with st.expander("CSV Format Example"):
            st.code("""name,email
Dr. John Smith,john@university.edu
Dr. Jane Doe,jane@university.edu
Prof. Bob Wilson,bob@university.edu""")
    
    with col2:
        st.subheader(f"Current Lecturers ({len(st.session_state.lecturers)})")
        
        if st.session_state.lecturers:
            lecturers_data = [l.to_dict() for l in st.session_state.lecturers]
            df = pd.DataFrame(lecturers_data)
            
            st.dataframe(df, use_container_width=True, height=400)
            
            # Delete functionality
            st.subheader("Remove Lecturer")
            lecturer_to_delete = st.selectbox(
                "Select lecturer to remove",
                options=range(len(st.session_state.lecturers)),
                format_func=lambda x: st.session_state.lecturers[x].name
            )
            
            if st.button("Remove Selected Lecturer", type="secondary"):
                deleted = st.session_state.lecturers.pop(lecturer_to_delete)
                st.success(f"Removed: {deleted.name}")
                st.rerun()
        else:
            st.info("No lecturers added yet. Add lecturers manually or import from CSV.")

# ============================================================================
# TAB 3: ROOMS
# ============================================================================
with tab3:
    st.header("Room Management")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Add New Room")
        
        with st.form("room_form", clear_on_submit=True):
            room_name = st.text_input("Room Name *", placeholder="A101")
            room_capacity = st.number_input("Capacity *", min_value=1, max_value=500, value=30)
            room_type = st.selectbox("Type", ["lecture", "lab"])
            
            submitted = st.form_submit_button("Add Room", use_container_width=True)
            
            if submitted:
                if room_name:
                    new_room = Room(
                        name=room_name,
                        capacity=room_capacity,
                        room_type=room_type
                    )
                    st.session_state.rooms.append(new_room)
                    st.success(f"Added room: {room_name}")
                    st.rerun()
                else:
                    st.error("Please fill all required fields")
        
        st.divider()
        
        # File upload
        st.subheader("Import from File")
        uploaded_file = st.file_uploader("Upload CSV", type=['csv'], key="rooms_file")
        
        if uploaded_file and not st.session_state.rooms_uploaded:
            try:
                imported_rooms = FileHandler.import_rooms_csv(uploaded_file)
                # st.session_state.rooms.extend(imported_rooms)
                st.session_state.rooms = imported_rooms
                st.session_state.rooms_uploaded = True
                st.success(f"Imported {len(imported_rooms)} rooms")
                # st.rerun()
            except Exception as e:
                st.error(f"Error importing file: {str(e)}")
        
        with st.expander("CSV Format Example"):
            st.code("""name,capacity,type
A101,50,lecture
Lab-1,30,lab
B203,100,lecture""")
    
    with col2:
        st.subheader(f"Current Rooms ({len(st.session_state.rooms)})")
        
        if st.session_state.rooms:
            rooms_data = [r.to_dict() for r in st.session_state.rooms]
            df = pd.DataFrame(rooms_data)
            
            st.dataframe(df, use_container_width=True, height=400)
            
            # Delete functionality
            st.subheader("Remove Room")
            room_to_delete = st.selectbox(
                "Select room to remove",
                options=range(len(st.session_state.rooms)),
                format_func=lambda x: st.session_state.rooms[x].name
            )
            
            if st.button("Remove Selected Room", type="secondary"):
                deleted = st.session_state.rooms.pop(room_to_delete)
                st.success(f"Removed: {deleted.name}")
                st.rerun()
        else:
            st.info("No rooms added yet. Add rooms manually or import from CSV.")


# TAB 4: TIME SLOTS 
with tab4:
    st.header("Time Slot Configuration")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Generate Time Slots")
        
        days_selected = st.multiselect(
            "Select Days",
            options=Settings.DAYS,
            default=Settings.DAYS
        )
        
        start_hour = st.number_input("Start Hour", min_value=6, max_value=20, value=8)
        end_hour = st.number_input("End Hour", min_value=7, max_value=22, value=18)
        
        if st.button("Generate Time Slots", use_container_width=True, type="primary"):
            if start_hour >= end_hour:
                st.error("End hour must be greater than start hour")
            else:
                st.session_state.time_slots = []
                for day in days_selected:
                    for hour in range(start_hour, end_hour):
                        time_slot = TimeSlot(day, f"{hour}:00")
                        st.session_state.time_slots.append(time_slot)
                
                st.success(f"Generated {len(st.session_state.time_slots)} time slots")
                st.rerun()
    
    with col2:
        st.subheader(f"Current Time Slots ({len(st.session_state.time_slots)})")
        
        if st.session_state.time_slots:
            # Group by day
            slots_by_day = {}
            for slot in st.session_state.time_slots:
                if slot.day not in slots_by_day:
                    slots_by_day[slot.day] = []
                slots_by_day[slot.day].append(slot.hour)
            
            # Display
            for day in Settings.DAYS:
                if day in slots_by_day:
                    hours = sorted(slots_by_day[day])
                    st.write(f"**{day}:** {', '.join(hours)}")
            
            if st.button("Clear Time Slots", type="secondary"):
                st.session_state.time_slots = []
                st.rerun()
        else:
            st.info("No time slots generated yet. Use the form to create time slots.")

# TAB 5: RESULTS & EXECUTION
with tab5:
    st.header("Algorithm Execution & Results")
    
    # Validation
    valid, message = Validator.validate_all(
        st.session_state.courses,
        st.session_state.lecturers,
        st.session_state.rooms,
        st.session_state.time_slots
    )
    
    if not valid:
        st.warning(f"{message}")
        st.info("Please complete the data input in the previous tabs before running the algorithm.")
    else:
        st.success("All inputs validated. Ready to run!")
        
        # Run button
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col2:
            run_button = st.button(
                "Run Algorithm",
                use_container_width=True,
                type="primary"
            )
        
        if run_button:
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            metrics_placeholder = st.empty()
            
            def progress_callback(generation, total, fitness, hard_v, soft_v):
                progress = generation / total
                progress_bar.progress(progress)
                status_text.text(f"Generation {generation}/{total}")
                
                with metrics_placeholder.container():
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Best Fitness", f"{fitness:.5f}")
                    col2.metric("Hard Violations", hard_v)
                    col3.metric("Soft Violations", soft_v)
            
            # Create and run algorithm
            with st.spinner("Running Cultural Algorithm..."):
                ca = CulturalAlgorithm(
                    courses=st.session_state.courses,
                    lecturers=st.session_state.lecturers,
                    rooms=st.session_state.rooms,
                    time_slots=st.session_state.time_slots,
                    population_size=pop_size,
                    generations=generations,
                    acceptance_rate=acceptance_rate,
                    mutation_rate=mutation_rate
                )
                
                best_timetable, history = ca.run(callback=progress_callback)
                
                st.session_state.results = best_timetable
                st.session_state.history = history
                print("========RESULTS=========")
                # print(st.session_state.results.to_dict_list())
                progress_bar.progress(1.0)
                st.success("Algorithm completed successfully!")
    
    # Display results
    if st.session_state.results:
        st.divider()
        st.subheader("Faculty Timetable Grid (Days as Rows)")

        timetable_data = st.session_state.results.to_dict_list()
        df_timetable = pd.DataFrame(timetable_data)
        # print(st.session_state.time_slots) 
        # Days of the week
        days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]

        # Get unique time slots and sort them
        time_slots = sorted(df_timetable['hour'].unique(), key=lambda x: int(x.split(':')[0]))

        # Create empty timetable DataFrame
        grid_df = pd.DataFrame("", index=days, columns=time_slots)

        # Fill the timetable
        for _, row in df_timetable.iterrows():
            day = row['day']
            hour = row['hour']
            entry = f"{row['course']} | {row['room']} | {row['lecturer']}"
            if grid_df.at[day, hour] != "":
                grid_df.at[day, hour] += "\n" + entry 
            else:
                grid_df.at[day, hour] = entry

        # Display
        st.dataframe(grid_df, use_container_width=True, height=400)
        
        
        
        # ------------- Download CSV ----------------
        csv_data = grid_df.to_csv(index=True)
        st.download_button("Download CSV", csv_data, "timetable.csv", "text/csv")

        # ------------- Download JSON ----------------
        json_data = grid_df.to_dict(orient='index')
        st.download_button("Download JSON", json.dumps(json_data, indent=2), "timetable.json", "application/json")

        # ------------- Download PDF ----------------
        def create_pdf(df):
            pdf = FPDF(orientation="L", unit="mm", format="A4")
            pdf.add_page()
            pdf.set_font("Arial", "B", 12)
            
            col_width = pdf.w / (len(df.columns) + 1)
            row_height = 10
            
            # Header row
            pdf.cell(col_width, row_height, "Day/Time", border=1, ln=0, align="C")
            for col in df.columns:
                pdf.cell(col_width, row_height, str(col), border=1, ln=0, align="C")
            pdf.ln(row_height)
            
            pdf.set_font("Arial", "", 10)
            
            for idx, row in df.iterrows():
                pdf.cell(col_width, row_height, idx, border=1)
                for item in row:
                    pdf.cell(col_width, row_height, str(item).replace("\n", " | "), border=1)
                pdf.ln(row_height)
            
            # Generate PDF as bytes
            pdf_bytes = pdf.output(dest='S').encode('latin1')  # returns bytes
            return pdf_bytes

        pdf_bytes = create_pdf(grid_df)
        st.download_button("Download PDF", pdf_bytes, "timetable.pdf", "application/pdf")

        # ------------- Download PNG ----------------
        def create_png(df):
            fig, ax = plt.subplots(figsize=(len(df.columns)*1.5, len(df.index)*0.8))
            ax.axis('tight')
            ax.axis('off')
            table = ax.table(cellText=df.values, rowLabels=df.index, colLabels=df.columns,
                            cellLoc='center', loc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.auto_set_column_width(col=list(range(len(df.columns))))
            
            png_output = BytesIO()
            plt.savefig(png_output, format='png', bbox_inches='tight')
            plt.close(fig)
            png_output.seek(0)
            return png_output

        png_file = create_png(grid_df)
        st.download_button("Download PNG", png_file, "timetable.png", "image/png")
        
        
    if st.session_state.history:
                
        st.divider()
        st.subheader("Algorithm Performance Visualization")

        history = st.session_state.history
        generations_range = range(1, len(history['best_fitness']) + 1)

        # ------------------ FITNESS PLOT ------------------
        st.markdown("### Fitness Convergence")

        fig1, ax1 = plt.subplots(figsize=(8, 4))
        ax1.plot(generations_range, history['best_fitness'], label="Best Fitness")
        ax1.plot(generations_range, history['avg_fitness'], label="Average Fitness")
        ax1.set_xlabel("Generation")
        ax1.set_ylabel("Fitness Value")
        ax1.set_title("Fitness Convergence Over Generations")
        ax1.legend()
        ax1.grid(True)

        st.pyplot(fig1)

        # ------------------ VIOLATIONS PLOT ------------------
        st.markdown("### Constraint Violations")

        fig2, ax2 = plt.subplots(figsize=(8, 4))
        ax2.plot(generations_range, history['hard_violations'], label="Hard Violations")
        ax2.plot(generations_range, history['soft_violations'], label="Soft Violations")
        ax2.set_xlabel("Generation")
        ax2.set_ylabel("Number of Violations")
        ax2.set_title("Constraint Violations Over Generations")
        ax2.legend()
        ax2.grid(True)

        st.pyplot(fig2)




# FOOTER
st.divider()
# st.markdown("""
# <div style='text-align: center; color: #666; padding: 2rem;'>
#     <p>Built By:</p>
#     <p>- Ayman Abdulaziz <br> - Ahmed Magdy <br> - Eyad Gamal <br> - Shahed Waleed <br> - Mahitab mohammed <br> - Mostafa Farghly</p>
# </div>
# """, unsafe_allow_html=True)