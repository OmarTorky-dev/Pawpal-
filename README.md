# 🐾 PawPal+

**PawPal+** is a pet care planner for busy owners. It tracks feedings, walks, medications and appointments across all of your pets, puts them in time order, warns you when two tasks clash, rolls recurring tasks forward automatically, and builds a daily plan that fits the time you actually have — explaining what it skipped and why.

It's built CLI-first: all logic lives in `pawpal_system.py` (verified by `main.py` and a pytest suite), and `app.py` is a Streamlit UI on top.

## ✨ Features

- **Multi-pet households** – an `Owner` manages any number of `Pet`s; duplicate pet names are rejected (case-insensitive).
- **Validated tasks** – each task has a time, duration, priority (low/medium/high) and frequency (once/daily/weekly). Times like `"7:05"` are normalized to `"07:05"`; impossible times such as `"25:00"` are rejected.
- **Sorting by time** – `Scheduler.sort_by_time()` orders tasks by date, then time, with high priority first when two tasks share a slot.
- **Today's view** – `Scheduler.get_todays_tasks()` shows today's tasks plus anything still overdue; old completed tasks drop off.
- **Filtering** – `Scheduler.filter_tasks()` narrows tasks by pet, by done / to-do, or both.
- **Conflict warnings** – `Scheduler.detect_conflicts()` flags tasks whose time windows overlap (using start time + duration), across pets and even across midnight. It warns instead of crashing or silently rescheduling.
- **Daily & weekly recurrence** – completing a recurring task via `Scheduler.mark_task_complete()` automatically creates the next one (`timedelta(days=1)` / `timedelta(weeks=1)`). Overdue tasks come back *after* today, and weekly tasks keep their weekday.
- **Time-budgeted plan with explanations** – `Scheduler.generate_plan()` fits pending tasks into the owner's available minutes, highest priority first, and `Scheduler.explain_plan()` says why anything was skipped.
- **Streamlit UI** – add pets and tasks, filter today's schedule, mark tasks done, see conflicts and upcoming recurring tasks, and generate a plan; data persists across clicks via `st.session_state`.

## 🚀 Getting started

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

| Command | What it does |
|---------|--------------|
| `python main.py` | Runs the CLI demo (sorting, filtering, conflicts, recurrence, plan) |
| `python -m streamlit run app.py` | Launches the web app |
| `python -m pytest` | Runs the test suite |

### Project layout

```
pawpal_system.py        # Logic layer: Task, Pet, Owner, Scheduler
main.py                 # CLI demo script
app.py                  # Streamlit UI
tests/test_pawpal.py    # pytest suite
diagrams/uml.mmd        # Phase 1 draft UML
diagrams/uml_final.mmd  # Final UML (matches the code)
reflection.md           # Design + AI collaboration reflection
```

## 🏗️ Architecture

`Owner` has many `Pet`s, each `Pet` has many `Task`s, and the `Scheduler` reads everything through the `Owner` (it holds a reference, not a copy, so it always sees live data). See [`diagrams/uml_final.mmd`](diagrams/uml_final.mmd) for the full class diagram.

## 🖥️ Sample Output

Output of `python main.py`:

