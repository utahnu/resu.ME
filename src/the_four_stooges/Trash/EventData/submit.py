"""Streamlit pieces for user-submitted events. Import and call from app.py."""
import os
from datetime import date

import streamlit as st

import db

EVENT_TYPES = ["Career fairs", "Networking mixers", "Workshops", "Hackathons",
               "Guest speakers", "Info sessions", "Volunteering", "Other"]


def render_submit_form():
    st.divider()
    st.header("Know of an event? Add it")
    st.caption("Submissions are reviewed before they appear for other students.")

    with st.form("submit_event", clear_on_submit=True):
        title = st.text_input("Event name", placeholder="Spring Engineering Career Fair")
        c1, c2 = st.columns(2)
        etype = c1.selectbox("Type", EVENT_TYPES)
        when = c2.date_input("Date", min_value=date.today())
        virtual = st.checkbox("This is a virtual event")
        place = st.text_input("Venue / address", placeholder="Wilkinson Student Center, Provo, UT",
                              help="Leave blank if virtual. A full address lets us place it on the map.")
        url = st.text_input("Link (optional)", placeholder="https://")
        description = st.text_area("What is it? (optional)", max_chars=400)
        school = st.text_input("School (optional)", placeholder="BYU")
        majors = st.text_input("Best for which majors? (optional)", placeholder="cs, engineering")
        website = st.text_input("Leave this empty", key="hp", label_visibility="collapsed")  # honeypot
        submitted = st.form_submit_button("Submit event")

    if not submitted:
        return
    if website:  # bots fill hidden-ish fields
        return
    if not title.strip():
        st.warning("Please add an event name.")
    elif not virtual and not place.strip():
        st.warning("Please add a venue, or mark the event as virtual.")
    elif url.strip() and not url.strip().startswith(("http://", "https://")):
        st.warning("The link should start with http:// or https://")
    else:
        result = db.add_event({
            "title": title, "type": etype, "start": when.isoformat(), "virtual": virtual,
            "place": place.strip(), "url": url.strip(), "description": description.strip(),
            "school": school.strip() or None,
            "majors": ",".join(m.strip().lower() for m in majors.split(",") if m.strip()),
            "source": "user",
        }, status="pending")
        if result == "added":
            st.success("Thanks! Your event is waiting for review.")
        else:
            st.info("That event is already in the system.")


def render_moderation():
    """Hidden unless ADMIN_PASSWORD is set in the environment."""
    admin_pw = os.environ.get("ADMIN_PASSWORD")
    if not admin_pw:
        return
    with st.expander("Admin: review submissions"):
        if st.text_input("Admin password", type="password", key="admin_pw") != admin_pw:
            return
        pending = db.pending_events()
        if not pending:
            st.write("Nothing pending.")
        for e in pending:
            st.markdown(f"**{e['title']}** · {e['type']} · {e['start']}  \n"
                        f"{'Virtual' if e['virtual'] else e['place']}  \n{e['description'] or ''}")
            a, r, _ = st.columns([1, 1, 4])
            if a.button("Approve", key=f"ok_{e['id']}"):
                db.set_status(e["id"], "approved")
                st.rerun()
            if r.button("Reject", key=f"no_{e['id']}"):
                db.set_status(e["id"], "rejected")
                st.rerun()
            st.divider()
