import datetime as dt

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Plan and track care for all your pets in one place.")

# --- Application memory -------------------------------------------------------
# Streamlit reruns this script top-to-bottom on every interaction, so the Owner
# is created only once and kept in session_state ("the vault") after that.
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan", available_minutes=120)

owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)  # cheap to rebuild: it reads live data from the owner

# --- Owner --------------------------------------------------------------------
st.subheader("👤 Owner")
col1, col2 = st.columns(2)
with col1:
    owner.name = st.text_input("Owner name", value=owner.name)
with col2:
    owner.available_minutes = int(
        st.number_input("Minutes available today", min_value=0, max_value=1440,
                        value=owner.available_minutes, step=15)
    )

# --- Add a pet ----------------------------------------------------------------
st.subheader("🐶 Pets")
with st.form("add_pet", clear_on_submit=True):
    c1, c2, c3 = st.columns([2, 1, 1])
    pet_name = c1.text_input("Pet name")
    species = c2.selectbox("Species", ["dog", "cat", "other"])
    age = c3.number_input("Age", min_value=0, max_value=40, value=1)
    if st.form_submit_button("Add pet"):
        if not pet_name.strip():
            st.error("Please enter a pet name.")
        else:
            try:
                owner.add_pet(Pet(pet_name.strip(), species, int(age)))
                st.success(f"Added {pet_name.strip()} 🎉")
            except ValueError as err:
                st.error(str(err))

if owner.pets:
    st.table([{"Name": p.name, "Species": p.species, "Age": p.age, "Tasks": len(p.tasks)}
              for p in owner.pets])
else:
    st.info("No pets yet. Add one above to start scheduling tasks.")
    if st.button("Or load sample pets and tasks"):
        mochi, luna = Pet("Mochi", "dog", 3), Pet("Luna", "cat", 5)
        owner.add_pet(mochi)
        owner.add_pet(luna)
        mochi.add_task(Task("Morning walk", "07:30", 20, "high", "daily"))
        mochi.add_task(Task("Breakfast", "08:00", 10, "high", "daily"))
        luna.add_task(Task("Flea medication", "08:00", 5, "high", "weekly"))
        mochi.add_task(Task("Grooming", "10:00", 40, "low"))
        luna.add_task(Task("Play session", "18:00", 15, "medium", "daily"))
        st.rerun()

# --- Schedule a task ----------------------------------------------------------
if owner.pets:
    st.subheader("📝 Schedule a task")
    with st.form("add_task", clear_on_submit=True):
        c1, c2 = st.columns(2)
        target = c1.selectbox("For pet", [p.name for p in owner.pets])
        description = c2.text_input("Task", placeholder="Morning walk")
        c3, c4, c5, c6 = st.columns(4)
        time = c3.time_input("Time", value=dt.time(8, 0), step=dt.timedelta(minutes=15))
        duration = c4.number_input("Minutes", min_value=1, max_value=240, value=20)
        priority = c5.selectbox("Priority", ["high", "medium", "low"])
        frequency = c6.selectbox("Repeats", ["once", "daily", "weekly"])
        if st.form_submit_button("Add task"):
            if not description.strip():
                st.error("Please describe the task.")
            else:
                task = Task(description.strip(), time.strftime("%H:%M"), int(duration),
                            priority, frequency)
                owner.get_pet(target).add_task(task)
                st.success(f"Scheduled '{task.description}' for {target} at {task.time}.")

PRIORITY_BADGE = {"high": "🔴 high", "medium": "🟡 medium", "low": "🟢 low"}


def task_rows(tasks: list[Task], show_date: bool = False) -> list[dict]:
    """Turn Task objects into table rows for st.table."""
    rows = []
    for t in tasks:
        row = {"Date": t.due_date.strftime("%a %b %d")} if show_date else {}
        row.update({"Time": t.time, "Pet": t.pet_name, "Task": t.description,
                    "Minutes": t.duration_minutes, "Priority": PRIORITY_BADGE[t.priority],
                    "Repeats": t.frequency, "Done": "✅" if t.completed else "⬜"})
        rows.append(row)
    return rows


# --- Today's schedule ---------------------------------------------------------
st.divider()
st.subheader("📅 Today's schedule")

# A message saved before st.rerun() so it survives the rerun.
if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))

todays = scheduler.get_todays_tasks()  # already sorted by Scheduler.sort_by_time()
if not todays:
    st.info("Nothing scheduled for today yet.")
else:
    # Conflicts go first so the owner sees them before reading the list.
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        st.warning(
            f"**{len(conflicts)} scheduling conflict(s)** — you can't be in two places at once. "
            "Consider moving one of these tasks:\n\n" + "\n".join(f"- {c}" for c in conflicts)
        )
    else:
        st.success("No conflicts — every task has its own time slot.")

    c1, c2 = st.columns(2)
    pet_filter = c1.selectbox("Show pet", ["All pets"] + [p.name for p in owner.pets])
    status_filter = c2.radio("Show", ["All", "To do", "Done"], horizontal=True)
    shown = scheduler.filter_tasks(
        pet_name=None if pet_filter == "All pets" else pet_filter,
        completed={"All": None, "To do": False, "Done": True}[status_filter],
        tasks=todays,
    )
    if shown:
        st.table(task_rows(shown))
    else:
        st.caption("No tasks match these filters.")

    done = sum(t.completed for t in todays)
    st.progress(done / len(todays), text=f"{done} of {len(todays)} tasks done today")

    pending = [t for t in todays if not t.completed]
    if pending:
        labels = {f"{t.time} · {t.pet_name} · {t.description}": t for t in pending}
        c1, c2 = st.columns([3, 1])
        choice = c1.selectbox("Mark a task complete", list(labels))
        if c2.button("Mark done"):
            t = labels[choice]
            result = scheduler.mark_task_complete(t.pet_name, t.description)
            msg = f"Nice! '{t.description}' for {t.pet_name} is done."
            if result is not None and result is not t:
                msg += f" Next {result.frequency} occurrence added for {result.due_date:%a %b %d}."
            st.session_state.flash = msg
            st.rerun()

# --- Daily plan ---------------------------------------------------------------
st.divider()
st.subheader("🧠 Build today's plan")
st.caption(f"Fits your pending tasks into **{owner.available_minutes} minutes**, "
           "highest priority first, then lists them in time order.")
if st.button("Generate plan", type="primary"):
    planned, skipped = scheduler.generate_plan()
    reasons = scheduler.explain_plan(planned, skipped)
    if not planned and not skipped:
        st.info("Nothing left to plan today. 🎉")
    else:
        st.success(reasons[0])
        if planned:
            st.table(task_rows(planned))
        for reason in reasons[1:]:
            st.warning(reason)

# --- Upcoming -----------------------------------------------------------------
upcoming = scheduler.sort_by_time(
    [t for t in owner.get_all_tasks() if t.due_date > dt.date.today() and not t.completed]
)
if upcoming:
    with st.expander(f"🔁 Upcoming ({len(upcoming)}) — includes auto-created recurring tasks"):
        st.table(task_rows(upcoming, show_date=True))
