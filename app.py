import sys
import os
import hashlib
import random
import time
import json
from itertools import combinations

import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Serve & Smash Tournament",
    page_icon="🏸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CSS — Light Professional Theme ──────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=DM+Sans:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Override Streamlit background */
.stApp {
    background-color: #f5f7fa;
}

section[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e2e8f0;
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem;
}

/* Hide default Streamlit header */
header[data-testid="stHeader"] {
    background: transparent;
}

/* Main container */
.block-container {
    padding-top: 1rem;
    max-width: 1100px;
}

/* Hero */
.hero {
    background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 50%, #1d4ed8 100%);
    border-radius: 16px;
    padding: 36px 40px;
    margin-bottom: 28px;
    color: white;
    display: flex;
    align-items: center;
    gap: 20px;
}
.hero-icon { font-size: 52px; line-height: 1; }
.hero-title {
    font-family: 'Inter', sans-serif;
    font-size: 32px;
    font-weight: 800;
    letter-spacing: -0.5px;
    margin: 0;
    color: white;
}
.hero-sub {
    font-size: 14px;
    color: rgba(255,255,255,0.75);
    margin-top: 4px;
    letter-spacing: 0.5px;
}

/* Phase badge */
.phase-badge {
    display: inline-block;
    background: rgba(255,255,255,0.2);
    color: white;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding: 4px 12px;
    border-radius: 20px;
    margin-top: 10px;
    border: 1px solid rgba(255,255,255,0.3);
}

/* Cards */
.ss-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

/* Section title */
.section-title {
    font-family: 'Inter', sans-serif;
    font-size: 18px;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 16px;
    padding-bottom: 10px;
    border-bottom: 2px solid #e2e8f0;
}

