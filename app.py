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

# --- Today's tasks ------------------------------------------------------------
st.divider()
st.subheader("📅 Today's tasks")
todays = scheduler.get_todays_tasks()
if not todays:
    st.info("Nothing scheduled for today yet.")
else:
    st.table([{"Time": t.time, "Pet": t.pet_name, "Task": t.description,
               "Minutes": t.duration_minutes, "Priority": t.priority,
               "Repeats": t.frequency, "Done": "✅" if t.completed else "⬜"}
              for t in todays])

    pending = [t for t in todays if not t.completed]
    if pending:
        labels = {f"{t.time} · {t.pet_name} · {t.description}": t for t in pending}
        c1, c2 = st.columns([3, 1])
        choice = c1.selectbox("Mark a task complete", list(labels), label_visibility="collapsed")
        if c2.button("Mark done"):
            t = labels[choice]
            scheduler.mark_task_complete(t.pet_name, t.description)
            st.rerun()
