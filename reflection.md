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

**Conflict detection only warns; it never reschedules.** `detect_conflicts()` checks every pair of pending same-day tasks and reports any whose windows overlap (start time + duration), but it leaves fixing them to the owner. An automatic rescheduler would have to guess which task to move and where, and could silently push a medication to a time the vet didn't recommend. A warning is reasonable here because the owner knows things the app doesn't — feeding the cat while the dog eats might be perfectly fine, so a hard block would be wrong too.

A second, smaller tradeoff: the planner is **greedy** (highest priority first, shorter first within a priority) instead of finding the mathematically best combination of tasks for the time budget. With 5–10 tasks a day, greedy is easy to explain to the user ("Grooming was skipped because higher-priority tasks used the time"), which matters more than squeezing in one extra low-priority task.

**Readability vs. "Pythonic":** when I asked the AI to simplify `detect_conflicts()`, it offered a single list comprehension over `itertools.combinations`. It was shorter, but the overlap condition and the "same time" vs. "overlap" label were buried inside one expression, so I kept the explicit loop (while still using `combinations` to avoid a hand-written nested index loop).

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