/* Status pills */
.stat-row { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 16px; }
.stat-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    border: 1px solid;
}
.pill-blue { background: #eff6ff; color: #1d4ed8; border-color: #bfdbfe; }
.pill-amber { background: #fffbeb; color: #b45309; border-color: #fde68a; }
.pill-red { background: #fef2f2; color: #dc2626; border-color: #fecaca; }
.pill-green { background: #f0fdf4; color: #15803d; border-color: #bbf7d0; }

/* Match rows */
.match-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    transition: box-shadow 0.15s;
}
.match-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
.match-card.live {
    border-left: 4px solid #ef4444;
    background: #fff5f5;
}
.match-card.done {
    border-left: 4px solid #22c55e;
    background: #f0fdf4;
    opacity: 0.85;
}
.match-card.pending {
    border-left: 4px solid #94a3b8;
}

.match-num {
    font-size: 11px;
    font-weight: 600;
    color: #94a3b8;
    letter-spacing: 1px;
    text-transform: uppercase;
    min-width: 50px;
}
.match-teams {
    font-size: 15px;
    font-weight: 700;
    color: #1e293b;
    flex: 1;
    margin: 0 16px;
}
.match-vs { color: #94a3b8; font-weight: 500; margin: 0 8px; font-size: 13px; }
.match-score {
    font-family: 'Inter', sans-serif;
    font-size: 16px;
    font-weight: 800;
    color: #1e293b;
    min-width: 60px;
    text-align: center;
}
.match-court {
    font-size: 11px;
    font-weight: 600;
    color: #2563eb;
    background: #eff6ff;
    padding: 3px 10px;
    border-radius: 20px;
    margin-left: 10px;
}
.match-status-live {
    font-size: 11px; font-weight: 700; color: #ef4444;
    background: #fee2e2; padding: 3px 10px; border-radius: 20px; margin-left: 6px;
    animation: blink 1.5s infinite;
}
.match-status-done {
    font-size: 11px; font-weight: 600; color: #15803d;
    background: #dcfce7; padding: 3px 10px; border-radius: 20px; margin-left: 6px;
}
.match-status-pending {
    font-size: 11px; font-weight: 600; color: #64748b;
    background: #f1f5f9; padding: 3px 10px; border-radius: 20px; margin-left: 6px;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.5} }

/* Team cards */
.team-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 12px;
    border-top: 3px solid var(--tc);
}
.team-name {
    font-family: 'Inter', sans-serif;
    font-size: 16px;
    font-weight: 800;
    color: #1e293b;
    margin-bottom: 8px;
}
.team-player {
    font-size: 13px;
    color: #475569;
    padding: 3px 0;
}

/* Leaderboard */
.lb-header-row {
    display: grid;
    grid-template-columns: 44px 1fr 56px 44px 44px 70px 70px 70px;
    gap: 6px;
    padding: 8px 14px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px 8px 0 0;
    font-size: 10px;
    font-weight: 700;
    color: #64748b;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 2px;
}
.lb-row {
    display: grid;
    grid-template-columns: 44px 1fr 56px 44px 44px 70px 70px 70px;
    gap: 6px;
    padding: 12px 14px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    margin-bottom: 3px;
    font-size: 14px;
    align-items: center;
    transition: box-shadow 0.1s;
}
.lb-row:hover { box-shadow: 0 2px 6px rgba(0,0,0,0.06); }
.lb-row.qualified { border-left: 3px solid #f59e0b; background: #fffbeb; }
.lb-row.my-team { background: #eff6ff; border: 1px solid #bfdbfe; }

/* Score display for referee */
.score-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 24px;
    text-align: center;
}
.score-team-name {
    font-size: 15px;
    font-weight: 700;
    color: #475569;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.score-number {
    font-family: 'Inter', sans-serif;
    font-size: 80px;
    font-weight: 800;
    line-height: 1;
}
.score-red { color: #dc2626; }
.score-blue { color: #2563eb; }

/* Sidebar items */
.sidebar-stat {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid #f1f5f9;
    font-size: 13px;
}
.sidebar-stat-label { color: #64748b; font-weight: 500; }
.sidebar-stat-val { font-weight: 700; color: #1e293b; }

/* User chips */
.user-chip {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 6px;
}
.user-chip-name { font-size: 14px; font-weight: 600; color: #1e293b; }
.user-chip-mobile { font-size: 12px; color: #64748b; margin-top: 2px; }

/* Slot label */
.slot-label {
    font-size: 11px;
    font-weight: 700;
    color: #94a3b8;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin: 14px 0 6px;
}

/* Champion banner */
.champion-banner {
    background: linear-gradient(135deg, #1e3a5f, #2563eb);
    border-radius: 16px;
    padding: 40px;
    text-align: center;
    color: white;
    margin-top: 20px;
}
.champion-label {
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: #fbbf24;
    margin-bottom: 8px;
}
.champion-name {
    font-family: 'Inter', sans-serif;
    font-size: 52px;
    font-weight: 800;
    color: white;
    letter-spacing: -1px;
}
</style>
""", unsafe_allow_html=True)

# ─── Supabase ─────────────────────────────────────────────────────────────────
@st.cache_resource
def get_client() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# ─── DB Functions ────────────────────────────────────────────────────────────
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def signup_user(name, mobile, password, role):
    try:
        r = get_client().table("users").insert({
            "name": name, "mobile": mobile,
            "password_hash": hash_pw(password), "role": role
        }).execute()
        return r.data[0], None
    except Exception as e:
        return None, str(e)

def login_user(mobile, password):
    r = get_client().table("users").select("*").eq("mobile", mobile).execute()
    if not r.data:
        return None, "Mobile number not registered."
    u = r.data[0]
    if hash_pw(password) != u["password_hash"]:
        return None, "Incorrect password."
    return u, None

def count_by_role():
    r = get_client().table("users").select("role").execute()
    c = {"player": 0, "referee": 0, "admin": 0}
    for row in r.data:
        c[row["role"]] += 1
    return c

def get_all_users():
    return get_client().table("users").select("*").order("created_at").execute().data

def get_state():
    return get_client().table("tournament_state").select("*").eq("id", 1).execute().data[0]

def update_state(**kw):
    get_client().table("tournament_state").update(kw).eq("id", 1).execute()

def get_teams():
    return get_client().table("teams").select(
        "*, p1:users!teams_player1_id_fkey(id,name), p2:users!teams_player2_id_fkey(id,name)"
    ).order("name").execute().data

def get_teams_simple():
    return get_client().table("teams").select("id,name").order("name").execute().data

def create_teams(assignments):
    get_client().table("teams").insert(assignments).execute()

def get_courts():
    return get_client().table("courts").select("*, ref:users(id,name)").execute().data

def assign_court(court_id, referee_id):
    get_client().table("courts").update({"referee_id": referee_id}).eq("id", court_id).execute()

def get_matches(stage=None):
    q = get_client().table("matches").select(
        "*, team1:teams!matches_team1_id_fkey(id,name),"
        "team2:teams!matches_team2_id_fkey(id,name),"
        "court:courts(name),winner:teams!matches_winner_id_fkey(id,name)"
    ).order("match_order")
    if stage:
        q = q.eq("stage", stage)
    return q.execute().data

def create_matches(matches):
    get_client().table("matches").insert(matches).execute()

def start_match(mid):
    get_client().table("matches").update({"status": "live"}).eq("id", mid).execute()

def add_score(mid, field, cur, t1id, t2id):
    ns = cur + 1
    get_client().table("matches").update({field: ns}).eq("id", mid).execute()
    if ns >= 15:
        wid = t1id if field == "score_team1" else t2id
        get_client().table("matches").update({
            "winner_id": wid, "status": "completed"
        }).eq("id", mid).execute()
        return True, wid
    return False, None

def get_live_matches():
    return get_client().table("matches").select(
        "*, team1:teams!matches_team1_id_fkey(id,name),"
        "team2:teams!matches_team2_id_fkey(id,name),court:courts(name)"
    ).eq("status", "live").execute().data

def get_referee_match(ref_id):
    cr = get_client().table("courts").select("id,name").eq("referee_id", ref_id).execute()
    if not cr.data:
        return None, None
    court = cr.data[0]
    mr = get_client().table("matches").select(
        "*, team1:teams!matches_team1_id_fkey(id,name),"
        "team2:teams!matches_team2_id_fkey(id,name),court:courts(name)"
    ).eq("court_id", court["id"]).in_("status", ["pending", "live"]).order("match_order").limit(1).execute()
    return (mr.data[0] if mr.data else None), court

def get_leaderboard():
    rows = get_client().table("leaderboard").select("*").execute().data
    for r in rows:
        r["score_diff"] = r["score_for"] - r["score_against"]
    return rows

def check_group_done():
    r = get_client().table("matches").select("id").eq("stage", "group").neq("status", "completed").execute()
    return len(r.data) == 0

def get_top4():
    rows = get_leaderboard()
    rows.sort(key=lambda x: (x["won"], x["score_diff"], x["score_for"]), reverse=True)
    return rows[:4], rows[4:]

def create_semis(top4):
    courts = get_courts()
    c2 = next(c for c in courts if c["name"] == "Court 2")
    c3 = next(c for c in courts if c["name"] == "Court 3")
    mn = get_client().table("matches").select("match_number").order("match_number", desc=True).limit(1).execute()
    mo = get_client().table("matches").select("match_order").order("match_order", desc=True).limit(1).execute()
    base_n = mn.data[0]["match_number"] if mn.data else 21
    base_o = mo.data[0]["match_order"] if mo.data else 21
    get_client().table("matches").insert([
        {"match_number": base_n+1, "stage": "semifinal",
         "team1_id": top4[0]["id"], "team2_id": top4[3]["id"],
         "court_id": c2["id"], "referee_id": c2.get("referee_id"),
         "status": "pending", "match_order": base_o+1},
        {"match_number": base_n+2, "stage": "semifinal",
         "team1_id": top4[1]["id"], "team2_id": top4[2]["id"],
         "court_id": c3["id"], "referee_id": c3.get("referee_id"),
         "status": "pending", "match_order": base_o+2},
    ]).execute()

def create_finals(sf_matches):
    courts = get_courts()
    c2 = next(c for c in courts if c["name"] == "Court 2")
    c3 = next(c for c in courts if c["name"] == "Court 3")
    mn = get_client().table("matches").select("match_number").order("match_number", desc=True).limit(1).execute()
    mo = get_client().table("matches").select("match_order").order("match_order", desc=True).limit(1).execute()
    base_n = mn.data[0]["match_number"]
    base_o = mo.data[0]["match_order"]
    sf = sorted(sf_matches, key=lambda x: x["match_number"])

    def loser(m):
        t1 = (m.get("team1") or {}).get("id")
        t2 = (m.get("team2") or {}).get("id")
        w = m.get("winner_id") or ((m.get("winner") or {}).get("id"))
        return t1 if w == t2 else t2

    def winner(m):
        return m.get("winner_id") or ((m.get("winner") or {}).get("id"))

    get_client().table("matches").insert([
        {"match_number": base_n+1, "stage": "third_place",
         "team1_id": loser(sf[0]), "team2_id": loser(sf[1]),
         "court_id": c2["id"], "referee_id": c2.get("referee_id"),
         "status": "pending", "match_order": base_o+1},
        {"match_number": base_n+2, "stage": "final",
         "team1_id": winner(sf[0]), "team2_id": winner(sf[1]),
         "court_id": c3["id"], "referee_id": c3.get("referee_id"),
         "status": "pending", "match_order": base_o+2},
    ]).execute()

# ─── Schedule Builder ─────────────────────────────────────────────────────────
TEAM_LABELS = ["Team A","Team B","Team C","Team D","Team E","Team F","Team G"]
TEAM_COLORS = ["#2563eb","#dc2626","#16a34a","#9333ea","#ea580c","#0891b2","#be185d"]

def build_schedule(team_names, court_names):
    all_pairs = list(combinations(team_names, 2))
    random.shuffle(all_pairs)
    consecutive = {t: 0 for t in team_names}
    last_played = {t: -1 for t in team_names}
    schedule = []
    remaining = list(all_pairs)
    slot = 0
    while remaining and slot < 300:
        busy = set()
        slot_matches = []
        for court in court_names:
            if not remaining:
                break
            best, best_score = None, -1
            for pair in remaining:
                t1, t2 = pair
                if t1 in busy or t2 in busy:
                    continue
                c1 = consecutive[t1] if last_played[t1] == slot - 1 else 0
                c2 = consecutive[t2] if last_played[t2] == slot - 1 else 0
                if c1 >= 2 or c2 >= 2:
                    continue
                score = (slot - last_played[t1]) + (slot - last_played[t2])
                if score > best_score:
                    best_score = score
                    best = pair
            if best:
                remaining.remove(best)
                slot_matches.append({"team1": best[0], "team2": best[1],
                                     "court_name": court,
                                     "match_order": len(schedule) + len(slot_matches) + 1})
                busy.add(best[0])
                busy.add(best[1])
        playing = set()
        for sm in slot_matches:
            playing.add(sm["team1"])
            playing.add(sm["team2"])
        for t in team_names:
            if t in playing:
                consecutive[t] = (consecutive[t] + 1) if last_played[t] == slot - 1 else 1
                last_played[t] = slot
        schedule.extend(slot_matches)
        slot += 1
    for pair in remaining:
        schedule.append({"team1": pair[0], "team2": pair[1],
                         "court_name": court_names[len(schedule) % len(court_names)],
                         "match_order": len(schedule) + 1})
    return schedule

# ─── UI Helpers ───────────────────────────────────────────────────────────────
def render_match(m):
    t1 = m.get("team1") or {}
    t2 = m.get("team2") or {}
    court = m.get("court") or {}
    winner = m.get("winner") or {}
    status = m.get("status", "pending")
    s1 = m.get("score_team1", 0)
    s2 = m.get("score_team2", 0)
    stage_map = {"group": "GROUP", "semifinal": "SEMI", "third_place": "3RD PLACE", "final": "FINAL"}
    stage_label = stage_map.get(m.get("stage", ""), "")
    css_class = status  # "live", "done", "pending"
    score_str = f"{s1} — {s2}" if status != "pending" else "vs"
    win_str = ""
    if winner.get("name") and status == "completed":
        win_str = f" &nbsp; 🏆 <span style='color:#15803d'>{winner['name']}</span>"
    status_badge = {
        "live": "<span class='match-status-live'>● LIVE</span>",
        "completed": "<span class='match-status-done'>✓ DONE</span>",
        "pending": "<span class='match-status-pending'>Upcoming</span>"
    }[status]
    st.markdown(f"""
    <div class='match-card {css_class}'>
        <span class='match-num'>#{m['match_number']} {stage_label}</span>
        <span class='match-teams'>
            {t1.get('name','?')} <span class='match-vs'>vs</span> {t2.get('name','?')}{win_str}
        </span>
        <span class='match-score'>{score_str}</span>
        <span class='match-court'>{court.get('name','?')}</span>
        {status_badge}
    </div>
    """, unsafe_allow_html=True)

def render_leaderboard(rows, my_team_name=None):
    rows = sorted(rows, key=lambda x: (x["won"], x["score_diff"], x["score_for"]), reverse=True)
    pos_icons = {1: "🥇", 2: "🥈", 3: "🥉", 4: "4th"}
    st.markdown("""
    <div class='lb-header-row'>
        <div>Pos</div><div>Team</div><div>Played</div>
        <div>W</div><div>L</div><div>For</div><div>Against</div><div>Diff</div>
    </div>
    """, unsafe_allow_html=True)
    for i, row in enumerate(rows):
        pos = i + 1
        diff = row["score_diff"]
        diff_str = ("+" if diff > 0 else "") + str(diff)
        diff_color = "#15803d" if diff > 0 else "#dc2626" if diff < 0 else "#64748b"
        is_mine = my_team_name and row["team_name"] == my_team_name
        extra_class = "my-team" if is_mine else ("qualified" if pos <= 4 else "")
        mine_star = " ⭐" if is_mine else ""
        st.markdown(f"""
        <div class='lb-row {extra_class}'>
            <div style='font-weight:700;color:#1e293b'>{pos_icons.get(pos, str(pos))}</div>
            <div style='font-weight:600;color:#1e293b'>{row['team_name']}{mine_star}</div>
            <div style='color:#64748b'>{row['matches_played']}</div>
            <div style='color:#15803d;font-weight:700'>{row['won']}</div>
            <div style='color:#dc2626'>{row['lost']}</div>
            <div style='color:#2563eb'>{row['score_for']}</div>
            <div style='color:#7c3aed'>{row['score_against']}</div>
            <div style='color:{diff_color};font-weight:700'>{diff_str}</div>
        </div>
        """, unsafe_allow_html=True)
    st.caption("🏅 Top 4 advance to Semifinals | ⭐ = Your team")

def spin_wheel_html(player_names):
    colors = [
        "#2563eb","#dc2626","#16a34a","#9333ea","#ea580c",
        "#0891b2","#be185d","#b45309","#0f766e","#4338ca",
        "#c2410c","#1d4ed8","#15803d","#7e22ce"
    ]
    nj = json.dumps(player_names)
    cj = json.dumps(colors[:len(player_names)])
    return f"""<!DOCTYPE html><html><head>
<style>
  body{{background:#f5f7fa;display:flex;flex-direction:column;align-items:center;
        justify-content:center;height:560px;margin:0;
        font-family:'DM Sans',system-ui,sans-serif;}}
  canvas{{border-radius:50%;box-shadow:0 8px 32px rgba(37,99,235,0.25);}}
  #spinBtn{{margin-top:18px;background:linear-gradient(135deg,#1d4ed8,#2563eb);
    color:white;border:none;padding:13px 44px;font-size:16px;font-weight:700;
    letter-spacing:1px;cursor:pointer;border-radius:8px;transition:all 0.2s;
    box-shadow:0 4px 12px rgba(37,99,235,0.35);}}
  #spinBtn:hover{{background:linear-gradient(135deg,#1e40af,#1d4ed8);transform:translateY(-1px);}}
  #spinBtn:disabled{{background:#cbd5e1;cursor:not-allowed;transform:none;box-shadow:none;}}
  #result{{margin-top:12px;font-size:16px;font-weight:700;color:#1d4ed8;
           letter-spacing:0.5px;min-height:26px;text-align:center;}}
  .wrap{{position:relative;}}
  .ptr{{position:absolute;top:50%;right:-20px;transform:translateY(-50%);
    width:0;height:0;border-top:14px solid transparent;
    border-bottom:14px solid transparent;border-left:24px solid #f59e0b;}}
</style></head><body>
<div class="wrap">
  <canvas id="wh" width="300" height="300"></canvas>
  <div class="ptr"></div>
</div>
<button id="spinBtn" onclick="spin()">🎡 Spin the Wheel</button>
<div id="result"></div>
<script>
const names={nj},colors={cj};
const cv=document.getElementById('wh'),ctx=cv.getContext('2d');
let cur=0,spinning=false,rem=[...names];
function draw(a){{
  const cx=150,cy=150,r=144,disp=rem.length>0?rem:names,arc=2*Math.PI/disp.length;
  ctx.clearRect(0,0,300,300);
  for(let i=0;i<disp.length;i++){{
    const s=a+i*arc;
    ctx.beginPath();ctx.moveTo(cx,cy);ctx.arc(cx,cy,r,s,s+arc);ctx.closePath();
    ctx.fillStyle=colors[i%colors.length];ctx.fill();
    ctx.strokeStyle='rgba(255,255,255,0.6)';ctx.lineWidth=2;ctx.stroke();
    ctx.save();ctx.translate(cx,cy);ctx.rotate(s+arc/2);ctx.textAlign='right';
    ctx.fillStyle='#fff';ctx.font='bold '+Math.min(12,180/disp.length+6)+'px DM Sans,system-ui';
    ctx.shadowColor='rgba(0,0,0,0.4)';ctx.shadowBlur=3;
    const n=disp[i];ctx.fillText(n.length>13?n.substring(0,12)+'…':n,r-8,4);ctx.restore();
  }}
  ctx.beginPath();ctx.arc(cx,cy,20,0,2*Math.PI);
  ctx.fillStyle='#fff';ctx.fill();
  ctx.strokeStyle='#e2e8f0';ctx.lineWidth=2;ctx.stroke();
  ctx.fillStyle='#2563eb';ctx.font='bold 14px DM Sans';
  ctx.textAlign='center';ctx.fillText('🏸',cx,cy+5);
}}
function spin(){{
  if(spinning||rem.length===0)return;
  spinning=true;document.getElementById('spinBtn').disabled=true;
  document.getElementById('result').textContent='Spinning...';
  const extra=(5+Math.random()*5)*2*Math.PI,stop=Math.random()*2*Math.PI;
  const total=extra+stop,dur=4000,t0=performance.now(),a0=cur;
  function anim(now){{
    const el=now-t0,t=Math.min(el/dur,1),e=1-Math.pow(1-t,4);
    cur=a0+total*e;draw(cur);
    if(t<1){{requestAnimationFrame(anim);return;}}
    spinning=false;
    const arc=2*Math.PI/rem.length;
    const norm=(((-cur)%(2*Math.PI))+2*Math.PI)%(2*Math.PI);
    const idx=Math.floor(norm/arc)%rem.length;
    const w=rem[idx];
    document.getElementById('result').textContent='Selected: '+w;
    rem=rem.filter(n=>n!==w);
    setTimeout(()=>{{
      if(rem.length>0){{
        document.getElementById('spinBtn').disabled=false;
        document.getElementById('spinBtn').textContent='Spin Again ('+rem.length+' left)';
      }}else{{
        document.getElementById('spinBtn').textContent='All players spun!';
        document.getElementById('result').textContent='Done! Click Auto-Assign Teams below.';
      }}
      draw(cur);
    }},1500);
  }}
  requestAnimationFrame(anim);
}}
draw(0);
</script></body></html>"""

def show_teams_grid(teams):
    cols = st.columns(4)
    for i, t in enumerate(teams):
        p1 = t.get("p1") or {}
        p2 = t.get("p2") or {}
        color = TEAM_COLORS[i % len(TEAM_COLORS)]
        p1n = p1.get("name", "?")
        p2n = p2.get("name", "?")
        tn = t["name"]
        with cols[i % 4]:
            st.markdown(f"""
            <div style='background:#fff;border:1px solid #e2e8f0;border-radius:10px;
                        border-top:3px solid {color};padding:14px;margin-bottom:12px;'>
                <div style='font-family:Inter,sans-serif;font-size:15px;font-weight:800;
                            color:#1e293b;margin-bottom:8px;'>{tn}</div>
                <div style='font-size:13px;color:#475569;padding:2px 0'>🏸 {p1n}</div>
                <div style='font-size:13px;color:#475569;padding:2px 0'>🏸 {p2n}</div>
            </div>
            """, unsafe_allow_html=True)

# ─── PAGES ────────────────────────────────────────────────────────────────────
LIMITS = {"player": 14, "referee": 2, "admin": 1}

def page_signup():
    state = get_state()
    if state["signups_frozen"]:
        st.error("🔒 Signups are closed — all slots are filled. Please log in.")
        return
    counts = count_by_role()
    available = [r for r in ("admin", "referee", "player") if counts[r] < LIMITS[r]]
    if not available:
        update_state(signups_frozen=True)
        st.error("🔒 All slots filled!")
        return

    st.markdown("<div class='section-title'>📝 Create Your Account</div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Players Registered", f"{counts['player']} / 14")
    c2.metric("Referees Registered", f"{counts['referee']} / 2")
    c3.metric("Admin Registered", f"{counts['admin']} / 1")
    st.markdown("---")

    with st.form("signup", clear_on_submit=True):
        name = st.text_input("Full Name", placeholder="e.g. Rahul Sharma")
        mobile = st.text_input("Mobile Number (10 digits) — this is your login username", max_chars=10)
        password = st.text_input("Password", type="password", placeholder="Minimum 6 characters")
        confirm = st.text_input("Confirm Password", type="password")
        role = st.selectbox("Register As",
                            available,
                            format_func=lambda x: {"player": "🏸 Player", "referee": "🎯 Referee", "admin": "⚙️ Admin"}[x])
        submitted = st.form_submit_button("Register", type="primary", use_container_width=True)

    if submitted:
        errs = []
        if not name.strip():
            errs.append("Name is required.")
        if not mobile.isdigit() or len(mobile) != 10:
            errs.append("Enter a valid 10-digit mobile number.")
        if len(password) < 6:
            errs.append("Password must be at least 6 characters.")
        if password != confirm:
            errs.append("Passwords do not match.")
        if errs:
            for e in errs:
                st.error(e)
        else:
            user, err = signup_user(name.strip(), mobile.strip(), password, role)
            if err:
                if "unique" in err.lower() or "duplicate" in err.lower():
                    st.error("This mobile number is already registered.")
                else:
                    st.error(f"Registration failed: {err}")
            else:
                st.success(f"✅ Registered successfully as a **{role}**! Please switch to the Login tab.")
                new_counts = count_by_role()
                if new_counts["player"] >= 14 and new_counts["referee"] >= 2 and new_counts["admin"] >= 1:
                    update_state(signups_frozen=True)
                st.rerun()


def page_login():
    st.markdown("<div class='section-title'>🔐 Login to Your Account</div>", unsafe_allow_html=True)
    with st.form("login"):
        mobile = st.text_input("Mobile Number", placeholder="Your registered 10-digit number")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
    if submitted:
        if not mobile or not password:
            st.error("Please fill in both fields.")
        else:
            user, err = login_user(mobile.strip(), password)
            if err:
                st.error(err)
            else:
                st.session_state.user = user
                st.success(f"Welcome back, {user['name']}!")
                st.rerun()


def page_admin():
    state = get_state()
    tabs = st.tabs(["👥 Participants", "🎡 Team Assignment", "🏟️ Courts & Referees",
                    "📅 Schedule", "🏆 Leaderboard", "🥊 Knockout"])

    # ── TAB 1: PARTICIPANTS ───────────────────────────────────────────────────
    with tabs[0]:
        st.markdown("<div class='section-title'>Registered Participants</div>", unsafe_allow_html=True)
        users = get_all_users()
        players = [u for u in users if u["role"] == "player"]
        refs = [u for u in users if u["role"] == "referee"]
        admins = [u for u in users if u["role"] == "admin"]
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"**🏸 Players ({len(players)}/14)**")
            for p in players:
                st.markdown(f"<div class='user-chip'><div class='user-chip-name'>{p['name']}</div><div class='user-chip-mobile'>{p['mobile']}</div></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"**🎯 Referees ({len(refs)}/2)**")
            for r in refs:
                st.markdown(f"<div class='user-chip'><div class='user-chip-name'>{r['name']}</div><div class='user-chip-mobile'>{r['mobile']}</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"**⚙️ Admin ({len(admins)}/1)**")
            for a in admins:
                st.markdown(f"<div class='user-chip'><div class='user-chip-name'>{a['name']}</div><div class='user-chip-mobile'>{a['mobile']}</div></div>", unsafe_allow_html=True)
        needed = []
        if len(players) < 14: needed.append(f"{14 - len(players)} more player(s)")
        if len(refs) < 2: needed.append(f"{2 - len(refs)} more referee(s)")
        if needed:
            st.warning(f"Waiting for: {', '.join(needed)}")
        else:
            st.success("✅ All 17 participants registered. Ready to assign teams!")

    # ── TAB 2: TEAM ASSIGNMENT ────────────────────────────────────────────────
    with tabs[1]:
        st.markdown("<div class='section-title'>Team Assignment via Spin the Wheel</div>", unsafe_allow_html=True)
        teams = get_teams()
        if state["teams_assigned"] and teams:
            st.success("✅ Teams have been assigned.")
            show_teams_grid(teams)
        else:
            users = get_all_users()
            players = [u for u in users if u["role"] == "player"]
            if len(players) < 14:
                st.warning(f"Need all 14 players first. Currently {len(players)} registered.")
            else:
                st.info("Spin the wheel to cycle through all 14 players for fun, then click **Auto-Assign Teams** to randomly form 7 teams of 2.")
                components.html(spin_wheel_html([p["name"] for p in players]), height=560)
                st.markdown("---")
                if st.button("⚡ Auto-Assign Teams (Random Draw)", type="primary", use_container_width=True):
                    shuffled = random.sample(players, len(players))
                    assignments = [
                        {"name": TEAM_LABELS[i],
                         "player1_id": shuffled[i * 2]["id"],
                         "player2_id": shuffled[i * 2 + 1]["id"]}
                        for i in range(7)
                    ]
                    create_teams(assignments)
                    update_state(teams_assigned=True)
                    st.success("✅ Teams assigned successfully!")
                    st.rerun()

    # ── TAB 3: COURTS ─────────────────────────────────────────────────────────
    with tabs[2]:
        st.markdown("<div class='section-title'>Assign Referees to Courts</div>", unsafe_allow_html=True)
        courts = get_courts()
        users = get_all_users()
        refs = [u for u in users if u["role"] == "referee"]
        ref_opts = {r["id"]: r["name"] for r in refs}
        if not ref_opts:
            st.warning("No referees registered yet.")
        else:
            for court in courts:
                ref_info = court.get("ref") or {}
                current = ref_info.get("name", "Not assigned") if isinstance(ref_info, dict) else "Not assigned"
                with st.container():
                    c1, c2, c3 = st.columns([1, 2, 1])
                    c1.markdown(f"**🏟️ {court['name']}**")
                    c2.markdown(f"Currently: `{current}`")
                    with c3:
                        sel = st.selectbox("Assign referee", list(ref_opts.keys()),
                                           format_func=lambda x: ref_opts[x],
                                           key=f"court_{court['id']}")
                        if st.button("Assign", key=f"btn_{court['id']}"):
                            assign_court(court["id"], sel)
                            st.success(f"✅ {ref_opts[sel]} assigned to {court['name']}")
                            st.rerun()
                    st.markdown("---")
            if all(c.get("referee_id") for c in courts):
                st.success("✅ Both courts have referees assigned!")

    # ── TAB 4: SCHEDULE ───────────────────────────────────────────────────────
    with tabs[3]:
        st.markdown("<div class='section-title'>Group Stage Schedule (21 Matches)</div>", unsafe_allow_html=True)
        if not state["teams_assigned"]:
            st.warning("Please assign teams first.")
        else:
            existing = get_matches("group")
            if not existing:
                courts = get_courts()
                if not all(c.get("referee_id") for c in courts):
                    st.warning("Please assign referees to both courts first.")
                else:
                    st.info("**21 matches** will be generated — all 7 teams play each other once. No team plays more than 2 back-to-back matches.")
                    if st.button("Generate Match Schedule", type="primary"):
                        court_map = {c["name"]: c for c in courts}
                        team_map = {t["name"]: t["id"] for t in get_teams_simple()}
                        sched = build_schedule(TEAM_LABELS, [c["name"] for c in courts])
                        matches = [
                            {"match_number": i + 1, "stage": "group",
                             "team1_id": team_map[s["team1"]],
                             "team2_id": team_map[s["team2"]],
                             "court_id": court_map[s["court_name"]]["id"],
                             "referee_id": court_map[s["court_name"]].get("referee_id"),
                             "status": "pending", "match_order": i + 1}
                            for i, s in enumerate(sched)
                        ]
                        create_matches(matches)
                        update_state(phase="group_stage", schedule_generated=True)
                        st.success("✅ 21 matches generated!")
                        st.rerun()
            else:
                done = sum(1 for m in existing if m["status"] == "completed")
                live = sum(1 for m in existing if m["status"] == "live")
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Matches", 21)
                c2.metric("Completed", done)
                c3.metric("Live Now", live)
                st.markdown("---")
                for i in range(0, len(existing), 2):
                    slot = existing[i:i + 2]
                    st.markdown(f"<div class='slot-label'>Slot {i // 2 + 1}</div>", unsafe_allow_html=True)
                    for m in slot:
                        render_match(m)
                if done == 21 and not state["group_stage_complete"]:
                    update_state(group_stage_complete=True)
                    st.success("🎉 All group stage matches complete!")

    # ── TAB 5: LEADERBOARD ────────────────────────────────────────────────────
    with tabs[4]:
        st.markdown("<div class='section-title'>Group Stage Leaderboard</div>", unsafe_allow_html=True)
        rows = get_leaderboard()
        if not rows:
            st.info("No match data yet.")
        else:
            render_leaderboard(rows)

    # ── TAB 6: KNOCKOUT ───────────────────────────────────────────────────────
    with tabs[5]:
        st.markdown("<div class='section-title'>Knockout Stage</div>", unsafe_allow_html=True)
        if not state["group_stage_complete"]:
            all_group = get_matches("group")
            done = sum(1 for m in all_group if m["status"] == "completed")
            st.warning(f"Group stage not complete yet. ({done}/21 matches done)")
            return
        sf = get_matches("semifinal")
        tp = get_matches("third_place")
        fn = get_matches("final")
        if not sf:
            top4, _ = get_top4()
            st.markdown("**Top 4 teams qualified for Semifinals:**")
            seeds = ["1st Seed 🥇", "2nd Seed 🥈", "3rd Seed 🥉", "4th Seed"]
            for i, t in enumerate(top4):
                diff = t["score_diff"]
                diff_s = ("+" if diff > 0 else "") + str(diff)
                st.markdown(f"""
                <div class='match-card qualified' style='border-left:4px solid #f59e0b;background:#fffbeb;'>
                    <span class='match-num'>{seeds[i]}</span>
                    <span class='match-teams' style='font-size:17px'>{t['team_name']}</span>
                    <span style='font-size:13px;color:#64748b'>Wins: {t['won']} | Diff: {diff_s}</span>
                </div>
                """, unsafe_allow_html=True)
            st.info("**Semifinal 1:** Seed 1 vs Seed 4  |  **Semifinal 2:** Seed 2 vs Seed 3")
            if st.button("Create Semifinal Matches", type="primary"):
                create_semis(top4)
                update_state(phase="semifinals")
                st.rerun()
        else:
            st.markdown("**Semifinals**")
            for m in sf:
                render_match(m)
            sf_done = all(m["status"] == "completed" for m in sf)
            if sf_done and not tp and not fn:
                if st.button("Create Final & 3rd Place Match", type="primary"):
                    create_finals(sf)
                    update_state(semifinals_complete=True, phase="final")
                    st.rerun()
            if tp:
                st.markdown("---")
                st.markdown("**3rd Place Match 🥉**")
                for m in tp:
                    render_match(m)
            if fn:
                st.markdown("---")
                st.markdown("**Grand Final 🏆**")
                for m in fn:
                    render_match(m)
                if all(m["status"] == "completed" for m in fn):
                    w = (fn[0].get("winner") or {}).get("name", "")
                    if w:
                        st.balloons()
                        st.markdown(f"""
                        <div class='champion-banner'>
                            <div class='champion-label'>🏆 Tournament Champion 🏆</div>
                            <div class='champion-name'>{w}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        update_state(phase="completed")


def page_referee():
    user = st.session_state.user
    st.markdown(f"<div class='section-title'>🎯 Referee Panel — {user['name']}</div>", unsafe_allow_html=True)
    match, court = get_referee_match(user["id"])
    if court is None:
        st.warning("You have not been assigned to a court yet. Please wait for the Admin.")
        return
    st.markdown(f"""
    <div style='background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;
                padding:14px 20px;margin-bottom:20px;display:inline-block;'>
        <span style='font-size:12px;font-weight:600;color:#2563eb;letter-spacing:1px;
                     text-transform:uppercase;'>Your Court</span><br>
        <span style='font-size:22px;font-weight:800;color:#1e3a5f;'>🏟️ {court['name']}</span>
    </div>
    """, unsafe_allow_html=True)
    if match is None:
        st.success("✅ No pending matches on your court right now. Great work!")
        return
    t1 = match.get("team1") or {}
    t2 = match.get("team2") or {}
    status = match.get("status", "pending")
    s1 = match.get("score_team1", 0)
    s2 = match.get("score_team2", 0)
    stage_map = {"group": "Group Stage", "semifinal": "Semifinal",
                 "third_place": "3rd Place Match", "final": "Grand Final"}
    st.markdown(f"""
    <div style='text-align:center;margin-bottom:20px;'>
        <span style='font-size:13px;font-weight:600;color:#64748b;letter-spacing:1px;'>
            MATCH #{match['match_number']} &nbsp;·&nbsp; {stage_map.get(match.get('stage',''),'')}&nbsp;·&nbsp; {court['name']}
        </span>
    </div>
    """, unsafe_allow_html=True)
    c1, cv, c2 = st.columns([2, 1, 2])
    with c1:
        st.markdown(f"""
        <div class='score-box'>
            <div class='score-team-name'>{t1.get('name', 'Team 1')}</div>
            <div class='score-number score-red'>{s1}</div>
        </div>
        """, unsafe_allow_html=True)
    with cv:
        st.markdown("""
        <div style='text-align:center;padding:40px 0;'>
            <div style='font-size:20px;font-weight:800;color:#94a3b8;'>VS</div>
            <div style='font-size:11px;font-weight:600;color:#cbd5e1;margin-top:6px;letter-spacing:1px;'>FIRST TO 15</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class='score-box'>
            <div class='score-team-name'>{t2.get('name', 'Team 2')}</div>
            <div class='score-number score-blue'>{s2}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if status == "completed":
        w = match.get("winner") or {}
        st.success(f"🏆 Match Complete! Winner: **{w.get('name', '?')}**")
        if match.get("stage") == "group" and check_group_done():
            update_state(group_stage_complete=True)
        if st.button("Next Match ➡️", type="primary"):
            st.rerun()
        return
    if status == "pending":
        st.markdown("<div style='text-align:center'>", unsafe_allow_html=True)
        if st.button("▶️ Start Match", type="primary", use_container_width=True):
            start_match(match["id"])
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        return
    # LIVE
    st.markdown("""
    <div style='text-align:center;padding:10px;background:#fee2e2;border:1px solid #fecaca;
                border-radius:8px;margin-bottom:20px;'>
        <span style='color:#dc2626;font-weight:700;font-size:13px;letter-spacing:2px;'>● LIVE</span>
    </div>
    """, unsafe_allow_html=True)
    b1, _, b2 = st.columns([5, 1, 5])
    with b1:
        if st.button(f"➕  +1 Point for {t1.get('name', 'Team 1')}",
                     type="primary", use_container_width=True, key="score_t1"):
            won, _ = add_score(match["id"], "score_team1", s1, t1.get("id"), t2.get("id"))
            if won:
                st.balloons()
            st.rerun()
    with b2:
        if st.button(f"➕  +1 Point for {t2.get('name', 'Team 2')}",
                     type="secondary", use_container_width=True, key="score_t2"):
            won, _ = add_score(match["id"], "score_team2", s2, t1.get("id"), t2.get("id"))
            if won:
                st.balloons()
            st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Score Progress** (first to 15 wins)")
    pc1, pc2 = st.columns(2)
    with pc1:
        st.markdown(f"{t1.get('name')} — **{s1} / 15**")
        st.progress(min(s1 / 15, 1.0))
    with pc2:
        st.markdown(f"{t2.get('name')} — **{s2} / 15**")
        st.progress(min(s2 / 15, 1.0))
    time.sleep(2)
    st.rerun()


def page_player():
    user = st.session_state.user
    teams = get_teams()
    my_team = None
    for t in teams:
        p1 = t.get("p1") or {}
        p2 = t.get("p2") or {}
        if user["id"] in (p1.get("id"), p2.get("id")):
            my_team = t
            break
    tabs = st.tabs(["🔴 Live Matches", "📅 My Schedule", "🏆 Leaderboard", "👥 All Teams"])

    with tabs[0]:
        st.markdown("<div class='section-title'>Live Matches</div>", unsafe_allow_html=True)
        live = get_live_matches()
        if not live:
            st.info("No matches are live right now. Check back soon!")
        else:
            cols = st.columns(min(len(live), 2))
            for i, m in enumerate(live[:2]):
                t1 = m.get("team1") or {}
                t2 = m.get("team2") or {}
                court = m.get("court") or {}
                with cols[i]:
                    st.markdown(f"""
                    <div style='background:#fff;border:1px solid #e2e8f0;border-radius:12px;
                                border-top:4px solid #dc2626;padding:24px;text-align:center;'>
                        <div style='font-size:12px;font-weight:700;color:#2563eb;
                                    letter-spacing:1.5px;text-transform:uppercase;margin-bottom:16px;'>
                            🏟️ {court.get('name','?')} &nbsp;·&nbsp; Match #{m['match_number']}
                        </div>
                        <div style='display:flex;justify-content:space-around;align-items:center;'>
                            <div>
                                <div style='font-size:14px;font-weight:700;color:#dc2626;text-transform:uppercase;'>{t1.get('name','?')}</div>
                                <div style='font-family:Inter,sans-serif;font-size:72px;font-weight:800;color:#dc2626;line-height:1;'>{m['score_team1']}</div>
                            </div>
                            <div style='font-size:18px;font-weight:800;color:#cbd5e1;'>—</div>
                            <div>
                                <div style='font-size:14px;font-weight:700;color:#2563eb;text-transform:uppercase;'>{t2.get('name','?')}</div>
                                <div style='font-family:Inter,sans-serif;font-size:72px;font-weight:800;color:#2563eb;line-height:1;'>{m['score_team2']}</div>
                            </div>
                        </div>
                        <div style='margin-top:12px;'>
                            <span style='background:#fee2e2;color:#dc2626;font-size:11px;font-weight:700;
                                         padding:4px 12px;border-radius:20px;letter-spacing:1px;'>● LIVE</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        st.caption("Auto-refreshes every 3 seconds")
        time.sleep(3)
        st.rerun()

    with tabs[1]:
        st.markdown("<div class='section-title'>My Match Schedule</div>", unsafe_allow_html=True)
        if not my_team:
            st.info("Teams have not been assigned yet.")
        else:
            tn = my_team["name"]
            st.markdown(f"<span class='stat-pill pill-blue'>Your Team: {tn}</span>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            all_m = get_matches()
            my_m = sorted(
                [m for m in all_m if
                 (m.get("team1") or {}).get("id") == my_team["id"] or
                 (m.get("team2") or {}).get("id") == my_team["id"]],
                key=lambda x: x["match_order"]
            )
            if not my_m:
                st.info("Schedule not generated yet.")
            else:
                for m in my_m:
                    render_match(m)
                won = sum(1 for m in my_m if (m.get("winner") or {}).get("id") == my_team["id"] and m["status"] == "completed")
                played = sum(1 for m in my_m if m["status"] == "completed")
                st.markdown(f"<br>**Record:** {won} wins / {played - won} losses from {played} matches played", unsafe_allow_html=True)

    with tabs[2]:
        st.markdown("<div class='section-title'>Group Stage Leaderboard</div>", unsafe_allow_html=True)
        rows = get_leaderboard()
        if not rows:
            st.info("No data yet.")
        else:
            render_leaderboard(rows, my_team["name"] if my_team else None)

    with tabs[3]:
        st.markdown("<div class='section-title'>All Teams</div>", unsafe_allow_html=True)
        if not teams:
            st.info("Teams not assigned yet.")
        else:
            show_teams_grid(teams)


# ─── Init session ─────────────────────────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏸 Serve & Smash")
    try:
        state = get_state()
        counts = count_by_role()
        st.markdown(f"""
        <div class='sidebar-stat'><span class='sidebar-stat-label'>Players</span><span class='sidebar-stat-val'>{counts['player']} / 14</span></div>
        <div class='sidebar-stat'><span class='sidebar-stat-label'>Referees</span><span class='sidebar-stat-val'>{counts['referee']} / 2</span></div>
        <div class='sidebar-stat'><span class='sidebar-stat-label'>Admin</span><span class='sidebar-stat-val'>{counts['admin']} / 1</span></div>
        <div class='sidebar-stat'><span class='sidebar-stat-label'>Phase</span><span class='sidebar-stat-val'>{state['phase'].replace('_',' ').title()}</span></div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Cannot connect to database: {e}")
    st.markdown("---")
    if st.session_state.user:
        u = st.session_state.user
        role_label = {"player": "🏸 Player", "referee": "🎯 Referee", "admin": "⚙️ Admin"}[u["role"]]
        st.success(f"**{u['name']}**\n\n{role_label}")
        if st.button("Logout", use_container_width=True):
            st.session_state.user = None
            st.rerun()
    else:
        st.info("Sign up or log in to continue.")

# ─── Header ───────────────────────────────────────────────────────────────────
try:
    state_phase = get_state()["phase"].replace("_", " ").title()
except Exception:
    state_phase = "Loading..."

st.markdown(f"""
<div class='hero'>
    <div class='hero-icon'>🏸</div>
    <div>
        <div class='hero-title'>Serve &amp; Smash</div>
        <div class='hero-sub'>Badminton Tournament Management System</div>
        <div class='phase-badge'>{state_phase}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Router ───────────────────────────────────────────────────────────────────
user = st.session_state.user
if user is None:
    t1, t2 = st.tabs(["📝 Sign Up", "🔐 Login"])
    with t1:
        page_signup()
    with t2:
        page_login()
else:
    if user["role"] == "admin":
        page_admin()
    elif user["role"] == "referee":
        page_referee()
    elif user["role"] == "player":
        page_player()
