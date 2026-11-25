"""CLI demo for PawPal+: exercises scheduling, sorting, filtering, conflicts, and recurrence."""

from pawpal_system import Owner, Pet, Scheduler, Task


def print_schedule(title: str, tasks: list[Task]) -> None:
    """Print tasks as an aligned, readable table."""
    print(f"\n{title}")
    print("=" * 70)
    if not tasks:
        print("  (no tasks)")
        return
    print(f"  {'Due':<10} {'Time':<6} {'Pet':<8} {'Task':<20} {'Min':>4}  {'Priority':<8} {'Repeats':<7} Done")
    print("  " + "-" * 66)
    for t in tasks:
        done = "[x]" if t.completed else "[ ]"
        print(
            f"  {t.due_date:%m-%d}      {t.time:<6} {t.pet_name:<8} {t.description:<20} "
            f"{t.duration_minutes:>4}  {t.priority:<8} {t.frequency:<7} {done}"
        )


def main() -> None:
    owner = Owner("Jordan", available_minutes=60)
    mochi = Pet("Mochi", "dog", age=3)
    luna = Pet("Luna", "cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Added deliberately out of order; two tasks share 08:00 to trigger a conflict.
    luna.add_task(Task("Play session", "18:00", 15, "medium", "daily"))
    mochi.add_task(Task("Breakfast", "8:00", 10, "high", "daily"))
    luna.add_task(Task("Flea medication", "08:00", 5, "high", "weekly"))
    mochi.add_task(Task("Morning walk", "07:30", 20, "high", "daily"))
    mochi.add_task(Task("Grooming", "10:00", 40, "low"))

    scheduler = Scheduler(owner)
    print(f"PawPal+ for {owner.name} ({len(owner.pets)} pets, {owner.available_minutes} min available)")

    print_schedule("Tasks in the order they were added", owner.get_all_tasks())
    print_schedule("Today's Schedule (sorted by time)", scheduler.get_todays_tasks())

    print("\nConflict check")
    print("=" * 70)
    for warning in scheduler.detect_conflicts() or ["  No conflicts."]:
        print(f"  {warning}")

    print_schedule("Filter: Luna's tasks only", scheduler.sort_by_time(scheduler.filter_tasks(pet_name="luna")))

    nxt = scheduler.mark_task_complete("Mochi", "Morning walk")
    print(f"\nCompleted Mochi's daily 'Morning walk' -> next one auto-created for {nxt.due_date}")
    print_schedule("Filter: completed tasks", scheduler.filter_tasks(completed=True))
    print_schedule("Mochi's tasks (note tomorrow's walk)", scheduler.sort_by_time(mochi.get_tasks()))

    planned, skipped = scheduler.generate_plan()
    print_schedule(f"Today's Plan (fits in {owner.available_minutes} min)", planned)
    for line in scheduler.explain_plan(planned, skipped):
        print(f"  * {line}")


if __name__ == "__main__":
    main()
