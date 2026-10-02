# resu.ME

A Streamlit app built to help students and early-career job seekers discover future events that can strengthen their resume, expand their network, and make them more competitive in the job market.

The app combines a user profile, resume upload, and AI-powered recommendations to suggest career fairs, workshops, hackathons, networking events, and other resume-building opportunities that fit the user's goals and travel range.

## What it does

- Collects a user's name, major, location, travel radius, and event preferences
- Accepts a PDF or DOCX resume upload for analysis
- Uses Claude to recommend future events based on the user's profile and resume
- Filters opportunities by location, virtual/in-person preference, and travel distance
- Highlights each event's resume value and relevant skills
- Provides calendar downloads, email draft links, and JSON/CSV export options
- Includes an optional newsletter email feature for job-hunting students

## How it works

1. A user fills out their profile and travel preferences.
2. They upload a resume to help the app identify skill gaps and stronger resume-building opportunities.
3. The app asks Claude for tailored opportunities such as career events, networking mixers, research talks, workshops, hackathons, or employer events.
4. Results are shown with date, location, resume value, skills, and direct event links.
5. Users can add the event to their calendar or share it by email.

## Project structure

- `src/the_four_stooges/main.py` — the Streamlit user interface and page layout
- `src/the_four_stooges/backend.py` — resume parsing, event recommendation logic, and formatting helpers
- `src/the_four_stooges/auto_email.py` — SMTP wrapper for sending email newsletters and event emails
- `src/the_four_stooges/images/` — founder photos and avatar assets

## Requirements

- Python 3.14+
- `streamlit`
- `pillow`
- `pypdf`
- `anthropic`
- A valid `ANTHROPIC_API_KEY` for the Claude-powered recommendation engine

## Setup

From the project root:

```bash
cd /home/hansil/the_four_stooges
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
export ANTHROPIC_API_KEY="your-api-key"
```

If you use `uv`, the project is also compatible with:

```bash
cd /home/hansil/the_four_stooges
uv sync
export ANTHROPIC_API_KEY="your-api-key"
```

## Run the app

```bash
cd /home/hansil/the_four_stooges
streamlit run src/the_four_stooges/main.py
```

You can also run it from the package directory:

```bash
cd /home/hansil/the_four_stooges/src/the_four_stooges
streamlit run main.py
```

## Notes

- The recommendation engine uses Claude and may rely on web search or a model-specific API setup depending on your environment.
- The newsletter/email features are optional and may require SMTP credentials to be configured in `src/the_four_stooges/auto_email.py`.
- The app is designed for career-focused students and early-career applicants, but the underlying event recommendation logic can be adapted for other majors and audiences.

## Example use case

A computer science student uploads a resume, enters their city and travel preferences, and receives a shortlist of upcoming technical events that can help them build evidence for leadership, technical communication, networking, and project exposure.
