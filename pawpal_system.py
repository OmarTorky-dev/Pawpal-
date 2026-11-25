"""PawPal+ logic layer: core classes for pets, owners, tasks, and scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

VALID_PRIORITIES = ("low", "medium", "high")
VALID_FREQUENCIES = ("once", "daily", "weekly")


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

    def next_occurrence(self) -> Task | None:
        """Return the next instance of a recurring task (implemented in Phase 4)."""
        raise NotImplementedError


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
        """Return tasks due on (or overdue before) today."""
        today = today or date.today()
        return [task for task in self.owner.get_all_tasks() if task.due_date <= today]

    def mark_task_complete(self, pet_name: str, description: str) -> Task | None:
        """Mark a pet's pending task complete; return it, or None if not found."""
        pet = self.owner.get_pet(pet_name)
        if pet is None:
            return None
        for task in pet.tasks:
            if task.description == description and not task.completed:
                task.mark_complete()
                return task
        return None

    # --- Algorithmic layer (implemented in Phase 4) ---

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by time of day."""
        raise NotImplementedError

    def filter_tasks(self, pet_name: str | None = None, completed: bool | None = None) -> list[Task]:
        """Return tasks matching a pet name and/or completion status."""
        raise NotImplementedError

    def detect_conflicts(self, tasks: list[Task]) -> list[str]:
        """Return warning messages for tasks scheduled at the same time."""
        raise NotImplementedError

    def generate_plan(self) -> list[Task]:
        """Choose and order today's tasks to fit the owner's available time."""
        raise NotImplementedError