```
PawPal+ for Jordan (2 pets, 60 min available)

Tasks in the order they were added
======================================================================
  Due        Time   Pet      Task                  Min  Priority Repeats Done
  ------------------------------------------------------------------
  11-25      08:00  Mochi    Breakfast              10  high     daily   [ ]
  11-25      07:30  Mochi    Morning walk           20  high     daily   [ ]
  11-25      10:00  Mochi    Grooming               40  low      once    [ ]
  11-25      18:00  Luna     Play session           15  medium   daily   [ ]
  11-25      08:00  Luna     Flea medication         5  high     weekly  [ ]

Today's Schedule (sorted by time)
======================================================================
  Due        Time   Pet      Task                  Min  Priority Repeats Done
  ------------------------------------------------------------------
  11-25      07:30  Mochi    Morning walk           20  high     daily   [ ]
  11-25      08:00  Mochi    Breakfast              10  high     daily   [ ]
  11-25      08:00  Luna     Flea medication         5  high     weekly  [ ]
  11-25      10:00  Mochi    Grooming               40  low      once    [ ]
  11-25      18:00  Luna     Play session           15  medium   daily   [ ]

Conflict check
======================================================================
  Conflict (same time): Mochi's 'Breakfast' (Wed 08:00, 10 min) and Luna's 'Flea medication' (Wed 08:00, 5 min)

Filter: Luna's tasks only
======================================================================
  Due        Time   Pet      Task                  Min  Priority Repeats Done
  ------------------------------------------------------------------
  11-25      08:00  Luna     Flea medication         5  high     weekly  [ ]
  11-25      18:00  Luna     Play session           15  medium   daily   [ ]

Completed Mochi's daily 'Morning walk' -> next one auto-created for 2026-11-26

Filter: completed tasks
======================================================================
  Due        Time   Pet      Task                  Min  Priority Repeats Done
  ------------------------------------------------------------------
  11-25      07:30  Mochi    Morning walk           20  high     daily   [x]

Mochi's tasks (note tomorrow's walk)
======================================================================
  Due        Time   Pet      Task                  Min  Priority Repeats Done
  ------------------------------------------------------------------
  11-25      07:30  Mochi    Morning walk           20  high     daily   [x]
  11-25      08:00  Mochi    Breakfast              10  high     daily   [ ]
  11-25      10:00  Mochi    Grooming               40  low      once    [ ]
  11-26      07:30  Mochi    Morning walk           20  high     daily   [ ]

Today's Plan (fits in 60 min)
======================================================================
  Due        Time   Pet      Task                  Min  Priority Repeats Done
  ------------------------------------------------------------------
  11-25      08:00  Luna     Flea medication         5  high     weekly  [ ]
  11-25      08:00  Mochi    Breakfast              10  high     daily   [ ]
  11-25      18:00  Luna     Play session           15  medium   daily   [ ]
  * Planned 3 task(s) using 30 of 60 available minutes.
  * Skipped 'Grooming' for Mochi (40 min, low priority): not enough time left after higher-priority tasks.
```

## 🧪 Testing PawPal+

Run the full suite from the project root:

```bash
python -m pytest
```

`tests/test_pawpal.py` contains **45 tests** covering both happy paths and edge cases:

| Area | What's verified |
|------|-----------------|
| Basics | `mark_complete()` flips status; `add_task()` grows a pet's list and tags the pet name; removing tasks; owners aggregate tasks across pets; duplicate pet names are rejected |
| Validation | Times normalize to `HH:MM` (`"7:05"` → `"07:05"`); bad times (`"25:00"`, `"noon"`, `""`), priorities, frequencies and zero durations raise `ValueError` |
| Sorting | Out-of-order tasks come back chronologically; `"9:00"` sorts before `"10:00"`; ties broken by priority; tomorrow sorts after today; empty list |
| Recurrence | Completing a daily task creates one for the next day (weekly → +7 days); one-off tasks don't recur; month, year and leap-day boundaries; completing twice rolls forward twice; overdue tasks come back *after* today (weekly keeps its weekday, missed weeks are skipped); completing early; unknown pet/task returns `None` |
| Conflicts | Exact same time is flagged; overlapping durations are flagged; back-to-back tasks are *not*; completed tasks and tasks on different days are ignored; a 23:30 task running past midnight clashes with a 00:15 task the next day, but one ending exactly at 00:00 doesn't; a long task is flagged against every task it covers; no tasks → no warnings |
| Filtering / today | Pet filter is case-insensitive; status filter and combined filters; a pet with no tasks; overdue pending tasks show today, old completed ones don't |
| Planning | Plan stays within the time budget and prefers high priority; explanations mention skipped tasks; empty day and zero-minute budget |

To check the tests actually catch bugs (not just pass), I temporarily broke three pieces of logic — conflict boundary (`<` → `<=`), recurrence date (no `+ timedelta`), the sort key, the overdue catch-up loop, and cross-midnight detection — and each change made the relevant tests fail.

