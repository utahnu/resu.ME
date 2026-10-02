import streamlit as st

SAGE = "#3F6C73"
SAGE_LIGHT = "#E9EFEC"
CLAY = "#C99A7A"
INK = "#2B3A42"
MUTED = "#6B7A80"
LINE = "#E3DED3"

FORM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600&display=swap');

/* cards */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: white;
    border: 1px solid {LINE} !important;
    border-radius: 16px !important;
    padding: 0.4rem 0.6rem 0.6rem;
    box-shadow: 0 2px 10px rgba(63, 108, 115, 0.06);
}}

/* section headers */
.sec-head {{display: flex; align-items: center; gap: 12px; margin: 0.3rem 0 0.9rem;}}
.sec-num {{
    flex: none; width: 34px; height: 34px; line-height: 34px; text-align: center;
    border-radius: 50%; background: {SAGE}; color: white; font-weight: 600;
}}
.sec-title {{font-family: 'Fraunces', Georgia, serif; font-size: 1.2rem; color: {INK}; line-height: 1.2;}}
.sec-sub {{color: {MUTED}; font-size: 0.88rem;}}
.optional {{
    display: inline-block; margin-left: 8px; padding: 1px 9px; border-radius: 20px;
    background: #F3E6DC; color: #9A6B4B; font-size: 0.72rem; font-family: sans-serif; vertical-align: middle;
}}

/* inputs */
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-baseweb="select"] > div {{
    border-radius: 10px !important;
    background: #FCFBF8 !important;
    border: 1px solid {LINE} !important;
}}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus {{
    border-color: {SAGE} !important;
    box-shadow: 0 0 0 3px rgba(63, 108, 115, 0.15) !important;
}}
label p {{color: {INK}; font-weight: 500; font-size: 0.92rem;}}

/* radius readout */
.radius-readout {{
    text-align: center; background: {SAGE_LIGHT}; border-radius: 12px; padding: 0.5rem 0.2rem;
}}
.radius-readout .big {{font-family: 'Fraunces', Georgia, serif; font-size: 2rem; color: {SAGE}; line-height: 1.1;}}
.radius-readout .unit {{color: {MUTED}; font-size: 0.8rem;}}
.anywhere {{
    background: {SAGE_LIGHT}; color: {INK}; border-radius: 10px; padding: 0.7rem 1rem; font-size: 0.92rem;
}}

/* submit button */
.stButton > button {{
    background: {SAGE}; color: white; border: none; border-radius: 12px;
    padding: 0.75rem 1.6rem; font-weight: 600; font-size: 1.05rem;
    transition: background 0.15s, transform 0.1s;
}}
.stButton > button:hover {{background: #335A60; color: white; transform: translateY(-1px);}}
.stButton > button:active {{transform: translateY(0);}}
</style>
"""


def section_header(num, title, subtitle, optional=False):
    badge = '<span class="optional">Optional</span>' if optional else ""
    st.markdown(
        f'<div class="sec-head"><span class="sec-num">{num}</span>'
        f'<div><div class="sec-title">{title}{badge}</div>'
        f'<div class="sec-sub">{subtitle}</div></div></div>',
        unsafe_allow_html=True,
    )


def render_profile_form():
    """Draw the user input form. Returns the profile dict when the user submits, else None."""
    st.markdown(FORM_CSS, unsafe_allow_html=True)
    st.header("Tell us about you")

    # ----- 1. About you -----
    with st.container(border=True):
        section_header("1", "About you", "The basics, so we can match events to you.")
        name = st.text_input("Name", placeholder="Jordan Smith", key="pf_name")
        c1, c2 = st.columns(2)
        major = c1.text_input("Major", placeholder="Computer Science", key="pf_major")
        location = c2.text_input("Location", placeholder="City, State or ZIP code", key="pf_location")

    st.write("")

    # ----- 2. Travel range -----
    with st.container(border=True):
        section_header("2", "Travel range", "How far are you comfortable going for an event?")
        use_radius = st.toggle("Limit events to a travel radius", value=True, key="pf_use_radius")

        radius, unit = None, "miles"
        if use_radius:
            unit = st.segmented_control("Distance unit", ["miles", "km"], default="miles", key="pf_unit") or "miles"
            s1, s2 = st.columns([4, 1.3], vertical_alignment="center")
            radius = s1.slider("Radius", 5, 200, 25, step=5, label_visibility="collapsed", key="pf_radius")
            s2.markdown(
                f'<div class="radius-readout"><div class="big">{radius}</div><div class="unit">{unit}</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="anywhere">No limit set. We\'ll include events from anywhere, including virtual ones.</div>',
                unsafe_allow_html=True,
            )

    st.write("")

    # ----- 3. Preferences -----
    with st.container(border=True):
        section_header("3", "Preferences", "Help us find better matches.", optional=True)
        year = st.selectbox(
            "Year in school",
            ["Prefer not to say", "Freshman", "Sophomore", "Junior", "Senior", "Graduate student", "Recent graduate"],
            key="pf_year",
        )
        event_types = st.pills(
            "What kinds of events interest you?",
            ["Career fairs", "Networking mixers", "Workshops", "Hackathons", "Guest speakers", "Info sessions", "Volunteering"],
            selection_mode="multi",
            key="pf_types",
        )
        include_virtual = st.toggle("Include virtual events", value=True, key="pf_virtual")
        notes = st.text_area(
            "Anything else we should know?",
            placeholder="Career goals, industries you like, and so on.",
            key="pf_notes",
        )

    st.write("")

    # ----- Submit -----
    if st.button("Find events for me", use_container_width=True, key="pf_submit"):
        missing = [label for label, val in (("name", name), ("major", major), ("location", location)) if not val.strip()]
        if missing:
            st.warning("Please fill in your " + ", ".join(missing) + ".")
            return None
        return {
            "name": name.strip(),
            "major": major.strip(),
            "location": location.strip(),
            "radius": radius,  # None means no limit
            "radius_unit": unit,
            "year": year,
            "event_types": event_types or [],
            "include_virtual": include_virtual,
            "notes": notes.strip(),
        }
    return None


if __name__ == "__main__":
    st.set_page_config(page_title="resu.ME form", page_icon="📄", layout="centered")
    profile = render_profile_form()
    if profile:
        st.success(f"Thanks, {profile['name']}!")
        st.json(profile)