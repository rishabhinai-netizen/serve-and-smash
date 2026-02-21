# 🏸 Serve & Smash — Badminton Tournament Manager

A full-featured badminton tournament management system built with **Streamlit + Supabase**.

## 🎯 Features

| Feature | Details |
|---|---|
| **Participants** | 14 Players, 2 Referees, 1 Admin |
| **Courts** | Court 2 & Court 3 (concurrent matches) |
| **Group Stage** | 21 matches (round-robin, all 7 teams vs each other) |
| **Team Assignment** | Animated spin wheel → 7 teams of 2 |
| **Live Scoring** | Referee +1 per point, first to 15 wins |
| **Leaderboard** | Live with full tiebreaker logic |
| **Knockout** | SF → Final + 3rd Place |
| **Roles** | Admin / Referee / Player dashboards |

## 📁 Project Structure

```
serve-and-smash/
├── app.py                  # Main entry point & router
├── requirements.txt
├── .gitignore
├── .streamlit/
│   ├── config.toml         # Theme config
│   └── secrets.toml        # ← You create this (see below)
├── pages/
│   ├── signup.py           # Registration page
│   ├── login.py            # Login page
│   ├── admin.py            # Admin dashboard
│   ├── referee.py          # Referee scoring panel
│   └── player.py           # Player view
└── utils/
    ├── db.py               # All Supabase interactions
    └── schedule.py         # Match schedule generation logic
```

## 🚀 Setup Instructions

### Step 1 — Create GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Name it `serve-and-smash`
3. Set to **Private** (recommended)
4. **Don't** initialize with README (we already have files)
5. Click **Create repository**
6. Follow GitHub's instructions to push these files:

```bash
cd serve-and-smash
git init
git add .
git commit -m "Initial commit: Serve & Smash tournament app"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/serve-and-smash.git
git push -u origin main
```

### Step 2 — Get Supabase Service Role Key

1. Go to your Supabase project: [supabase.com/dashboard](https://supabase.com/dashboard)
2. Project: **serve-and-smash**
3. Go to **Settings → API**
4. Copy the **service_role** key (NOT the anon key)

### Step 3 — Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **New app**
3. Connect your GitHub repo `serve-and-smash`
4. Set **Main file path** to `app.py`
5. Click **Advanced settings → Secrets** and paste:

```toml
SUPABASE_URL = "https://pqhipbnjkbhlguvrjcah.supabase.co"
SUPABASE_KEY = "your_service_role_key_here"
```

6. Click **Deploy!**

### Step 4 — Local Development (Optional)

```bash
pip install -r requirements.txt

# Create your secrets file
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml with your actual service_role key

streamlit run app.py
```

---

## 🏆 Tournament Flow

```
1. SIGNUP PHASE
   ├── 14 players register
   ├── 2 referees register  
   └── 1 admin registers → signups auto-freeze

2. TEAM ASSIGNMENT (Admin)
   ├── Spin the wheel (animated)
   └── 14 players → 7 teams (Team A–G)

3. COURT SETUP (Admin)
   └── Assign Referee 1 → Court 2, Referee 2 → Court 3

4. SCHEDULE GENERATION (Admin)
   └── 21 group stage matches generated
       • No team plays 3+ matches back-to-back
       • Equal rest distribution

5. GROUP STAGE (Referees score)
   ├── First to 15 points wins
   ├── Live leaderboard updates
   └── Each team plays 6 matches

6. LEADERBOARD FREEZE → Top 4 qualify
   Tiebreaker rules:
   a) More wins → higher seed
   b) Tie on wins → higher score difference
   c) Same diff → head-to-head result
   d) 3-way tie → see full tiebreaker logic in db.py

7. SEMIFINALS
   ├── Match 22: 1st vs 4th (Court 2)
   └── Match 23: 2nd vs 3rd (Court 3)

8. FINALS
   ├── Match 24: SF loser 1 vs SF loser 2 → 3rd place
   └── Match 25: SF winner 1 vs SF winner 2 → CHAMPION 🏆
```

---

## 📊 Leaderboard Columns

| Column | Meaning |
|---|---|
| MP | Matches Played |
| W | Wins |
| L | Losses |
| SF | Score For (total points scored by team) |
| SA | Score Against (total points scored by opponents) |
| DIFF | Score For − Score Against |

---

## ⚙️ Supabase Project Details

- **Project:** serve-and-smash  
- **URL:** `https://pqhipbnjkbhlguvrjcah.supabase.co`  
- **Region:** ap-south-1 (Mumbai)

---

## 🔐 Security Notes

- Passwords are SHA-256 hashed before storage
- Service role key goes in Streamlit Secrets only (never in code)
- `.gitignore` excludes `secrets.toml`
- RLS is disabled (app uses service role — suitable for internal tournament use)