Sample test output:

```
============================= test session starts =============================
platform win32 -- Python 3.15.2, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\omart\OneDrive\Desktop\Pawpal-\ai110-module2show-pawpal-starter
plugins: anyio-4.16.0
collected 45 items

tests\test_pawpal.py .............................................       [100%]

============================= 45 passed in 0.12s ==============================
```

**Confidence level: ★★★★☆ (4/5)** — every core scheduling behavior and the edge cases I could think of are covered and passing, and the suite catches deliberately injected bugs. One star held back because the Streamlit UI is only checked manually / with a smoke test, and real-world inputs like time zones or daylight-saving changes aren't handled yet.

## 📐 Smarter Scheduling

All scheduling logic lives in `Scheduler` (and `Task`) in `pawpal_system.py`.

| Feature | Method(s) | How it works |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()` | `sorted()` with a `lambda` key of `(due_date, time, priority rank)`. Times are normalized to zero-padded `"HH:MM"` in `Task.__post_init__`, so string order equals chronological order (`"9:00"` becomes `"09:00"`). Ties at the same time put high priority first. |
| Today's view | `Scheduler.get_todays_tasks()` | Tasks due today plus *unfinished* overdue tasks, sorted by time. Completed tasks from past days drop off. |
| Filtering | `Scheduler.filter_tasks(pet_name=, completed=)` | Filter by pet (case-insensitive), by completion status, or both. A filter left as `None` is ignored. |
| Conflict detection | `Scheduler.detect_conflicts()` | Builds real start/end `datetime`s (due date + time + duration), sorts pending tasks by start, and flags any pair whose windows overlap, labelled "same time" or "overlap". Because it uses full datetimes, a 23:30 task lasting an hour clashes with a 00:15 task the next day. The scan stops early for each task once later tasks start after it ends. Works across pets, since the owner can't be in two places at once. Returns warning strings; never raises. |
| Recurring tasks | `Task.next_occurrence()`, `Scheduler.mark_task_complete()` | Completing a `daily`/`weekly` task automatically adds a fresh copy due `+ timedelta(days=1)` / `+ timedelta(weeks=1)` to the same pet. If the task was overdue, it keeps stepping forward until the new date is after today, so a missed daily walk comes back tomorrow and weekly meds keep their weekday. `once` tasks just complete. |
| Daily plan | `Scheduler.generate_plan()`, `Scheduler.explain_plan()` | Greedy fit to `Owner.available_minutes`: high priority first (shorter first within a priority), keep what fits, return `(planned, skipped)` with the plan in time order, plus plain-English reasons for each skip. |

## 📸 Demo Walkthrough

### What you can do in the app (`python -m streamlit run app.py`)

- **Owner** – set your name and how many minutes you have for pet care today.
- **Pets** – add a pet (name, species, age), or click the **Or load sample pets and tasks** button to try it instantly. Pets are listed in a table with their task counts.
- **Schedule a task** – pick a pet, describe the task, and choose its time, duration, priority and how often it repeats.
- **Today's schedule** – a time-sorted table with priority badges, filters for pet and status (All / To do / Done), a progress bar, and a **Mark done** control.
- **Conflict warnings** – shown in a yellow box *above* the schedule so you see them first, naming both pets, both tasks and their times, with a suggestion to move one. If there are none, a green "No conflicts" message appears.
- **Build today's plan** – generates a plan that fits your available minutes and explains anything skipped.
- **Upcoming** – an expander listing future tasks, including the ones created automatically by recurrence.

### Example workflow

1. Open the app and click the **Or load sample pets and tasks** button (or add pets yourself). Mochi the dog and Luna the cat appear with 5 tasks between them.
2. Look at **Today's schedule**: tasks are listed by time (07:30 → 18:00) even though they were added out of order.
3. A **conflict warning** appears: Mochi's *Breakfast* and Luna's *Flea medication* are both at 08:00.
4. Set the **Show pet** filter to *Luna* to see only her tasks, then switch back to *All pets*.
5. Select *07:30 · Mochi · Morning walk* and click **Mark done**. A success message confirms it and says the next daily walk was added for tomorrow; it now appears under **Upcoming**, and the progress bar moves to 1 of 5.
6. Lower **Minutes available today** to 30 and click **Generate plan**. PawPal+ keeps the high- and medium-priority tasks that fit (30 of 30 minutes) and warns that *Grooming* (40 min, low priority) was skipped for lack of time.

### Key scheduler behaviors shown

| Behavior | Where you see it |
|----------|------------------|
| Sorting by time (`sort_by_time`) | Today's schedule order; plan order |
| Filtering (`filter_tasks`) | Pet / status filters |
| Conflict detection (`detect_conflicts`) | Yellow warning above the schedule |
| Recurrence (`mark_task_complete` → `next_occurrence`) | Success message after **Mark done**; Upcoming expander |
| Time-budgeted planning (`generate_plan`, `explain_plan`) | **Generate plan** results |

### CLI demo output (`python main.py`)

```
PawPal+ for Jordan (2 pets, 60 min available)

