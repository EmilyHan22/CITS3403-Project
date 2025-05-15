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
  - [1. Clone & virtualenv](#1-clone--virtualenv)  
  - [2. Install dependencies](#2-install-dependencies)  
  - [3. Configuration](#3-configuration)  
  - [4. Database setup](#4-database-setup)  
  - [5. Run the server](#5-run-the-server)  
- [Running Tests / Manual QA](#running-tests--manual-qa)  
- [Group Members](#group-members)  

---

## Purpose
This application is designed for users to visualize the podcasts they listen to in an organized manner, their top listened to genres and series, learn more about their own preferences, and able to share their visualized dashboard with friends. meet people in the community that share the same tastes, or get introduced to new flavours all together. It's a safe and fun space for podcast lovers to learn more about themselves, about others, and share their passion. 

## Features

- **User accounts** (email/password & Google OAuth)  
- **Podcast logging** with notes, platform, duration, rating  
- **Analytics dashboard** (genre pie-chart, time series, top shows)  
- **Friend system**: follow, private profiles, share feeds  
- **Share feed**: scrolling “reels” of friends’ logged episodes, with likes & comments


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
   SECRET_KEY=your-secret-key
   FLASK_ENV=development
   SQLALCHEMY_DATABASE_URI=sqlite:////full/path/to/app/podfolio.db

   # Google OAuth
   GOOGLE_CLIENT_ID=...
   GOOGLE_CLIENT_SECRET=...
   OAUTHLIB_INSECURE_TRANSPORT=1

   # Spotify API
   SPOTIFY_CLIENT_ID=...
   SPOTIFY_CLIENT_SECRET=...

   # Mail (Gmail SMTP for password resets)
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=podfolio.noreply@gmail.com
   MAIL_PASSWORD=your-app-password
   MAIL_DEFAULT_SENDER="Podfolio Support <podfolio.noreply@gmail.com>"
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
- Create dummy accounts to test sign up, login, password reset.
- Log podcasts on the logger page; verify dashboard charts.
- Send/accept friend requests; confirm privacy on profiles.
- Post to the share feed; like and comment in real time.

### Group 63 Members:

| Name            | UWA ID   | Github username |
| --------------- |:--------:| ---------------:|
| Emily Han       | 23925907 | EmilyHan22      |
| Isabelle O'Hara | 23178076 | Unknown-Asterix |
| Khant Soe Kyaw  | 23673385 | 505cs           |
| Aagney Singh    | 23739771 | aagney2         |


