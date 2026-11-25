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

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

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