Tasks in the order they were added
======================================================================
  Due        Time   Pet      Task                  Min  Priority Repeats Done
  ------------------------------------------------------------------
  11-25      08:00  Mochi    Breakfast              10  high     daily   [ ]
  11-25      07:30  Mochi    Morning walk           20  high     daily   [ ]
  11-25      10:00  Mochi    Grooming               40  low      once    [ ]
  11-25      18:00  Luna     Play session           15  medium   daily   [ ]
  11-25      08:00  Luna     Flea medication         5  high     weekly  [ ]

Today's Schedule (sorted by time)
======================================================================
  Due        Time   Pet      Task                  Min  Priority Repeats Done
  ------------------------------------------------------------------
  11-25      07:30  Mochi    Morning walk           20  high     daily   [ ]
  11-25      08:00  Mochi    Breakfast              10  high     daily   [ ]
  11-25      08:00  Luna     Flea medication         5  high     weekly  [ ]
  11-25      10:00  Mochi    Grooming               40  low      once    [ ]
  11-25      18:00  Luna     Play session           15  medium   daily   [ ]

Conflict check
======================================================================
  Conflict (same time): Mochi's 'Breakfast' (Wed 08:00, 10 min) and Luna's 'Flea medication' (Wed 08:00, 5 min)

Filter: Luna's tasks only
======================================================================
  Due        Time   Pet      Task                  Min  Priority Repeats Done
  ------------------------------------------------------------------
  11-25      08:00  Luna     Flea medication         5  high     weekly  [ ]
  11-25      18:00  Luna     Play session           15  medium   daily   [ ]

Completed Mochi's daily 'Morning walk' -> next one auto-created for 2026-11-26

Filter: completed tasks
======================================================================
  Due        Time   Pet      Task                  Min  Priority Repeats Done
  ------------------------------------------------------------------
  11-25      07:30  Mochi    Morning walk           20  high     daily   [x]

Mochi's tasks (note tomorrow's walk)
======================================================================
  Due        Time   Pet      Task                  Min  Priority Repeats Done
  ------------------------------------------------------------------
  11-25      07:30  Mochi    Morning walk           20  high     daily   [x]
  11-25      08:00  Mochi    Breakfast              10  high     daily   [ ]
  11-25      10:00  Mochi    Grooming               40  low      once    [ ]
  11-26      07:30  Mochi    Morning walk           20  high     daily   [ ]

Today's Plan (fits in 60 min)
======================================================================
  Due        Time   Pet      Task                  Min  Priority Repeats Done
  ------------------------------------------------------------------
  11-25      08:00  Luna     Flea medication         5  high     weekly  [ ]
  11-25      08:00  Mochi    Breakfast              10  high     daily   [ ]
  11-25      18:00  Luna     Play session           15  medium   daily   [ ]
  * Planned 3 task(s) using 30 of 60 available minutes.
  * Skipped 'Grooming' for Mochi (40 min, low priority): not enough time left after higher-priority tasks.
```
