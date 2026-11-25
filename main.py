"""CLI demo for PawPal+: builds an owner with pets and prints today's schedule."""

from pawpal_system import Owner, Pet, Scheduler, Task


def print_schedule(title: str, tasks: list[Task]) -> None:
    """Print tasks as an aligned, readable table."""
    print(f"\n{title}")
    print("=" * 62)
    if not tasks:
        print("  (no tasks)")
        return
    print(f"  {'Time':<6} {'Pet':<8} {'Task':<22} {'Min':>4}  {'Priority':<8} Done")
    print("  " + "-" * 58)
    for t in tasks:
        done = "[x]" if t.completed else "[ ]"
        print(f"  {t.time:<6} {t.pet_name:<8} {t.description:<22} {t.duration_minutes:>4}  {t.priority:<8} {done}")


def main() -> None:
    owner = Owner("Jordan", available_minutes=90)
    mochi = Pet("Mochi", "dog", age=3)
    luna = Pet("Luna", "cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    mochi.add_task(Task("Morning walk", "07:30", 30, "high", "daily"))
    mochi.add_task(Task("Breakfast", "08:00", 10, "high", "daily"))
    luna.add_task(Task("Flea medication", "09:00", 5, "high", "weekly"))
    luna.add_task(Task("Play session", "18:00", 15, "medium", "daily"))

    scheduler = Scheduler(owner)
    print(f"PawPal+ for {owner.name} ({len(owner.pets)} pets)")
    print_schedule("Today's Schedule", scheduler.get_todays_tasks())

    scheduler.mark_task_complete("Mochi", "Morning walk")
    print_schedule("After completing Mochi's morning walk", scheduler.get_todays_tasks())


if __name__ == "__main__":
    main()
