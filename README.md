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

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
