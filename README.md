# CITS3403-Project
Repo for CITS3403 group project. 

### A description of the purpose of the application, explaining its design and use.
**Application name:**
Podfolio

## Table of Contents

-[Purpose](#purpose)
- [Features](#features)  
- [Prerequisites](#prerequisites)  
- [Getting Started](#getting-started)  
  - [1. Clone & Virtual Environment](#1-clone--virtualenv)  
  - [2. Install dependencies](#2-install-dependencies)  
  - [3. Configure Environment](#3-configuration)  
  - [4. Database Migrations](#4-database-setup)  
  - [5. Run the server](#5-run-the-server)
- [Testing & Usage](#running-tests--manual-qa)
- [Avoid problems because of not installing Jinja Extension](#6-avoid-problems)
- [Directory structure](#directory-structure)   
- [Group Members](#group-members)  

---

## Purpose

Track & Organize Your Listening

Every time you listen to a podcast episode, you can log it in Podfolio—marking what show it was, how long you spent listening, on which platform, and any quick notes you’d like to remember.

Discover Your Tastes at a Glance

Rather than digging through weekly email receipts or scrolling through your podcast app, Podfolio turns your history into easy-to-read charts: “Which genres do I binge most?” “How has my listening time changed week to week?”

Build a Personal Dashboard

Your very own analytics page shows your top five shows, your overall listening trends, and even highlights the single episode you rated highest. It’s like your personal “audio fingerprint,” uniquely yours.

Connect with Fellow Pod-Lovers

See who else is logging the same shows as you. Follow friends (or discover new ones) based on shared tastes, then peek at their profile to get fresh recommendations.

Share Your Passion Safely

Podfolio keeps your data private by default but makes it simple to share a “feed” of your recent listens. Friends can like or comment on your posts—no upvotes, trolls, or misinformation, just genuine chatter about what’s worth a listen. 

## Features

- Secure, Flexible Authentication:

Sign in with email/password or one-click Google OAuth

CSRF-protected forms and hashed passwords

- Podcast Logging:

Log each episode with show title, episode name, listening platform, duration, genre, star rating, and optional text review

Instantly see new entries on your personal profile

- Social Sharing & Messaging:

ShareFeed: post a logged episode to your feed where friends can like and comment

Send to Friend: choose one or more friends to send a podcast directly into your private chat

Built-in chat UI shows sent podcasts inline, displays timestamps, and badges for up to 4+ unread messages

- Friends & Privacy Controls:

Search for users by username, send and accept friend requests

Private profiles by default—only approved friends can view each other’s logs and analytics

- Interactive Analytics Dashboard:

Genre Breakdown: horizontal bar chart of total listening minutes by genre

Listening Trends: time-series plot of weekly minutes listened

Top 5 Shows: list of your most-played podcasts this month

Most Loved: highlight the single episode you rated highest

- Profile & Settings:

Click your name in the sidebar to view your profile and all logged episodes

Settings Page: update display name, email, password, profile picture, or permanently delete your account

- Global Search & Navigation:

Sidebar links let you jump to Logger, Dashboard, ShareFeed, Chats, Friends, Settings, and Logout

Responsive layout adapts seamlessly from mobile to desktop

- One-click Logout:

Securely sign out from any page with a single click


## Prerequisites
- Python 3.11+
- SQLite (bundled)
- Spotify API credentials (for fetching podcast details)
- Gmail account (for password reset emails)

## Getting Started

1. **Clone & Virtual Environment**  
   ```bash
   git clone https://github.com/EmilyHan22/CITS3403-Project.git
   cd CITS3403-Project
   python3 -m venv venv
   source venv/bin/activate
   ```
2. **Install Dependencies**  
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Configure Environment**  
   Copy the example `.env` file or create a new one in the project root:

   ```ini
   #SECRET_KEY=dev
   #FLASK_ENV=development
   #SQLALCHEMY_DATABASE_URI=sqlite:////full/path/to/app/podfolio.db

   #GOOGLE_CLIENT_ID=200793653741-f64k1lagqq8n5acbt993u0ni48t81g3s.apps.googleusercontent.com
   #GOOGLE_CLIENT_SECRET=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
   #OAUTHLIB_INSECURE_TRANSPORT=1

   #SPOTIFY_CLIENT_ID=41f896f36304442fbb01a77a11c0aebb
   #SPOTIFY_CLIENT_SECRET=99c407e2cbe048e684b172c76c92896a


   #MAIL_SERVER=smtp.gmail.com
   #MAIL_PORT=587
   #MAIL_USE_TLS=True
   #MAIL_USERNAME=podfolio.noreply@gmail.com
   #MAIL_PASSWORD=yoipgtxgjfmtrjlu
   #MAIL_DEFAULT_SENDER=Podfolio Support <podfolio.noreply@gmail.com> -->
   ```

4. **Database Migrations**  
   ```bash
   flask db upgrade
   ```
   If starting fresh:
   ```bash
   rm app/podfolio.db
   flask db stamp head
   flask db upgrade
   ```

5. **Run the Server**  
   ```bash
   flask run
   ```
   Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

## Testing & Usage
python -m unittest discover -s tests for all the tests at once
python -m unittest tests.test_models only unit tests
python -m unittest tests.test_selenium for selenium tests only

  **Running the test files:**
- all the tests at once: python -m unittest discover -s tests
- only unit tests: python -m unittest tests.test_models 
- only selenium tests: python -m unittest tests.test_selenium 

## Avoid problems because of not installing Jinja Extension
- Open your user settings JSON
- Do this by typing Ctrl+Shift+P on Windows and ⌘ + Shift + P on Mac
- Type Preferences: Open settings(JSON) and hit enter
- In that file (your User settings.json) add exactly:
```
"files.associations": {
  "**/templates/**/*.html": "jinja"
},
"[jinja]": {
  "css.validate": false
}
```

# Directory Structure

CITS3403-Project/
│
├── app/
│ ├── init.py
│ ├── auth.py
│ ├── database.py
│ ├── db.py
│ ├── load_data.py
│ ├── models.py
│ ├── routes.py
│ ├── podcast_log_dummy_data.csv
│ ├── podcast_table_dummy_data.csv
│ ├── static/
│ │ └── … (CSS, JS, icons, uploads, etc.)
│ └── templates/
│ └── … (Jinja2 HTML templates)
│
├── migrations/ # Flask-Migrate migrations
│ └── …
│
├── tests/
│ └── … (unit & Selenium tests)
│
├── load.py # data‐loading script (standalone)
├── run.py # app entry‐point
├── requirements.txt
├── README.md
└── .gitignore

### Group 63 Members:

| Name            | UWA ID   | Github username |
| --------------- |:--------:| ---------------:|
| Emily Han       | 23925907 | EmilyHan22      |
| Isabelle O'Hara | 23178076 | Unknown-Asterix |
| Khant Soe Kyaw  | 23673385 | 505cs           |
| Aagney Singh    | 23739771 | aagney2         |


