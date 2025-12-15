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
from algorithm.cultural_algorithm import CulturalAlgorithm, MultiTimetableCulturalAlgorithm

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
if 'final_fitness' not in st.session_state:
    st.session_state.final_fitness = None
if 'final_hard_violations' not in st.session_state:
    st.session_state.final_hard_violations = None
if 'final_soft_violations' not in st.session_state:
    st.session_state.final_soft_violations = None
if 'algorithm_completed' not in st.session_state:
    st.session_state.algorithm_completed = False
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
    
# Algorithm Results Summary
    if st.session_state.algorithm_completed and st.session_state.final_fitness is not None:
        st.divider()
        st.subheader("Last Algorithm Results")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Best Fitness", 
                f"{st.session_state.final_fitness:.5f}",
                help="Higher is better (max: 1.0)"
            )
        with col2:
            st.metric(
                "Hard Violations", 
                st.session_state.final_hard_violations,
                delta=-st.session_state.final_hard_violations if st.session_state.final_hard_violations > 0 else None,
                help="Critical constraints violated"
            )
        with col3:
            st.metric(
                "Soft Violations", 
                st.session_state.final_soft_violations,
                delta=-st.session_state.final_soft_violations if st.session_state.final_soft_violations > 0 else None,
                help="Preference constraints violated"
            )
        
        # Solution quality indicator
        if st.session_state.final_hard_violations == 0:
            st.success("Feasible Solution Found - No Hard Constraint Violations")
        elif st.session_state.final_hard_violations <= 5:
            st.warning(f"Nearly Feasible - {st.session_state.final_hard_violations} Hard Violations")
        else:
            st.error(f"Infeasible Solution - {st.session_state.final_hard_violations} Hard Violations")
    
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
        st.session_state.final_fitness = None
        st.session_state.final_hard_violations = None
        st.session_state.final_soft_violations = None
        st.session_state.algorithm_completed = False
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
            # Clear previous results
            st.session_state.final_fitness = None
            st.session_state.final_hard_violations = None
            st.session_state.final_soft_violations = None
            st.session_state.algorithm_completed = False
            
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
            
            # Create and run multi-timetable algorithm
            with st.spinner("Running Cultural Algorithm for all Level-Group combinations..."):
                def multi_progress_callback(message, completed, total):
                    if completed < total:
                        progress_bar.progress(completed / total)
                        status_text.text(f"{message} ({completed + 1}/{total})")
                    else:
                        progress_bar.progress(1.0)
                        status_text.text(message)
                
                ca = MultiTimetableCulturalAlgorithm(
                    courses=st.session_state.courses,
                    lecturers=st.session_state.lecturers,
                    rooms=st.session_state.rooms,
                    time_slots=st.session_state.time_slots,
                    population_size=pop_size,
                    generations=generations,
                    acceptance_rate=acceptance_rate,
                    mutation_rate=mutation_rate
                )
                
                all_timetables, all_histories = ca.run(callback=multi_progress_callback)
                
                st.session_state.results = all_timetables
                st.session_state.history = all_histories
                
                # Store final results for persistent display
                if all_histories:
                    st.session_state.algorithm_completed = True
                    # Store summary statistics from all timetables
                    all_fitness = []
                    all_hard_violations = []
                    all_soft_violations = []
                    
                    for level_group_id, history in all_histories.items():
                        if history and len(history['best_fitness']) > 0:
                            all_fitness.append(history['best_fitness'][-1])
                            all_hard_violations.append(history['hard_violations'][-1])
                            all_soft_violations.append(history['soft_violations'][-1])
                    
                    # Store average results
                    if all_fitness:
                        st.session_state.final_fitness = sum(all_fitness) / len(all_fitness)
                        st.session_state.final_hard_violations = sum(all_hard_violations)
                        st.session_state.final_soft_violations = sum(all_soft_violations)
                
                # Results processed successfully
                progress_bar.progress(1.0)
                st.success("Algorithm completed successfully!")
    
    # Performance Analysis for Multiple Timetables
    if st.session_state.history:
        st.divider()
        st.subheader("Algorithm Performance Analysis")
        
        # Check if history is a dictionary (multiple timetables) or single history
        if isinstance(st.session_state.history, dict):
            # Multiple histories - show aggregated and individual results
            perf_tab1, perf_tab2, perf_tab3 = st.tabs([
                "Aggregated Performance",
                "Individual Level-Group Performance", 
                "Summary Statistics"
            ])
            
            with perf_tab1:
                # Aggregated fitness evolution
                col1, col2 = st.columns(2)
                
                with col1:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    
                    # Calculate average fitness across all level-groups for each generation
                    max_generations = 0
                    all_histories = []
                    
                    for level_group_id, history in st.session_state.history.items():
                        if history and 'best_fitness' in history:
                            all_histories.append(history)
                            max_generations = max(max_generations, len(history['best_fitness']))
                    
                    if all_histories:
                        avg_best_fitness = []
                        avg_avg_fitness = []
                        
                        for gen in range(max_generations):
                            gen_best_fitness = []
                            gen_avg_fitness = []
                            
                            for history in all_histories:
                                if gen < len(history['best_fitness']):
                                    gen_best_fitness.append(history['best_fitness'][gen])
                                if gen < len(history['avg_fitness']):
                                    gen_avg_fitness.append(history['avg_fitness'][gen])
                            
                            if gen_best_fitness:
                                avg_best_fitness.append(sum(gen_best_fitness) / len(gen_best_fitness))
                            if gen_avg_fitness:
                                avg_avg_fitness.append(sum(gen_avg_fitness) / len(gen_avg_fitness))
                        
                        generations_range = list(range(1, len(avg_best_fitness) + 1))
                        ax.plot(generations_range, avg_best_fitness, 
                               label='Avg Best Fitness', color='green', linewidth=2)
                        ax.plot(generations_range, avg_avg_fitness, 
                               label='Avg Population Fitness', color='blue', alpha=0.7)
                    
                    ax.set_xlabel('Generation')
                    ax.set_ylabel('Fitness')
                    ax.set_title('Aggregated Fitness Evolution (All Level-Groups)')
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    st.pyplot(fig)
                    plt.close(fig)
                
                with col2:
                    # Aggregated violations plot
                    fig, ax = plt.subplots(figsize=(10, 6))
                    
                    if all_histories:
                        avg_hard_violations = []
                        avg_soft_violations = []
                        
                        for gen in range(max_generations):
                            gen_hard_violations = []
                            gen_soft_violations = []
                            
                            for history in all_histories:
                                if gen < len(history.get('hard_violations', [])):
                                    gen_hard_violations.append(history['hard_violations'][gen])
                                if gen < len(history.get('soft_violations', [])):
                                    gen_soft_violations.append(history['soft_violations'][gen])
                            
                            if gen_hard_violations:
                                avg_hard_violations.append(sum(gen_hard_violations) / len(gen_hard_violations))
                            if gen_soft_violations:
                                avg_soft_violations.append(sum(gen_soft_violations) / len(gen_soft_violations))
                        
                        ax.plot(generations_range, avg_hard_violations, 
                               label='Avg Hard Violations', color='red', linewidth=2)
                        ax.plot(generations_range, avg_soft_violations, 
                               label='Avg Soft Violations', color='orange', alpha=0.7)
                    
                    ax.set_xlabel('Generation')
                    ax.set_ylabel('Number of Violations')
                    ax.set_title('Aggregated Constraint Violations (All Level-Groups)')
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    st.pyplot(fig)
                    plt.close(fig)
            
            with perf_tab2:
                # Individual level-group performance
                st.subheader("Individual Level-Group Performance")
                
                for level_group_id, history in st.session_state.history.items():
                    with st.expander(f"Performance Details - {level_group_id}"):
                        if history and 'best_fitness' in history:
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                # Individual fitness plot
                                fig, ax = plt.subplots(figsize=(8, 4))
                                generations_range = list(range(1, len(history['best_fitness']) + 1))
                                ax.plot(generations_range, history['best_fitness'], 
                                       label='Best Fitness', color='green', linewidth=2)
                                ax.plot(generations_range, history['avg_fitness'], 
                                       label='Average Fitness', color='blue', alpha=0.7)
                                ax.set_xlabel('Generation')
                                ax.set_ylabel('Fitness')
                                ax.set_title(f'Fitness Evolution - {level_group_id}')
                                ax.legend()
                                ax.grid(True, alpha=0.3)
                                st.pyplot(fig)
                                plt.close(fig)
                            
                            with col2:
                                # Individual metrics
                                final_fitness = history['best_fitness'][-1]
                                final_hard = history['hard_violations'][-1]
                                final_soft = history['soft_violations'][-1]
                                
                                st.metric("Final Fitness", f"{final_fitness:.5f}")
                                st.metric("Hard Violations", final_hard)
                                st.metric("Soft Violations", final_soft)
            
            with perf_tab3:
                # Summary statistics
                st.subheader("Algorithm Parameters Used")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Population Size:** {pop_size}")
                    st.write(f"**Max Generations:** {generations}")
                    st.write(f"**Acceptance Rate:** {acceptance_rate}")
                    st.write(f"**Mutation Rate:** {mutation_rate}")
                
                with col2:
                    st.subheader("Overall Results")
                    if hasattr(st.session_state, 'final_fitness'):
                        st.metric("Average Fitness", f"{st.session_state.final_fitness:.5f}")
                        st.metric("Total Hard Violations", st.session_state.final_hard_violations)
                        st.metric("Total Soft Violations", st.session_state.final_soft_violations)
        else:
            # Single history (fallback to original behavior)
            perf_tab1, perf_tab2, perf_tab3 = st.tabs([
                "Evolution Curves",
                "Parameter Analysis", 
                "Belief Space Insights"
            ])
            
            with perf_tab1:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Fitness evolution plot
                    fig, ax = plt.subplots(figsize=(10, 6))
                    generations_range = list(range(1, len(st.session_state.history['best_fitness']) + 1))
                    ax.plot(generations_range, st.session_state.history['best_fitness'], 
                           label='Best Fitness', color='green', linewidth=2)
                    ax.plot(generations_range, st.session_state.history['avg_fitness'], 
                           label='Average Fitness', color='blue', alpha=0.7)
                    ax.set_xlabel('Generation')
                    ax.set_ylabel('Fitness')
                    ax.set_title('Fitness Evolution Over Generations')
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    st.pyplot(fig)
                    plt.close(fig)
                
                with col2:
                    # Violations plot
                    fig, ax = plt.subplots(figsize=(10, 6))
                    ax.plot(generations_range, st.session_state.history['hard_violations'], 
                           label='Hard Violations', color='red', linewidth=2)
                    ax.plot(generations_range, st.session_state.history['soft_violations'], 
                           label='Soft Violations', color='orange', alpha=0.7)
                    ax.set_xlabel('Generation')
                    ax.set_ylabel('Number of Violations')
                    ax.set_title('Constraint Violations Over Generations')
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    st.pyplot(fig)
                    plt.close(fig)

    # Display results for multiple timetables
    if st.session_state.results:
        st.divider()
        st.subheader("Generated Timetables by Level and Group")

        # Check if results is a dictionary (multiple timetables) or single timetable
        if isinstance(st.session_state.results, dict):
            # Multiple timetables - display each one in a tab
            level_group_ids = sorted(st.session_state.results.keys())
            
            # Create summary metrics
            st.subheader("Summary Statistics")
            col1, col2, col3, col4 = st.columns(4)
            
            total_timetables = len(level_group_ids)
            avg_fitness = st.session_state.final_fitness if hasattr(st.session_state, 'final_fitness') else 0
            total_hard_violations = st.session_state.final_hard_violations if hasattr(st.session_state, 'final_hard_violations') else 0
            total_soft_violations = st.session_state.final_soft_violations if hasattr(st.session_state, 'final_soft_violations') else 0
            
            col1.metric("Total Timetables", total_timetables)
            col2.metric("Average Fitness", f"{avg_fitness:.4f}")
            col3.metric("Total Hard Violations", total_hard_violations)
            col4.metric("Total Soft Violations", total_soft_violations)
            
            # Create tabs for each timetable
            tabs = st.tabs(level_group_ids)
            
            all_grids = {}
            
            for i, level_group_id in enumerate(level_group_ids):
                with tabs[i]:
                    timetable = st.session_state.results[level_group_id]
                    if timetable and hasattr(timetable, 'to_dict_list'):
                        timetable_data = timetable.to_dict_list()
                        df_timetable = pd.DataFrame(timetable_data)
                        
                        if not df_timetable.empty:
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

                            # Display the timetable
                            st.dataframe(grid_df, use_container_width=True, height=400)
                            
                            # Store for PDF generation
                            all_grids[level_group_id] = grid_df
                            
                            # Individual timetable metrics
                            if level_group_id in st.session_state.history:
                                history = st.session_state.history[level_group_id]
                                if history and 'best_fitness' in history and len(history['best_fitness']) > 0:
                                    col1, col2, col3 = st.columns(3)
                                    col1.metric("Final Fitness", f"{history['best_fitness'][-1]:.4f}")
                                    col2.metric("Hard Violations", history['hard_violations'][-1])
                                    col3.metric("Soft Violations", history['soft_violations'][-1])
                            
                            # Debug info for this timetable
                            with st.expander(f"Debug Information - {level_group_id}"):
                                st.write(f"Total entries: {len(df_timetable)}")
                                st.write(f"Unique days: {df_timetable['day'].unique()}")
                                st.write(f"Unique hours: {sorted(df_timetable['hour'].unique())}")
                                st.write(f"Grid shape: {grid_df.shape}")
                                st.write("Sample entries:")
                                st.write(df_timetable.head())
                        else:
                            st.warning(f"No data available for {level_group_id}")
                    else:
                        st.error(f"Invalid timetable data for {level_group_id}")
            
            # Store grids for download functions
            st.session_state.all_grids = all_grids
        
        else:
            # Single timetable (fallback to original behavior)
            timetable_data = st.session_state.results.to_dict_list()
            df_timetable = pd.DataFrame(timetable_data)
            
            days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
            time_slots = sorted(df_timetable['hour'].unique(), key=lambda x: int(x.split(':')[0]))
            grid_df = pd.DataFrame("", index=days, columns=time_slots)

            for _, row in df_timetable.iterrows():
                day = row['day']
                hour = row['hour']
                entry = f"{row['course']} | {row['room']} | {row['lecturer']}"
                if grid_df.at[day, hour] != "":
                    grid_df.at[day, hour] += "\n" + entry 
                else:
                    grid_df.at[day, hour] = entry

            st.dataframe(grid_df, use_container_width=True, height=400)
            st.session_state.all_grids = {"Single Timetable": grid_df}
        
        # ------------- Download Options ----------------
        st.subheader("Download Options")
        download_col1, download_col2, download_col3 = st.columns(3)
        
        with download_col1:
            # CSV Download for all timetables
            if hasattr(st.session_state, 'all_grids') and st.session_state.all_grids:
                all_csv_data = {}
                for level_group_id, grid_df in st.session_state.all_grids.items():
                    all_csv_data[level_group_id] = grid_df.to_csv(index=True)
                
                combined_csv = ""
                for level_group_id, csv_data in all_csv_data.items():
                    combined_csv += f"=== {level_group_id} ===\n"
                    combined_csv += csv_data
                    combined_csv += "\n\n"
                
                st.download_button("Download All CSV", combined_csv, "all_timetables.csv", "text/csv")

        with download_col2:
            # JSON Download for all timetables
            if hasattr(st.session_state, 'all_grids') and st.session_state.all_grids:
                all_json_data = {}
                for level_group_id, grid_df in st.session_state.all_grids.items():
                    all_json_data[level_group_id] = grid_df.to_dict(orient='index')
                
                st.download_button("Download All JSON", 
                                 json.dumps(all_json_data, indent=2), 
                                 "all_timetables.json", "application/json")

        with download_col3:
            # PDF Download for all timetables (8 pages)
            if hasattr(st.session_state, 'all_grids') and st.session_state.all_grids:
                def create_multi_page_pdf(all_grids):
                    from fpdf import FPDF
                    
                    # Use A3 landscape for better space
                    pdf = FPDF(orientation="L", unit="mm", format="A3")
                    
                    for i, (level_group_id, df) in enumerate(all_grids.items()):
                        # Add a new page for each timetable
                        pdf.add_page()
                        
                        # Title for this timetable
                        pdf.set_font("Arial", "B", 16)
                        pdf.cell(0, 15, f"Timetable Schedule - {level_group_id}", ln=True, align="C")
                        pdf.ln(5)
                        
                        # Add level-group information
                        pdf.set_font("Arial", "", 12)
                        level = level_group_id[1]  # Extract level from L1G1 format
                        group = level_group_id[3]  # Extract group from L1G1 format
                        pdf.cell(0, 10, f"Level: {level} | Group: {group}", ln=True, align="C")
                        pdf.ln(5)
                        
                        # Calculate dimensions
                        page_width = pdf.w - 20  # Leave margins
                        col_width = page_width / (len(df.columns) + 1)
                        row_height = 20  # Increased height for better readability
                        
                        # Header styling
                        pdf.set_font("Arial", "B", 10)
                        pdf.set_fill_color(200, 220, 255)  # Light blue background
                        
                        # Header row - Day/Time column
                        pdf.cell(col_width, row_height, "Day/Time", border=1, ln=0, align="C", fill=True)
                        
                        # Header row - Time columns
                        for col in df.columns:
                            pdf.cell(col_width, row_height, str(col), border=1, ln=0, align="C", fill=True)
                        pdf.ln(row_height)
                        
                        # Data rows
                        pdf.set_font("Arial", "", 8)
                        pdf.set_fill_color(245, 245, 245)  # Light gray for alternating rows
                        
                        for idx, (day, row) in enumerate(df.iterrows()):
                            fill = idx % 2 == 0  # Alternate row coloring
                            
                            # Calculate row height based on content
                            max_lines = 1
                            for item in row:
                                if str(item) != "":
                                    lines = str(item).split("\n")
                                    max_lines = max(max_lines, len(lines))
                            
                            dynamic_row_height = max(row_height, max_lines * 6)  # 6mm per line
                            
                            # Day column
                            pdf.set_font("Arial", "B", 9)
                            pdf.cell(col_width, dynamic_row_height, str(day), border=1, ln=0, align="C", fill=fill)
                            
                            # Time slot columns
                            pdf.set_font("Arial", "", 7)
                            for item in row:
                                content = str(item) if item != "" else ""
                                
                                if content != "":
                                    # Split multiple entries and format each on new line
                                    entries = content.split("\n") if "\n" in content else [content]
                                    formatted_entries = []
                                    
                                    for entry in entries:
                                        if len(entry.strip()) > 0:
                                            # Format each entry nicely
                                            if len(entry) > 35:  # Wrap long entries
                                                words = entry.split()
                                                lines = []
                                                current_line = ""
                                                for word in words:
                                                    if len(current_line + " " + word) <= 35:
                                                        current_line += " " + word if current_line else word
                                                    else:
                                                        if current_line:
                                                            lines.append(current_line)
                                                        current_line = word
                                                if current_line:
                                                    lines.append(current_line)
                                                formatted_entries.extend(lines)
                                            else:
                                                formatted_entries.append(entry)
                                    
                                    # Join entries with newlines for vertical display
                                    final_content = "\n".join(formatted_entries)
                                else:
                                    final_content = ""
                                
                                # Create multi-line cell
                                x_pos = pdf.get_x()
                                y_pos = pdf.get_y()
                                
                                # Draw cell border
                                pdf.rect(x_pos, y_pos, col_width, dynamic_row_height)
                                if fill:
                                    pdf.set_fill_color(245, 245, 245)
                                    pdf.rect(x_pos, y_pos, col_width, dynamic_row_height, 'F')
                                
                                # Add text line by line
                                if final_content:
                                    lines = final_content.split("\n")
                                    line_height = 4
                                    start_y = y_pos + 2
                                    
                                    for j, line in enumerate(lines[:int(dynamic_row_height/line_height)-1]):  # Fit within cell
                                        pdf.set_xy(x_pos + 1, start_y + (j * line_height))
                                        pdf.cell(col_width - 2, line_height, line.strip(), ln=0, align="L")
                                
                                # Move to next column
                                pdf.set_xy(x_pos + col_width, y_pos)
                            
                            pdf.ln(dynamic_row_height)
                        
                        # Footer for this page
                        pdf.ln(10)
                        pdf.set_font("Arial", "I", 8)
                        pdf.cell(0, 10, f"Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} | Page {i+1} of {len(all_grids)}", ln=True, align="C")
                    
                    # Generate PDF as bytes
                    pdf_output = pdf.output(dest='S')
                    if isinstance(pdf_output, str):
                        pdf_bytes = pdf_output.encode('latin1')
                    else:
                        pdf_bytes = pdf_output
                    return pdf_bytes

                pdf_bytes = create_multi_page_pdf(st.session_state.all_grids)
                st.download_button("Download All PDF (8 Pages)", pdf_bytes, "all_timetables.pdf", "application/pdf")
        
        # Global Constraints Analysis
        if isinstance(st.session_state.results, dict):
            st.divider()
            st.subheader("Global Constraints Analysis")
            
            # Import and use the global constraint checker
            from algorithm.global_constraints import GlobalConstraintChecker
            
            global_checker = GlobalConstraintChecker()
            
            # Get constraint report
            constraint_report = global_checker.get_constraint_report(st.session_state.results)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Conflicts", constraint_report['total_conflicts'])
            with col2:
                st.metric("Lecturer Conflicts", len(constraint_report['lecturer_conflicts']))
            with col3:
                st.metric("Room Conflicts", len(constraint_report['room_conflicts']))
            
            # Show detailed conflicts if any exist
            if constraint_report['total_conflicts'] > 0:
                st.warning("⚠️ Global constraint violations detected!")
                
                if constraint_report['lecturer_conflicts']:
                    with st.expander("👨‍🏫 Lecturer Conflicts"):
                        for conflict in constraint_report['lecturer_conflicts']:
                            st.write(f"**{conflict['resource']}** has conflicts at **{conflict['time']}**:")
                            for assignment in conflict['conflicting_assignments']:
                                st.write(f"  - {assignment['level_group']}: {assignment['course']} in {assignment['room']}")
                            st.write("---")
                
                if constraint_report['room_conflicts']:
                    with st.expander("🏢 Room Conflicts"):
                        for conflict in constraint_report['room_conflicts']:
                            st.write(f"**{conflict['resource']}** has conflicts at **{conflict['time']}**:")
                            for assignment in conflict['conflicting_assignments']:
                                st.write(f"  - {assignment['level_group']}: {assignment['course']} by {assignment['lecturer']}")
                            st.write("---")
            else:
                st.success("✅ No global constraint violations found! All shared resources (lecturers and rooms) are properly scheduled.")
                
                # Show optimization summary if available
                optimization_summary = []
                for level_group_id, history in st.session_state.history.items():
                    if isinstance(history, dict) and 'global_optimization_iterations' in history:
                        optimization_summary.append(f"{level_group_id}: {history['global_optimization_iterations']} iterations")
                
                if optimization_summary:
                    with st.expander("🔧 Global Optimization Details"):
                        st.write("The following timetables required additional optimization to resolve conflicts:")
                        for summary in optimization_summary:
                            st.write(f"• {summary}")





# FOOTER
st.divider()
# st.markdown("""
# <div style='text-align: center; color: #666; padding: 2rem;'>
#     <p>Built By:</p>
#     <p>- Ayman Abdulaziz <br> - Ahmed Magdy <br> - Eyad Gamal <br> - Shahed Waleed <br> - Mahitab mohammed <br> - Mostafa Farghly</p>
# </div>
# """, unsafe_allow_html=True)