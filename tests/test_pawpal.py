"""Automated tests for the PawPal+ logic layer."""

import os
import sys
from datetime import date, timedelta

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pawpal_system import Owner, Pet, Scheduler, Task  # noqa: E402

TODAY = date(2026, 3, 10)


@pytest.fixture
def household():
    """An owner with two pets and an empty scheduler."""
    owner = Owner("Jordan", available_minutes=60)
    mochi, luna = Pet("Mochi", "dog"), Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    return owner, mochi, luna, Scheduler(owner)


# --- Basics (Phase 2) ---------------------------------------------------------

def test_mark_complete_changes_status():
    task = Task("Morning walk", "07:30")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    pet = Pet("Mochi", "dog")
    assert len(pet.tasks) == 0
    pet.add_task(Task("Breakfast", "08:00"))
    assert len(pet.tasks) == 1
    assert pet.tasks[0].pet_name == "Mochi"


def test_remove_task():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Breakfast", "08:00"))
    assert pet.remove_task("Breakfast") is True
    assert pet.remove_task("Breakfast") is False
    assert pet.tasks == []


def test_owner_aggregates_tasks_across_pets(household):
    owner, mochi, luna, _ = household
    mochi.add_task(Task("Walk", "07:00"))
    luna.add_task(Task("Feed", "08:00"))
    assert {t.description for t in owner.get_all_tasks()} == {"Walk", "Feed"}


def test_duplicate_pet_name_rejected(household):
    owner, *_ = household
    with pytest.raises(ValueError):
        owner.add_pet(Pet("mochi", "dog"))


# --- Validation ---------------------------------------------------------------

def test_time_is_normalized_to_zero_padded():
    assert Task("Walk", "7:05").time == "07:05"


@pytest.mark.parametrize("bad_time", ["25:00", "12:60", "noon", "12", ""])
def test_invalid_time_rejected(bad_time):
    with pytest.raises(ValueError):
        Task("Walk", bad_time)


def test_invalid_priority_and_frequency_rejected():
    with pytest.raises(ValueError):
        Task("Walk", "08:00", priority="urgent")
    with pytest.raises(ValueError):
        Task("Walk", "08:00", frequency="monthly")
    with pytest.raises(ValueError):
        Task("Walk", "08:00", duration_minutes=0)


# --- Sorting ------------------------------------------------------------------

def test_sort_by_time_returns_chronological_order(household):
    _, mochi, luna, scheduler = household
    for desc, time in [("Dinner", "18:00"), ("Walk", "7:30"), ("Meds", "10:00"), ("Brush", "09:15")]:
        mochi.add_task(Task(desc, time, due_date=TODAY))
    times = [t.time for t in scheduler.sort_by_time(mochi.tasks)]
    assert times == ["07:30", "09:15", "10:00", "18:00"]


def test_sort_handles_single_digit_hours():
    # As raw strings "9:00" > "10:00"; normalization must prevent that bug.
    tasks = [Task("B", "10:00", due_date=TODAY), Task("A", "9:00", due_date=TODAY)]
    assert [t.description for t in Scheduler(Owner("x")).sort_by_time(tasks)] == ["A", "B"]


def test_sort_breaks_time_ties_by_priority():
    tasks = [
        Task("Low", "08:00", priority="low", due_date=TODAY),
        Task("High", "08:00", priority="high", due_date=TODAY),
        Task("Medium", "08:00", priority="medium", due_date=TODAY),
    ]
    assert [t.description for t in Scheduler(Owner("x")).sort_by_time(tasks)] == ["High", "Medium", "Low"]


def test_sort_puts_later_dates_after_earlier_ones():
    tasks = [Task("Tomorrow early", "06:00", due_date=TODAY + timedelta(days=1)),
             Task("Today late", "22:00", due_date=TODAY)]
    assert [t.description for t in Scheduler(Owner("x")).sort_by_time(tasks)] == ["Today late", "Tomorrow early"]


def test_sort_empty_list():
    assert Scheduler(Owner("x")).sort_by_time([]) == []


# --- Recurrence ---------------------------------------------------------------

