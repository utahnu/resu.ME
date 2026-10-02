import base64
import html
import io
import json
from pathlib import Path

import streamlit as st
from PIL import Image, ImageOps

from backend import events_to_csv, extract_resume_text, recommend_resume_events

# =====================================================================
# resu.ME: complete single-file version
# Run with:  streamlit run main.py
# =====================================================================

# set_page_config must be the first Streamlit command
st.set_page_config(page_title="resu.ME", page_icon="📄", layout="centered")

# ---------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------
SAGE = "#3F6C73"
SAGE_LIGHT = "#E9EFEC"
CLAY = "#C99A7A"
INK = "#2B3A42"
MUTED = "#6B7A80"
LINE = "#E3DED3"

# ---------------------------------------------------------------------
# Styling (one block for the whole site)
# ---------------------------------------------------------------------
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600&display=swap');

#MainMenu, footer {{visibility: hidden;}}
.block-container {{padding-top: 2.5rem; max-width: 760px;}}
h1, h2, h3 {{font-family: 'Fraunces', Georgia, serif !important; color: {INK};}}
h1 {{font-size: 2.4rem !important; line-height: 1.2 !important;}}
hr {{border-color: {LINE} !important;}}

/* top section */
.accent-bar {{width: 64px; height: 4px; background: {CLAY}; border-radius: 2px; margin: 0.8rem 0 1rem;}}
.hero-sub {{color: {MUTED}; font-size: 1.1rem; margin-top: -0.4rem;}}
.who-card {{background: {SAGE_LIGHT}; border-left: 5px solid {SAGE}; border-radius: 12px; padding: 1.3rem 1.6rem; color: {INK};}}
.who-card h3 {{margin: 0 0 0.8rem;}}
.who-grid {{display: grid; grid-template-columns: 1fr 1fr; gap: 1.4rem;}}
.who-grid h4 {{margin: 0 0 0.3rem; color: {SAGE}; font-size: 0.8rem; letter-spacing: 0.08em; text-transform: uppercase;}}
.who-grid p {{margin: 0; line-height: 1.6; font-size: 0.97rem;}}
@media (max-width: 640px) {{.who-grid {{grid-template-columns: 1fr;}}}}

/* how it works */
.step {{background: white; border: 1px solid {LINE}; border-radius: 12px; padding: 1rem; text-align: center; height: 100%;}}
.step .num {{display: inline-block; width: 32px; height: 32px; line-height: 32px; border-radius: 50%;
    background: {CLAY}; color: white; font-weight: 600; margin-bottom: 0.4rem;}}
.step p {{margin: 0; color: {MUTED}; font-size: 0.92rem;}}
.step b {{color: {INK};}}

/* form cards */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: white;
    border: 1px solid {LINE} !important;
    border-radius: 16px !important;
    padding: 0.4rem 0.6rem 0.6rem;
    box-shadow: 0 2px 10px rgba(63, 108, 115, 0.06);
}}
.sec-head {{display: flex; align-items: center; gap: 12px; margin: 0.3rem 0 0.9rem;}}
.sec-num {{flex: none; width: 34px; height: 34px; line-height: 34px; text-align: center;
    border-radius: 50%; background: {SAGE}; color: white; font-weight: 600;}}
