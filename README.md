**Project**: Timetable Scheduling — Cultural Algorithm

- **Repository**: `d:/Projects/Python/TimeTable-Scheduling`
- **Purpose**: Use a simple Cultural Algorithm implementation to build weekly timetables by allocating course hours into defined time slots. A Streamlit frontend is provided to upload or edit CSV inputs and run the algorithm interactively.

**Setup (.venv)**
- **Create virtual environment**: from project root run:

```terminal
python -m venv .venv
```

- **Activate the venv (PowerShell)**:

```powershell
# If activation is blocked, run once (elevated if needed):
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\\.venv\Scripts\Activate.ps1
```

- **Install required packages**:

```powershell
pip install --upgrade pip
pip install streamlit pandas numpy
```

- Optional development helpers (recommended):

```powershell
pip install black pylint
```

**Run the Streamlit frontend**
- Start the app from project root:

```powershell
python -m streamlit run src/visualization/streamlit_app.py
```

- If `streamlit` command is available on PATH you can also use:

```powershell
streamlit run src/visualization/streamlit_app.py
```

**Data files used by the app**
- Default CSVs are under `data/`:
  - `data/lecturers.csv` — columns: `name,id,class` (sample provided)
  - `data/courses.csv` — columns: `course_id,name,hours_per_week,lecturer_id` (sample provided)
  - `data/rooms.csv` — columns: `room_id,name,capacity` (sample provided)
  - `data/classes.csv` — columns: `class_id,name,year,students` (sample provided)
  - `data/time-slots.csv` — columns: `slot_id,day,period,start_time,end_time` (sample provided)

**How uploads are handled in the Streamlit app**
- The app sidebar shows `file_uploader` widgets for each CSV. Behavior:
  - If you upload a file, the app reads that uploaded CSV and uses it for the run.
  - If you do not upload, the app falls back to the default CSV found in `data/` folder.
  - You can preview and edit the loaded data inline using the table editor before running.

- How to verify the upload worked:
  - After you upload a CSV, it appears in the 'Data Preview (editable)' section. Confirm the rows show your data.
  - If the preview remains empty, check the browser console and the Streamlit logs in the terminal for parsing errors.

**Common issues when upload isn't read**
- `file_uploader` returns a Streamlit `UploadedFile` object. The app's `load_df` function attempts a normal `pd.read_csv(uploaded)` first and falls back to decoding `uploaded.getvalue()` if necessary. If the upload isn't read:
  - Ensure the CSV has a header row and is UTF-8 encoded.
  - Try opening the file with a text editor and saving with UTF-8 encoding.
  - If the CSV uses a different delimiter (e.g., `;`) add a column in the top row or convert to comma-separated.

**Running the core runner (without Streamlit)**
- You can run the simple command-line runner which uses `data/` defaults:

```powershell
python -m src.main
```

This writes `data/output_timetable.csv` containing the timetable assignments.

**Fitness function: known issue and guidance**
- Current state: `src/algorithm/evaluation.py` implements a simple fitness that:
  - Counts assigned hours per course in the timetable and penalizes absolute deviation vs required hours with a large weight (100.0 per hour mismatch).
  - Adds a small penalty for empty slots.

- Why it may appear "incorrect":
  - Mismatched `course_id` keys: If `course_id` values in `data/courses.csv` don't match the course ids placed in the timetable (strings vs ints, leading/trailing spaces), the assigned counts will be zero and fitness will incorrectly show large penalties. Make sure `course_id` is consistent, and there are no extra spaces.
  - The large penalty multiplier (100.0) makes any small mismatch dominate the fitness and may hide other constraints. This can make search unstable when `hours_per_week` totals don't fit `time-slots` count.
  - The fitness has no knowledge of lecturer conflicts, room capacities, or cross-class clashes. If you expect those to be enforced, they must be added to the fitness as additional penalties (or implemented as hard constraints during candidate generation).

**Quick checks and troubleshooting for fitness**
- Print assigned counts while debugging: add a temporary print in `evaluation.fitness`:

```python
print('assigned_counts:', assigned_counts)
print('required:', course_hours_required)
```

- Ensure that `run_cultural_algorithm` receives a `course_hours` dict whose keys are exact `course_id` strings. In Streamlit the code maps `course_id` column to this dict — verify by printing it.

**Suggested fitness improvements**
- Make keys canonical (convert to str and strip whitespace) and reduce the mismatch weight. Replace `evaluation.py` body with the following improved version (suggested, not auto-applied):

```python
from typing import Dict
from src.models.timetable import Timetable


def fitness(t: Timetable, course_hours_required: Dict[str, int]) -> float:
    """Robust fitness: normalizes keys, penalizes mismatch less aggressively, and reports diagnostics."""
    fitness = 0.0
    # Normalize required keys
    req = {str(k).strip(): int(v) for k, v in course_hours_required.items()}
    assigned_counts = {}
    for cid in t.assignments:
        if cid is None:
            continue
        key = str(cid).strip()
        assigned_counts[key] = assigned_counts.get(key, 0) + 1

    # Penalize mismatch (lighter weight)
    for cid, req_hours in req.items():
        assigned = assigned_counts.get(cid, 0)
        fitness += abs(req_hours - assigned) * 10.0  # smaller weight

    # Penalty for any unknown assigned course ids
    for cid in assigned_counts:
        if cid not in req:
            fitness += assigned_counts[cid] * 20.0

    # small penalty for empty slots
    fitness += t.empty_slots() * 1.0

    return fitness
```

- If you want lecturer-conflict detection, you can extend fitness to accept a `course_to_lecturer` mapping and penalize cases where the same lecturer appears in multiple courses assigned to the same slot index across multiple class timetables.

**If you'd like me to apply the fitness fix**
- I can patch `src/algorithm/evaluation.py` to the improved version above and run a quick local check. Reply `apply-fix` and I'll update the code and run the runner to show results.

**Other recommended improvements**
- Add unit tests for `fitness()` with small timetables to validate behavior.
- Add stricter input validation in the Streamlit UI (e.g., required columns checks and clearer error messages).
- Extend candidate representation to include `room_id` and `lecturer_id` per assignment if your problem needs room/lecturer conflict checks.

**Contact / Next steps**
- Tell me if you want me to:
  - `apply-fix`: update `evaluation.py` and test the runner.
  - Improve fitness with lecturer conflict & room checks now.
  - Write unit tests for the algorithm components.

---
Generated on: 2025-11-29