def test_completing_daily_task_creates_next_day_task(household):
    _, mochi, _, scheduler = household
    mochi.add_task(Task("Walk", "07:30", frequency="daily", due_date=TODAY))

    nxt = scheduler.mark_task_complete("Mochi", "Walk")

    assert len(mochi.tasks) == 2
    original, new = mochi.tasks
    assert original.completed is True
    assert new is nxt
    assert new.due_date == TODAY + timedelta(days=1)
    assert new.completed is False
    assert (new.time, new.pet_name, new.frequency) == ("07:30", "Mochi", "daily")


def test_completing_weekly_task_creates_task_one_week_later(household):
    _, _, luna, scheduler = household
    luna.add_task(Task("Flea meds", "09:00", frequency="weekly", due_date=TODAY))
    nxt = scheduler.mark_task_complete("Luna", "Flea meds")
    assert nxt.due_date == TODAY + timedelta(weeks=1)


def test_completing_one_off_task_does_not_recur(household):
    _, mochi, _, scheduler = household
    mochi.add_task(Task("Vet visit", "14:00", frequency="once", due_date=TODAY))
    done = scheduler.mark_task_complete("Mochi", "Vet visit")
    assert done.completed is True
    assert len(mochi.tasks) == 1


@pytest.mark.parametrize("start, expected", [
    (date(2026, 1, 31), date(2026, 2, 1)),    # month boundary
    (date(2026, 12, 31), date(2027, 1, 1)),   # year boundary
    (date(2028, 2, 28), date(2028, 2, 29)),   # leap day
])
def test_daily_recurrence_crosses_calendar_boundaries(start, expected):
    assert Task("Walk", "07:00", frequency="daily", due_date=start).next_occurrence().due_date == expected


def test_completing_twice_rolls_forward_again(household):
    _, mochi, _, scheduler = household
    mochi.add_task(Task("Walk", "07:30", frequency="daily", due_date=TODAY))
    scheduler.mark_task_complete("Mochi", "Walk")
    second = scheduler.mark_task_complete("Mochi", "Walk")
    assert second.due_date == TODAY + timedelta(days=2)
    assert len(mochi.tasks) == 3


def test_mark_complete_unknown_pet_or_task_returns_none(household):
    _, mochi, _, scheduler = household
    mochi.add_task(Task("Walk", "07:30", due_date=TODAY))
    assert scheduler.mark_task_complete("Rex", "Walk") is None
    assert scheduler.mark_task_complete("Mochi", "Swim") is None


# --- Conflict detection -------------------------------------------------------

def test_detects_tasks_at_exact_same_time(household):
    _, mochi, luna, scheduler = household
    mochi.add_task(Task("Breakfast", "08:00", 10, due_date=TODAY))
    luna.add_task(Task("Meds", "08:00", 5, due_date=TODAY))
    warnings = scheduler.detect_conflicts(scheduler.get_todays_tasks(TODAY))
    assert len(warnings) == 1
    assert "same time" in warnings[0]
    assert "Breakfast" in warnings[0] and "Meds" in warnings[0]


def test_detects_overlapping_durations(household):
    _, mochi, _, scheduler = household
    mochi.add_task(Task("Walk", "07:30", 45, due_date=TODAY))     # 07:30-08:15
    mochi.add_task(Task("Breakfast", "08:00", 10, due_date=TODAY))
    warnings = scheduler.detect_conflicts(scheduler.get_todays_tasks(TODAY))
    assert len(warnings) == 1 and "overlap" in warnings[0]


def test_back_to_back_tasks_do_not_conflict(household):
    _, mochi, _, scheduler = household
    mochi.add_task(Task("Walk", "07:30", 30, due_date=TODAY))     # ends exactly 08:00
    mochi.add_task(Task("Breakfast", "08:00", 10, due_date=TODAY))
    assert scheduler.detect_conflicts(scheduler.get_todays_tasks(TODAY)) == []