.sec-title {{font-family: 'Fraunces', Georgia, serif; font-size: 1.2rem; color: {INK}; line-height: 1.2;}}
.sec-sub {{color: {MUTED}; font-size: 0.88rem;}}
.optional {{display: inline-block; margin-left: 8px; padding: 1px 9px; border-radius: 20px;
    background: #F3E6DC; color: #9A6B4B; font-size: 0.72rem; font-family: sans-serif; vertical-align: middle;}}
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-baseweb="select"] > div {{
    border-radius: 10px !important; background: #FCFBF8 !important; border: 1px solid {LINE} !important;
}}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus {{
    border-color: {SAGE} !important; box-shadow: 0 0 0 3px rgba(63, 108, 115, 0.15) !important;
}}
label p {{color: {INK}; font-weight: 500; font-size: 0.92rem;}}
.radius-readout {{text-align: center; background: {SAGE_LIGHT}; border-radius: 12px; padding: 0.5rem 0.2rem;}}
.radius-readout .big {{font-family: 'Fraunces', Georgia, serif; font-size: 2rem; color: {SAGE}; line-height: 1.1;}}
.radius-readout .unit {{color: {MUTED}; font-size: 0.8rem;}}
.anywhere {{background: {SAGE_LIGHT}; color: {INK}; border-radius: 10px; padding: 0.7rem 1rem; font-size: 0.92rem;}}
.stButton > button {{
    background: {SAGE}; color: white; border: none; border-radius: 12px;
    padding: 0.75rem 1.6rem; font-weight: 600; font-size: 1.05rem;
    transition: background 0.15s, transform 0.1s;
}}
.stButton > button:hover {{background: #335A60; color: white; transform: translateY(-1px);}}
.stButton > button:active {{transform: translateY(0);}}

/* event cards */
.event {{background: white; border: 1px solid {LINE}; border-left: 5px solid {SAGE}; border-radius: 10px;
    padding: 0.9rem 1.2rem; margin-bottom: 0.7rem;}}
.event h4 {{margin: 0 0 0.2rem; font-family: 'Fraunces', Georgia, serif; color: {INK};}}
.event .meta {{color: {MUTED}; font-size: 0.88rem; margin-bottom: 0.3rem;}}
.tag {{display: inline-block; background: {SAGE_LIGHT}; color: {SAGE}; border-radius: 20px;
    padding: 1px 10px; font-size: 0.78rem; margin-right: 6px;}}
.tag.virtual {{background: #F3E6DC; color: #9A6B4B;}}

/* founders */
.founder {{background: white; border: 1px solid {LINE}; border-radius: 16px; padding: 1.2rem 1rem; text-align: center;
    box-shadow: 0 2px 10px rgba(63, 108, 115, 0.06); height: 100%;}}
.avatars {{display: flex; justify-content: center; margin-bottom: 0.7rem;}}
.avatar {{width: 56px; height: 56px; line-height: 56px; border-radius: 50%; color: white; font-weight: 600;
    font-size: 1.1rem; border: 3px solid white;}}
.avatar.photo {{padding: 0; overflow: hidden; background: white;}}
.avatar.photo img {{width: 100%; height: 100%; object-fit: cover; display: block;}}
.avatar + .avatar {{margin-left: -14px;}}
.founder .founder-name {{font-family: 'Fraunces', Georgia, serif; color: {INK}; margin: 0 0 0.15rem; font-size: 1.1rem; font-weight: 600;
    width: 100%; text-align: center !important;}}
.founder .role {{color: {CLAY}; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.5rem;}}
.founder p {{color: {MUTED}; font-size: 0.9rem; line-height: 1.5; margin: 0;}}

div[data-testid="stExpander"] {{background: white; border-radius: 10px;}}
.footer-note {{text-align: center; color: #8A958F; font-size: 0.85rem; margin-top: 2rem;}}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------
# Resume drawing used in the top banner
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# Hero animation: CSS + resume drawing in one place
# ---------------------------------------------------------------------
st.markdown(
    """
<style>
.hero-float {animation: heroFloat 5s ease-in-out infinite;}
@keyframes heroFloat {
    0%, 100% {transform: translateY(0);}
    50% {transform: translateY(-6px);}
}
.hero-shadow {animation: heroShadow 5s ease-in-out infinite; transform-box: fill-box; transform-origin: center;}
@keyframes heroShadow {
    0%, 100% {transform: scale(1); opacity: 0.2;}
    50% {transform: scale(0.88); opacity: 0.1;}
}
.hero-bar {transform-box: fill-box; transform-origin: left center; animation: heroGrow 7s ease-out infinite;}
@keyframes heroGrow {
    0% {transform: scaleX(0);}
    30%, 92% {transform: scaleX(1);}
    100% {transform: scaleX(0);}
}
.hero-badge {transform-box: fill-box; transform-origin: center; animation: heroBadge 7s ease-out infinite;}
@keyframes heroBadge {
    0%, 42% {transform: scale(0); opacity: 0;}
    52% {transform: scale(1.12); opacity: 1;}
    58%, 92% {transform: scale(1); opacity: 1;}
    100% {transform: scale(1); opacity: 0;}
}
</style>
""",
    unsafe_allow_html=True,
)

RESUME_SVG = f"""<svg viewBox="0 0 260 310" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:230px;display:block;margin:auto;overflow:visible">
<defs><clipPath id="hero-av"><circle cx="60" cy="51" r="19"/></clipPath></defs>

<!-- ground shadow -->
<ellipse class="hero-shadow" cx="114" cy="296" rx="64" ry="7" fill="{INK}"/>

<g class="hero-float">
  <!-- page + offset sheet behind -->
  <rect x="32" y="30" width="180" height="244" rx="10" fill="#D9E3DF"/>
  <rect x="24" y="20" width="180" height="244" rx="10" fill="white" stroke="#D8D2C5" stroke-width="1.5"/>

  <!-- header band -->
  <rect x="24" y="20" width="180" height="64" rx="10" fill="{SAGE}"/>
  <rect x="24" y="66" width="180" height="18" fill="{SAGE}"/>

  <!-- profile silhouette -->
  <circle cx="60" cy="51" r="19" fill="{SAGE_LIGHT}"/>
  <g clip-path="url(#hero-av)">
    <circle cx="60" cy="46" r="7" fill="{SAGE}"/>
    <path d="M43 72 Q43 58 60 58 Q77 58 77 72 Z" fill="{SAGE}"/>
  </g>
  <circle cx="60" cy="51" r="19" fill="none" stroke="white" stroke-width="2"/>

  <!-- name + title -->
  <rect x="90" y="38" width="84" height="9" rx="3" fill="white"/>
  <rect x="90" y="54" width="54" height="6" rx="3" fill="{CLAY}"/>

  <!-- section: experience -->
  <rect x="42" y="102" width="46" height="7" rx="2" fill="{SAGE}"/>
  <rect x="94" y="105" width="94" height="1.5" fill="{LINE}"/>
  <circle cx="45" cy="124" r="2.5" fill="{CLAY}"/>
  <rect class="hero-bar" x="54" y="121" width="126" height="5" rx="2" fill="#D8D2C5" style="animation-delay:0.1s"/>
  <circle cx="45" cy="137" r="2.5" fill="{CLAY}"/>
  <rect class="hero-bar" x="54" y="134" width="108" height="5" rx="2" fill="#D8D2C5" style="animation-delay:0.3s"/>
  <circle cx="45" cy="150" r="2.5" fill="{CLAY}"/>
  <rect class="hero-bar" x="54" y="147" width="118" height="5" rx="2" fill="#D8D2C5" style="animation-delay:0.5s"/>

  <!-- section: education -->
  <rect x="42" y="172" width="46" height="7" rx="2" fill="{SAGE}"/>
  <rect x="94" y="175" width="94" height="1.5" fill="{LINE}"/>
  <rect class="hero-bar" x="42" y="190" width="130" height="5" rx="2" fill="#D8D2C5" style="animation-delay:0.7s"/>
  <rect class="hero-bar" x="42" y="202" width="90" height="5" rx="2" fill="#D8D2C5" style="animation-delay:0.9s"/>

  <!-- skills -->
  <rect class="hero-bar" x="42"  y="222" width="32" height="12" rx="6" fill="{SAGE_LIGHT}" stroke="{SAGE}" stroke-width="1" style="animation-delay:1.1s"/>
  <rect class="hero-bar" x="80"  y="222" width="38" height="12" rx="6" fill="{SAGE_LIGHT}" stroke="{SAGE}" stroke-width="1" style="animation-delay:1.2s"/>
  <rect class="hero-bar" x="124" y="222" width="28" height="12" rx="6" fill="{SAGE_LIGHT}" stroke="{SAGE}" stroke-width="1" style="animation-delay:1.3s"/>

  <!-- success badge -->
  <g class="hero-badge">
    <circle cx="198" cy="248" r="24" fill="{CLAY}" stroke="white" stroke-width="4"/>
    <path d="M187 248 L195 256 L210 239" stroke="white" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  </g>
</g>
</svg>""".replace("\n", "")


# ---------------------------------------------------------------------
# Founder photos
# Put pictures in an "images" folder next to app.py and name them:
#   ben1, ben2, wilbert, connor   (.jpg, .jpeg, .png, or .webp)
# If a photo is missing, the person's initial is shown instead.
# ---------------------------------------------------------------------
IMG_DIR = Path(__file__).parent / "images"
PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def find_photo(stem):
    if not IMG_DIR.is_dir():
        return None
    for path in IMG_DIR.iterdir():
        if path.stem.lower() == stem and path.suffix.lower() in PHOTO_EXTS:
            return path
    return None


@st.cache_data(show_spinner=False)
def photo_data_uri(path_str, modified_time):
    """Crop to a square, shrink, and return the photo as an inline data URI."""
    img = ImageOps.exif_transpose(Image.open(path_str)).convert("RGB")
    img = ImageOps.fit(img, (160, 160))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def avatar_html(letter, color, stem):
    path = find_photo(stem)
    if path:
        uri = photo_data_uri(str(path), path.stat().st_mtime)
        return f'<div class="avatar photo"><img src="{uri}" alt="{letter}"></div>'
    return f'<div class="avatar" style="background:{color}">{letter}</div>'


# ---------------------------------------------------------------------
# Founders data
# ---------------------------------------------------------------------
FOUNDERS = [
    {
        "name": "The Bens",
        "role": "Co-founders (times two)",
        "bio": "Two Bens, one mission. What began as a serendipitous encounter this morning has turned into a lifelong friendship. As experts in the field of entymology, they give special priority to anyone with the name of Ben. ",
        "avatars": [("B", SAGE, "ben1"), ("B", CLAY, "ben2")],
    },
    {
        "name": "Wilbert the Guy",
        "role": "Co-founder",
        "bio": "The main brain. Megamind. Legend. These are just a few of the many accolades he has collected over the years. Behind every great service is an even greater inventor, and his name is Wilbert. All the good we do here at resu.ME wouldn't be possible without him.",
        "avatars": [("W", "#7C9A92", "wilbert")],
    },
    {
        "name": "Connor",
        "role": "Co-founder",
        "bio": "As someone who was once like you, unemployed and desperate and searching for a better solution, he came across the other co-founders of resu.ME at a school hackathon, and instantly realized the life changing opportunity for what it was.",
        "avatars": [("C", "#9A8F7C", "connor")],
    },
]


# ---------------------------------------------------------------------
# Page sections (functions)
# ---------------------------------------------------------------------
def render_top():
    left, right = st.columns([3, 2], vertical_alignment="center")
    with left:
        st.title("Welcome to resu.ME, the place where we help you get hired!", anchor=False)
        st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)
        st.markdown('<p class="hero-sub">Build connections, find events, land the job.</p>', unsafe_allow_html=True)
    with right:
        st.markdown(RESUME_SVG, unsafe_allow_html=True)

    st.write("")
    st.markdown(
        """
<div class="who-card">
<div class="who-grid">
<div>
<h4>Who we are</h4>
<p> No, the real question you're asking is: "What can I become?"<br>With resu.ME we help YOU answer that question to help YOU unlock your fullest potential.

</p>
</div>
<div>
<h4>What we do</h4>
<p>Tell us your major, your interests, and how travel range, and we'll point you to the career fairs, networking events, workshops, and resume-boosting opportunities worth your time.
\n Show up. Stand out. Get hired.</p>

</div>
</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_how_it_works():
    cols = st.columns(3)
    steps = [
        ("1", "Tell us about you", "Your name, major, and location."),
        ("2", "Set your range", "Choose how far you'll travel."),
        ("3", "Find events", "We match events to your major."),
    ]
    for col, (num, head, body) in zip(cols, steps):
        col.markdown(
            f'<div class="step"><span class="num">{num}</span><br><b>{head}</b><p>{body}</p></div>',
            unsafe_allow_html=True,
        )


def section_header(num, title, subtitle, optional=False):
    badge = '<span class="optional">Optional</span>' if optional else ""
    st.markdown(
        f'<div class="sec-head"><span class="sec-num">{num}</span>'
        f'<div><div class="sec-title">{title}{badge}</div>'
        f'<div class="sec-sub">{subtitle}</div></div></div>',
        unsafe_allow_html=True,
    )


def render_profile_form():
    """Draws the profile fields and returns a complete profile, else None."""
    st.header("Tell us about you", anchor=False)

    with st.container(border=True):
        section_header("1", "About you", "The basics, so we can match events to you.")
        name = st.text_input("Name", placeholder="Jordan Smith", key="pf_name")
        c1, c2 = st.columns(2)
        major = c1.text_input("Major", placeholder="Computer Science", key="pf_major")
        location = c2.text_input("Location", placeholder="City, State or ZIP code", key="pf_location")

    st.write("")

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

    if not all(value.strip() for value in (name, major, location)):
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


def render_results(profile):
    events = st.session_state.get("resume_events")
    if events is None:
        return
    st.divider()
    st.header(f"Events for you, {profile['name']}", anchor=False)
    where = (
        "anywhere"
        if profile["radius"] is None
        else f"within {profile['radius']} {profile['radius_unit']} of {profile['location']}"
    )
    st.caption(f"Resume-building recommendations for {profile['major']} majors, {where}.")

    if not events:
        st.info("No events matched. Try a larger radius, more event types, or turn on virtual events.")
    for e in events:
        title = html.escape(str(e.get("title", "Untitled event")))
        event_type = html.escape(str(e.get("type", "Opportunity")))
        event_date = html.escape(str(e.get("date", "Date to be announced")))
        place = html.escape(str(e.get("place", "Location to be announced")))
        description = html.escape(str(e.get("description", "")))
        resume_value = html.escape(str(e.get("resume_value", "")))
        url = html.escape(str(e.get("url", "")), quote=True)
        skills = e.get("skills", [])
        skills_html = " ".join(
            f'<span class="tag">{html.escape(str(skill))}</span>' for skill in skills
        )
        if e.get("virtual"):
            mode_tag = '<span class="tag virtual">Virtual</span>'
        elif e.get("distance_mi") is not None:
            mode_tag = f'<span class="tag">{html.escape(str(e["distance_mi"]))} mi away</span>'
        else:
            mode_tag = '<span class="tag">In person</span>'
        link = f' <a href="{url}" target="_blank">Details</a>' if url else ""
        value_html = f"<br><strong>Resume value:</strong> {resume_value}" if resume_value else ""
        st.markdown(
            f'<div class="event"><h4>{title}</h4>'
            f'<div class="meta">{mode_tag}<span class="tag">{event_type}</span> '
            f'{event_date} · {place}{link}</div>'
            f'{description}{value_html}<div>{skills_html}</div></div>',
            unsafe_allow_html=True,
        )


def render_resume_section(profile=None):
    with st.container(border=True):
        section_header("4", "Your resume", "Upload your resume to find events that can add stronger evidence to it.")

        st.caption("Your resume text is sent to Claude to generate these recommendations.")
        uploaded = st.file_uploader(
            "Upload your resume (PDF or Word)", type=["pdf", "docx"], key="resume_upload"
        )
        if uploaded:
            st.success(f"Got it: {uploaded.name} ({round(uploaded.size / 1024)} KB)")

        can_recommend = profile is not None and uploaded is not None
        if profile is None:
            st.info("Fill in your name, major, and location above before requesting recommendations.")

        checks = [
            "Fits on one page (two at most for experienced applicants)",
            "Contact info and a professional email at the top",
            "Each bullet starts with an action verb and shows a result",
            "Skills and keywords match the roles you want",
            "No typos, and the formatting is consistent",
            "Saved as a PDF with a clean file name",
        ]
        st.markdown("\n".join(f"- {check}" for check in checks))

    if st.button("Find resume-building events", disabled=not can_recommend, key="resume_events_submit"):
        with st.spinner("Reading your resume and finding targeted opportunities..."):
            try:
                resume_text = extract_resume_text(uploaded)
                st.session_state["resume_events"] = recommend_resume_events(profile, resume_text)
                st.rerun()
            except (ValueError, RuntimeError, json.JSONDecodeError) as exc:
                st.error(str(exc))

    events = st.session_state.get("resume_events")
    if events:
        st.success("Recommendations are shown below. Verify dates and availability with each organizer.")
        left, right = st.columns(2)
        payload = json.dumps({"events": events}, indent=2)
        left.download_button(
            "Download JSON",
            data=payload,
            file_name="resume_events.json",
            mime="application/json",
            use_container_width=True,
        )
        right.download_button(
            "Download CSV",
            data=events_to_csv(events),
            file_name="resume_events.csv",
            mime="text/csv",
            use_container_width=True,
        )


def render_founders():
    st.divider()
    st.header("About the 4 Stooges", anchor=False)
    st.write("")

    cols = st.columns(3)
    for col, f in zip(cols, FOUNDERS):
        avatars = "".join(avatar_html(letter, color, stem) for letter, color, stem in f["avatars"])
        col.markdown(
            f'<div class="founder"><div class="avatars">{avatars}</div>'
            f'<div class="founder-name" role="heading" aria-level="4">{f["name"]}</div>'
            f'<div class="role">{f["role"]}</div><p>{f["bio"]}</p></div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------
# The page, top to bottom
# ---------------------------------------------------------------------
render_top()
st.write("")
render_how_it_works()
st.divider()

profile = render_profile_form()
if profile != st.session_state.get("profile"):
    st.session_state["profile"] = profile
    st.session_state.pop("resume_events", None)

render_resume_section(profile)

if profile is not None:
    render_results(profile)
render_founders()

st.markdown('<div class="footer-note">© resu.ME</div>', unsafe_allow_html=True)
