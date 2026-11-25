"""PawPal+ logic layer: core classes for pets, owners, tasks, and scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from itertools import combinations

VALID_PRIORITIES = ("low", "medium", "high")
VALID_FREQUENCIES = ("once", "daily", "weekly")
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
RECURRENCE_STEP = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}


def to_minutes(hhmm: str) -> int:
    """Convert an "HH:MM" string to minutes after midnight."""
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


@dataclass
class Task:
    """A single pet care activity scheduled at a time of day."""

    description: str
    time: str  # "HH:MM", 24-hour clock
    duration_minutes: int = 15
    priority: str = "medium"  # "low" | "medium" | "high"
    frequency: str = "once"  # "once" | "daily" | "weekly"
    due_date: date = field(default_factory=date.today)
    completed: bool = False
    pet_name: str = ""  # set by Pet.add_task so the Scheduler knows who the task is for

    def __post_init__(self) -> None:
        """Validate fields and normalize time to zero-padded "HH:MM"."""
        try:
            hours, minutes = (int(part) for part in self.time.strip().split(":"))
        except ValueError:
            raise ValueError(f"Time must look like HH:MM, got {self.time!r}") from None
        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            raise ValueError(f"Time out of range: {self.time!r}")
        self.time = f"{hours:02d}:{minutes:02d}"

        self.priority = self.priority.lower()
        self.frequency = self.frequency.lower()
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(f"Priority must be one of {VALID_PRIORITIES}, got {self.priority!r}")
        if self.frequency not in VALID_FREQUENCIES:
            raise ValueError(f"Frequency must be one of {VALID_FREQUENCIES}, got {self.frequency!r}")
        if self.duration_minutes <= 0:
            raise ValueError("Duration must be a positive number of minutes")

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    @property
    def end_minutes(self) -> int:
        """Minutes after midnight when this task ends."""
        return to_minutes(self.time) + self.duration_minutes

    def next_occurrence(self) -> Task | None:
        """Return a fresh, incomplete copy due one day/week later, or None for one-off tasks.

        Uses timedelta so month and year boundaries (e.g. Jan 31 -> Feb 1) are handled correctly.
        """
        step = RECURRENCE_STEP.get(self.frequency)
        if step is None:
            return None
        return replace(self, due_date=self.due_date + step, completed=False)


@dataclass
class Pet:
    """A pet and the care tasks that belong to it."""

    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet and tag it with the pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, description: str) -> bool:
        """Remove the first task with this description; return True if one was removed."""
        for i, task in enumerate(self.tasks):
            if task.description == description:
                del self.tasks[i]
                return True
        return False

    def get_tasks(self) -> list[Task]:
        """Return a copy of this pet's task list."""
        return list(self.tasks)


