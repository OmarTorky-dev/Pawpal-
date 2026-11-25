# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

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
  Conflict (same time): Mochi's 'Breakfast' (08:00, 10 min) and Luna's 'Flea medication' (08:00, 5 min)

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

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

All scheduling logic lives in `Scheduler` (and `Task`) in `pawpal_system.py`.

| Feature | Method(s) | How it works |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()` | `sorted()` with a `lambda` key of `(due_date, time, priority rank)`. Times are normalized to zero-padded `"HH:MM"` in `Task.__post_init__`, so string order equals chronological order (`"9:00"` becomes `"09:00"`). Ties at the same time put high priority first. |
| Today's view | `Scheduler.get_todays_tasks()` | Tasks due today plus *unfinished* overdue tasks, sorted by time. Completed tasks from past days drop off. |
| Filtering | `Scheduler.filter_tasks(pet_name=, completed=)` | Filter by pet (case-insensitive), by completion status, or both. A filter left as `None` is ignored. |
| Conflict detection | `Scheduler.detect_conflicts()` | Compares every pair of pending same-day tasks and flags any whose time windows overlap (start + duration), labelled "same time" or "overlap". Works across pets, since the owner can't be in two places at once. Returns warning strings; never raises. |
| Recurring tasks | `Task.next_occurrence()`, `Scheduler.mark_task_complete()` | Completing a `daily`/`weekly` task automatically adds a fresh copy due `+ timedelta(days=1)` / `+ timedelta(weeks=1)` to the same pet. `once` tasks just complete. |
| Daily plan | `Scheduler.generate_plan()`, `Scheduler.explain_plan()` | Greedy fit to `Owner.available_minutes`: high priority first (shorter first within a priority), keep what fits, return `(planned, skipped)` with the plan in time order, plus plain-English reasons for each skip. |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
