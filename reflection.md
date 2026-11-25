# PawPal+ Project Reflection

## 1. System Design

**Core user actions**

1. **Add a pet** – The owner enters a pet's name, species, and age so PawPal+ can track care for it.
2. **Schedule a care task** – The owner adds a task (walk, feeding, medication, appointment) for a specific pet with a time, duration, priority, and how often it repeats (once, daily, weekly).
3. **See today's schedule** – The owner views today's tasks across all pets in time order, with warnings for conflicts, and can mark tasks complete (recurring tasks then roll forward automatically).

**a. Initial design**

My initial UML has four classes with a simple ownership chain: an `Owner` has many `Pet`s, each `Pet` has many `Task`s, and a `Scheduler` reads everything through the `Owner`.

- **Task** (dataclass) – one care activity: description, time (`"HH:MM"`), duration, priority, frequency (`once`/`daily`/`weekly`), due date, and completion status. It can mark itself complete and produce its next occurrence if it recurs.
- **Pet** (dataclass) – a pet's details (name, species, age) plus its own list of tasks; it adds, removes, and returns its tasks.
- **Owner** – the person using the app: name, how many minutes they have for pet care per day, and their pets. It adds/looks up pets and gathers every task across all pets.
- **Scheduler** – the "brain." It holds a reference to the `Owner` (not a copy of the tasks) and is responsible for everything that spans pets: today's tasks, sorting by time, filtering by pet/status, conflict detection, completing tasks (including rolling recurring ones forward), and generating a plan that fits the owner's available time.

I kept `Task` and `Pet` as dataclasses because they are mostly data, and made `Owner` and `Scheduler` regular classes because they are mostly behavior.

**b. Design changes**

Yes — after asking the AI to review the skeleton for missing relationships and bottlenecks, I made two changes:

1. **Added `pet_name` to `Task`.** In the first skeleton a task had no link back to its pet. Since `Owner.get_all_tasks()` flattens everything into one list, the Scheduler couldn't say which pet a task or conflict belonged to without nested loops everywhere. `Pet.add_task()` now stamps the pet's name onto the task.
2. **Added `Task.__post_init__` to normalize times.** Times are stored as `"HH:MM"` strings so they're easy to read and type, but `"9:00"` sorts *after* `"10:00"` as a string. Normalizing every time to zero-padded `HH:MM` when the task is created means plain string sorting is also chronological sorting, and bad input fails early.

One suggestion I did *not* take: making `Task` hold a full reference to its `Pet` object. That creates a circular reference (Pet → Task → Pet) that makes the dataclasses harder to print and compare; a pet name is all the Scheduler actually needs.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers four constraints:

- **Time of day** – every task has an `"HH:MM"` start time, and the day is shown in chronological order.
- **Duration + the owner's available minutes** – `generate_plan()` only keeps tasks that fit into `Owner.available_minutes`.
- **Priority** – high-priority tasks get the time budget first and win ties when two tasks share a start time.
- **Due date / recurrence** – only tasks due today (or unfinished and overdue) show up, and daily/weekly tasks roll forward when completed.

I treated **priority as the most important constraint** because the cost of skipping a task isn't equal: missing a medication or a meal matters far more than skipping grooming. Time of day comes second — it decides the *order* of the day, but not *whether* something happens. Owner preferences (like "no walks after 9pm") were left out to keep the first version simple.

**b. Tradeoffs**

**Conflict detection only warns; it never reschedules.** `detect_conflicts()` reports any pending tasks whose windows overlap (real start/end datetimes, so it also catches a late-night task running into the next morning), but it leaves fixing them to the owner. An automatic rescheduler would have to guess which task to move and where, and could silently push a medication to a time the vet didn't recommend. A warning is reasonable here because the owner knows things the app doesn't — feeding the cat while the dog eats might be perfectly fine, so a hard block would be wrong too.

A second, smaller tradeoff: the planner is **greedy** (highest priority first, shorter first within a priority) instead of finding the mathematically best combination of tasks for the time budget. With 5–10 tasks a day, greedy is easy to explain to the user ("Grooming was skipped because higher-priority tasks used the time"), which matters more than squeezing in one extra low-priority task.

**Readability vs. "Pythonic":** when I asked the AI to simplify `detect_conflicts()`, it offered a single list comprehension over `itertools.combinations`. It was shorter, but the overlap condition and the "same time" vs. "overlap" label were buried inside one expression, so I kept an explicit loop. Later, when I fixed the midnight bug, I switched from checking every pair with `itertools.combinations` to a sorted scan that `break`s as soon as a later task starts after the current one ends. That's both faster and, with a one-line comment, still easy to follow.

---

## 3. AI Collaboration

**a. How you used AI**

I used Claude Code (agent mode inside VS Code) for the whole build: brainstorming the four classes and drafting the Mermaid UML, generating the dataclass skeleton, implementing each phase, writing tests, debugging, and drafting documentation.