class Owner:
    """A pet owner who manages one or more pets."""

    def __init__(self, name: str, available_minutes: int = 120) -> None:
        """Create an owner with a daily time budget for pet care."""
        self.name = name
        self.available_minutes = available_minutes
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet, rejecting duplicate names (case-insensitive)."""
        if self.get_pet(pet.name) is not None:
            raise ValueError(f"{self.name} already has a pet named {pet.name!r}")
        self.pets.append(pet)

    def get_pet(self, name: str) -> Pet | None:
        """Look up a pet by name (case-insensitive), or None if not found."""
        for pet in self.pets:
            if pet.name.lower() == name.lower():
                return pet
        return None

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]


class Scheduler:
    """The 'brain' that organizes tasks across all of an owner's pets."""

    def __init__(self, owner: Owner) -> None:
        """Create a scheduler that reads live data from the given owner."""
        self.owner = owner

    def get_todays_tasks(self, today: date | None = None) -> list[Task]:
        """Return today's tasks plus unfinished overdue ones, sorted by time.

        Completed tasks from earlier days are dropped so history doesn't clutter today.
        """
        today = today or date.today()
        tasks = [
            task for task in self.owner.get_all_tasks()
            if task.due_date == today or (task.due_date < today and not task.completed)
        ]
        return self.sort_by_time(tasks)

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return a new list in chronological order (date, then time), high priority first on ties.

        Task times are normalized to zero-padded "HH:MM", so plain string order is chronological.
        """
        return sorted(tasks, key=lambda t: (t.due_date, t.time, PRIORITY_RANK[t.priority]))

    def filter_tasks(
        self,
        pet_name: str | None = None,
        completed: bool | None = None,
        tasks: list[Task] | None = None,
    ) -> list[Task]:
        """Return tasks matching a pet name (case-insensitive) and/or completion status.

        Leaving a filter as None means "don't filter on this". Defaults to all of the owner's tasks.
        """
        tasks = self.owner.get_all_tasks() if tasks is None else tasks
        return [
            t for t in tasks
            if (pet_name is None or t.pet_name.lower() == pet_name.lower())
            and (completed is None or t.completed == completed)
        ]

    def detect_conflicts(self, tasks: list[Task] | None = None) -> list[str]:
        """Return a warning for every pair of pending, same-day tasks whose time windows overlap.

        Lightweight by design: it never raises or reschedules, it only reports. Checks every
        pair (O(n^2)), which is fine for the handful of tasks a household has per day.
        """
        tasks = self.get_todays_tasks() if tasks is None else tasks
        pending = self.sort_by_time([t for t in tasks if not t.completed])
        warnings = []
        for a, b in combinations(pending, 2):
            if a.due_date != b.due_date:
                continue
            if to_minutes(b.time) < a.end_minutes:  # b starts before a finishes
                kind = "same time" if a.time == b.time else "overlap"
                warnings.append(
                    f"Conflict ({kind}): {a.pet_name}'s '{a.description}' "
                    f"({a.time}, {a.duration_minutes} min) and {b.pet_name}'s "
                    f"'{b.description}' ({b.time}, {b.duration_minutes} min)"
                )
        return warnings

    def mark_task_complete(self, pet_name: str, description: str) -> Task | None:
        """Complete a pet's earliest pending task with this description.

        If the task repeats, its next occurrence is added to the same pet automatically.
        Returns the new occurrence for recurring tasks, the completed task otherwise,
        or None if no matching pending task exists.
        """
        pet = self.owner.get_pet(pet_name)
        if pet is None:
            return None
        matches = [t for t in pet.tasks if t.description == description and not t.completed]
        if not matches:
            return None
        task = min(matches, key=lambda t: (t.due_date, t.time))
        task.mark_complete()
        upcoming = task.next_occurrence()
        if upcoming is not None:
            pet.add_task(upcoming)
            return upcoming
        return task

    def generate_plan(self, today: date | None = None) -> tuple[list[Task], list[Task]]:
        """Pick today's pending tasks that fit the owner's available minutes.

        Greedy: considers high-priority tasks first (shorter ones first within a priority),
        keeps each task that still fits the time budget, then returns (planned, skipped)
        with the planned tasks in time order.
        """
        pending = [t for t in self.get_todays_tasks(today) if not t.completed]
        by_importance = sorted(pending, key=lambda t: (PRIORITY_RANK[t.priority], t.duration_minutes))
        budget = self.owner.available_minutes
        planned, skipped = [], []
        for task in by_importance:
            if task.duration_minutes <= budget:
                planned.append(task)
                budget -= task.duration_minutes
            else:
                skipped.append(task)
        return self.sort_by_time(planned), skipped

    def explain_plan(self, planned: list[Task], skipped: list[Task]) -> list[str]:
        """Return human-readable reasons for what made it into the plan and what didn't."""
        used = sum(t.duration_minutes for t in planned)
        lines = [f"Planned {len(planned)} task(s) using {used} of {self.owner.available_minutes} available minutes."]
        lines += [
            f"Skipped '{t.description}' for {t.pet_name} ({t.duration_minutes} min, {t.priority} priority): "
            "not enough time left after higher-priority tasks."
            for t in skipped
        ]
        return lines