def test_completed_tasks_are_not_conflicts(household):
    _, mochi, luna, scheduler = household
    mochi.add_task(Task("Breakfast", "08:00", due_date=TODAY, completed=True))
    luna.add_task(Task("Meds", "08:00", due_date=TODAY))
    assert scheduler.detect_conflicts(scheduler.get_todays_tasks(TODAY)) == []


def test_same_time_on_different_days_is_not_a_conflict(household):
    _, mochi, _, scheduler = household
    tasks = [Task("Walk", "08:00", due_date=TODAY), Task("Walk", "08:00", due_date=TODAY + timedelta(days=1))]
    for t in tasks:
        mochi.add_task(t)
    assert scheduler.detect_conflicts(tasks) == []


def test_no_tasks_means_no_conflicts(household):
    *_, scheduler = household
    assert scheduler.detect_conflicts([]) == []


# --- Filtering and today's view -----------------------------------------------

def test_filter_by_pet_name_is_case_insensitive(household):
    _, mochi, luna, scheduler = household
    mochi.add_task(Task("Walk", "07:00"))
    luna.add_task(Task("Feed", "08:00"))
    assert [t.description for t in scheduler.filter_tasks(pet_name="LUNA")] == ["Feed"]


def test_filter_by_completion_and_combined(household):
    _, mochi, luna, scheduler = household
    mochi.add_task(Task("Walk", "07:00", completed=True))
    mochi.add_task(Task("Brush", "09:00"))
    luna.add_task(Task("Feed", "08:00", completed=True))
    assert {t.description for t in scheduler.filter_tasks(completed=True)} == {"Walk", "Feed"}
    assert [t.description for t in scheduler.filter_tasks(pet_name="Mochi", completed=False)] == ["Brush"]
    assert len(scheduler.filter_tasks()) == 3


def test_pet_with_no_tasks(household):
    _, _, luna, scheduler = household
    assert luna.get_tasks() == []
    assert scheduler.filter_tasks(pet_name="Luna") == []
    assert scheduler.get_todays_tasks(TODAY) == []


def test_todays_tasks_include_overdue_pending_but_not_old_completed(household):
    _, mochi, _, scheduler = household
    yesterday = TODAY - timedelta(days=1)
    mochi.add_task(Task("Missed meds", "09:00", due_date=yesterday))
    mochi.add_task(Task("Old walk", "07:00", due_date=yesterday, completed=True))
    mochi.add_task(Task("Today walk", "07:00", due_date=TODAY))
    mochi.add_task(Task("Future bath", "07:00", due_date=TODAY + timedelta(days=1)))
    assert [t.description for t in scheduler.get_todays_tasks(TODAY)] == ["Missed meds", "Today walk"]


# --- Plan generation ----------------------------------------------------------

def test_plan_respects_time_budget_and_priority(household):
    owner, mochi, luna, scheduler = household  # 60 minutes available
    mochi.add_task(Task("Walk", "07:00", 30, "high", due_date=TODAY))
    luna.add_task(Task("Play", "18:00", 20, "medium", due_date=TODAY))
    mochi.add_task(Task("Grooming", "10:00", 40, "low", due_date=TODAY))

    planned, skipped = scheduler.generate_plan(TODAY)

    assert [t.description for t in planned] == ["Walk", "Play"]  # time order
    assert [t.description for t in skipped] == ["Grooming"]
    assert sum(t.duration_minutes for t in planned) <= owner.available_minutes
    reasons = scheduler.explain_plan(planned, skipped)
    assert "50 of 60" in reasons[0] and "Grooming" in reasons[1]


def test_plan_skips_completed_tasks_and_handles_empty_day(household):
    _, mochi, _, scheduler = household
    assert scheduler.generate_plan(TODAY) == ([], [])
    mochi.add_task(Task("Walk", "07:00", due_date=TODAY, completed=True))
    assert scheduler.generate_plan(TODAY) == ([], [])


def test_plan_with_zero_minutes_skips_everything(household):
    owner, mochi, _, scheduler = household
    owner.available_minutes = 0
    mochi.add_task(Task("Walk", "07:00", 10, due_date=TODAY))
    planned, skipped = scheduler.generate_plan(TODAY)
    assert planned == [] and len(skipped) == 1