**Most effective features:**
- **Agent mode with multi-file edits** – recurrence touched `Task`, `Scheduler`, `main.py`, the tests and the README at once; having the agent edit them together kept everything consistent.
- **Running code, not just writing it** – the agent ran `python main.py`, `python -m pytest`, and even drove the Streamlit app headlessly with `AppTest` after every change, so bugs showed up immediately (for example, it noticed tomorrow's recurring walk sorting in among today's tasks because the sort ignored the date).
- **Review-style prompts** – asking "what relationships are missing / where are the bottlenecks?" about the skeleton produced the two most useful design changes (`Task.pet_name` and time normalization).

**Most helpful prompts:** specific, checkable questions — "Why is this failing, and is the bug in my test or my logic?", "What edge cases matter for sorting and recurring tasks?", and "How could this be simplified?" — worked far better than "make it better."

**Staying organized:** instead of separate chat sessions per phase, I worked phase-by-phase with an explicit **checkpoint after every phase**, where the AI stopped, summarized what changed, and waited for my go-ahead. That gave the same benefit separate sessions would — each phase had a clear scope and a clean commit — while keeping the design context, so later phases didn't contradict earlier decisions.

**b. Judgment and verification**

A few AI suggestions I rejected or modified:
- **Shorter but less readable code.** The AI offered a one-expression list comprehension for `detect_conflicts()`. I kept an explicit loop because the overlap rule and the "same time"/"overlap" label were hidden inside the one-liner.
- **Circular references.** Giving each `Task` a reference to its whole `Pet` object was an option; I kept just `pet_name` to avoid a Pet → Task → Pet cycle.
- **Deferring known bugs.** At the end of testing, the AI listed two gaps — tasks crossing midnight couldn't conflict, and completing an overdue recurring task created a "next" task in the past — and proposed leaving them as future work. I decided to fix them right away instead, since both would give an owner wrong information.

How I verified: every change was checked by running the demo and the test suite, not by reading the code and trusting it. For the test suite specifically, I didn't just accept "all tests pass" — we deliberately broke the logic (flipping `<` to `<=` in the conflict check, removing the recurrence `timedelta`, simplifying the sort key, removing the overdue catch-up loop) and confirmed the right tests failed each time.

---

## 4. Testing and Verification

**a. What you tested**

The suite (45 tests) covers: task completion and addition, input validation, sorting (including the `"9:00"` vs `"10:00"` string trap and priority tie-breaks), recurrence (daily/weekly, one-off tasks, month/year/leap-day boundaries, overdue and early completions), conflict detection (exact matches, overlapping durations, back-to-back tasks that should *not* conflict, completed tasks, different days, tasks running past midnight), filtering, "today" view with overdue tasks, and plan generation within a time budget.

These mattered because they're the behaviors an owner relies on without double-checking: if recurrence silently stopped creating tomorrow's medication, or sorting put 10:00 before 9:00, the app would look fine but give wrong advice. The boundary tests (back-to-back tasks, Dec 31 → Jan 1) are where off-by-one bugs usually hide.

**b. Confidence**

About **4 out of 5**. All 45 tests pass, and I checked that the tests have teeth by deliberately breaking the conflict boundary, the recurrence date math, the sort key, the overdue catch-up loop, and cross-midnight detection — each broke the matching tests.

Writing this list of edge cases actually exposed two real bugs, which I then fixed: tasks running past midnight couldn't conflict with next-morning tasks (conflict detection only compared times within one day), and completing an overdue recurring task created a "next" task that was still in the past. Both now have tests. I'm holding back one point because the Streamlit UI is only smoke-tested.

Next edge cases I'd test:
- Two pending tasks with the same description for the same pet (which one does `mark_task_complete` pick?).
- Daylight-saving transitions, where a day is 23 or 25 hours long.
- Very large numbers of overlapping tasks (worst case for the conflict scan, since it can't stop early).

---

## 5. Reflection

**a. What went well**

I'm most satisfied with the scheduling logic and its test suite. The `Scheduler` reads live data through the `Owner` instead of copying it, so the CLI demo, the tests and the Streamlit app all use exactly the same logic. The 45 tests cover real edge cases (back-to-back tasks, midnight, leap day, overdue recurring tasks), and I know they work because they caught every bug we planted.

**b. What you would improve**

- **Persistence** – data lives in `st.session_state`, so it disappears when the browser tab closes. Saving to a JSON file or SQLite would make it actually usable day to day.
- **Editing tasks and stable IDs** – tasks are found by pet + description, so two tasks with the same name for the same pet are ambiguous. A task ID would fix that and make "edit" and "delete" in the UI straightforward.
- **Smarter planning** – the plan is greedy and only warns about conflicts. A next version could suggest a free time slot for a conflicting task, and support owner preferences (e.g. "no walks after 9 pm").
- **Time zones / daylight saving** – times are naive local times, which is fine for one household but not for travel.

**c. Key takeaway**

Being the "lead architect" with a powerful AI means owning the **decisions and the verification**, not the typing. The AI could produce a whole working class in seconds, but it was my job to keep the design small (four classes, clear responsibilities), decide which suggestions fit, and insist on evidence — a passing demo, passing tests, and tests that fail when the code is wrong. The most valuable moments weren't when the AI wrote code; they were when a pointed question ("what edge cases would break this?") surfaced a real bug that I then chose to fix rather than defer.
