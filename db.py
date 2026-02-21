import hashlib
import streamlit as st
from supabase import create_client, Client

# Read from Streamlit secrets (set in Streamlit Cloud or .streamlit/secrets.toml locally)
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

@st.cache_resource
def get_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

# ─── Auth ────────────────────────────────────────────────────────────────────

def signup_user(name: str, mobile: str, password: str, role: str):
    db = get_client()
    try:
        result = db.table("users").insert({
            "name": name,
            "mobile": mobile,
            "password_hash": hash_password(password),
            "role": role
        }).execute()
        return result.data[0], None
    except Exception as e:
        return None, str(e)

def login_user(mobile: str, password: str):
    db = get_client()
    result = db.table("users").select("*").eq("mobile", mobile).execute()
    if not result.data:
        return None, "Mobile number not found"
    user = result.data[0]
    if not check_password(password, user["password_hash"]):
        return None, "Incorrect password"
    return user, None

def count_by_role():
    db = get_client()
    result = db.table("users").select("role").execute()
    counts = {"player": 0, "referee": 0, "admin": 0}
    for row in result.data:
        counts[row["role"]] += 1
    return counts

def get_all_users():
    db = get_client()
    return db.table("users").select("*").order("created_at").execute().data

# ─── Tournament State ─────────────────────────────────────────────────────────

def get_state():
    db = get_client()
    return db.table("tournament_state").select("*").eq("id", 1).execute().data[0]

def update_state(**kwargs):
    db = get_client()
    db.table("tournament_state").update(kwargs).eq("id", 1).execute()

# ─── Teams ────────────────────────────────────────────────────────────────────

def get_teams():
    db = get_client()
    return db.table("teams").select("*, users!teams_player1_id_fkey(name), users!teams_player2_id_fkey(name)").order("name").execute().data

def create_teams(assignments: list):
    """assignments = [{"name":"Team A","player1_id":..,"player2_id":..}, ...]"""
    db = get_client()
    db.table("teams").insert(assignments).execute()

def get_teams_simple():
    db = get_client()
    return db.table("teams").select("id, name").order("name").execute().data

# ─── Courts ───────────────────────────────────────────────────────────────────

def get_courts():
    db = get_client()
    return db.table("courts").select("*, users(name, id)").execute().data

def assign_referee_to_court(court_id: str, referee_id: str):
    db = get_client()
    db.table("courts").update({"referee_id": referee_id}).eq("id", court_id).execute()

# ─── Matches ──────────────────────────────────────────────────────────────────

def get_matches(stage=None):
    db = get_client()
    q = db.table("matches").select(
        "*, team1:teams!matches_team1_id_fkey(id,name), "
        "team2:teams!matches_team2_id_fkey(id,name), "
        "court:courts(name), "
        "winner:teams!matches_winner_id_fkey(name), "
        "referee:users(name)"
    ).order("match_order")
    if stage:
        q = q.eq("stage", stage)
    return q.execute().data

def create_matches(matches: list):
    db = get_client()
    db.table("matches").insert(matches).execute()

def start_match(match_id: str):
    db = get_client()
    db.table("matches").update({"status": "live"}).eq("id", match_id).execute()

def add_score(match_id: str, team_field: str, current_score: int, team1_id: str, team2_id: str):
    db = get_client()
    new_score = current_score + 1
    db.table("matches").update({team_field: new_score}).eq("id", match_id).execute()
    # Check win condition
    if new_score >= 15:
        winner_id = team1_id if team_field == "score_team1" else team2_id
        db.table("matches").update({
            "winner_id": winner_id,
            "status": "completed",
            "completed_at": "now()"
        }).eq("id", match_id).execute()
        return True, winner_id
    return False, None

def get_live_matches():
    db = get_client()
    return db.table("matches").select(
        "*, team1:teams!matches_team1_id_fkey(id,name), "
        "team2:teams!matches_team2_id_fkey(id,name), "
        "court:courts(name)"
    ).eq("status", "live").execute().data

def get_referee_match(referee_id: str):
    """Get the current live/pending match assigned to this referee's court"""
    db = get_client()
    # Find court for this referee
    court_res = db.table("courts").select("id, name").eq("referee_id", referee_id).execute()
    if not court_res.data:
        return None, None
    court = court_res.data[0]
    # Find pending or live match on that court
    match_res = db.table("matches").select(
        "*, team1:teams!matches_team1_id_fkey(id,name), "
        "team2:teams!matches_team2_id_fkey(id,name), "
        "court:courts(name)"
    ).eq("court_id", court["id"]).in_("status", ["pending", "live"]).order("match_order").limit(1).execute()
    if not match_res.data:
        return None, court
    return match_res.data[0], court

# ─── Leaderboard ──────────────────────────────────────────────────────────────

def get_leaderboard():
    db = get_client()
    rows = db.table("leaderboard").select("*").execute().data
    for r in rows:
        r["score_diff"] = r["score_for"] - r["score_against"]
    return rows

def get_qualified_teams():
    """Return top 4 teams with tiebreaker logic"""
    rows = get_leaderboard()
    matches = get_matches(stage="group")

    def head_to_head_winner(team_a_id, team_b_id):
        for m in matches:
            t1 = m["team1"]["id"] if m["team1"] else None
            t2 = m["team2"]["id"] if m["team2"] else None
            if {t1, t2} == {team_a_id, team_b_id} and m["winner"]:
                w = m.get("winner_id") or ""
                return w
        return None

    def sort_key(team):
        return (team["won"], team["score_diff"], team["score_for"])

    rows.sort(key=sort_key, reverse=True)

    # Handle ties in top 4 boundary
    # Group by wins
    from itertools import groupby
    sorted_rows = sorted(rows, key=lambda x: x["won"], reverse=True)
    return sorted_rows[:4], sorted_rows[4:]

def check_group_stage_complete():
    db = get_client()
    res = db.table("matches").select("id").eq("stage", "group").neq("status", "completed").execute()
    return len(res.data) == 0

def create_knockout_matches(top4):
    """Create SF1, SF2, 3rd place, Final"""
    db = get_client()
    courts = get_courts()
    c2 = next(c for c in courts if c["name"] == "Court 2")
    c3 = next(c for c in courts if c["name"] == "Court 3")

    # Get current max match_order
    max_res = db.table("matches").select("match_number").order("match_number", desc=True).limit(1).execute()
    base = max_res.data[0]["match_number"] if max_res.data else 21
    base_order = db.table("matches").select("match_order").order("match_order", desc=True).limit(1).execute()
    base_ord = base_order.data[0]["match_order"] if base_order.data else 21

    sf1 = {
        "match_number": base + 1, "stage": "semifinal",
        "team1_id": top4[0]["id"], "team2_id": top4[3]["id"],
        "court_id": c2["id"], "referee_id": c2.get("referee_id"),
        "status": "pending", "match_order": base_ord + 1
    }
    sf2 = {
        "match_number": base + 2, "stage": "semifinal",
        "team1_id": top4[1]["id"], "team2_id": top4[2]["id"],
        "court_id": c3["id"], "referee_id": c3.get("referee_id"),
        "status": "pending", "match_order": base_ord + 2
    }
    db.table("matches").insert([sf1, sf2]).execute()

def create_final_matches(sf_matches):
    """After both semis done, create 3rd place and Final"""
    db = get_client()
    courts = get_courts()
    c2 = next(c for c in courts if c["name"] == "Court 2")
    c3 = next(c for c in courts if c["name"] == "Court 3")

    max_res = db.table("matches").select("match_number").order("match_number", desc=True).limit(1).execute()
    base = max_res.data[0]["match_number"]
    base_ord = db.table("matches").select("match_order").order("match_order", desc=True).limit(1).execute().data[0]["match_order"]

    # sf_matches sorted by match_number
    sf_matches = sorted(sf_matches, key=lambda x: x["match_number"])
    sf1, sf2 = sf_matches[0], sf_matches[1]

    # Winners go to Final, Losers go to 3rd place
    def loser_id(m):
        t1 = m["team1"]["id"] if m.get("team1") else m.get("team1_id")
        t2 = m["team2"]["id"] if m.get("team2") else m.get("team2_id")
        w = m.get("winner_id") or (m["winner"]["id"] if m.get("winner") else None)
        return t1 if w == t2 else t2

    def winner_id(m):
        return m.get("winner_id") or (m["winner"]["id"] if m.get("winner") else None)

    bronze = {
        "match_number": base + 1, "stage": "third_place",
        "team1_id": loser_id(sf1), "team2_id": loser_id(sf2),
        "court_id": c2["id"], "referee_id": c2.get("referee_id"),
        "status": "pending", "match_order": base_ord + 1
    }
    final = {
        "match_number": base + 2, "stage": "final",
        "team1_id": winner_id(sf1), "team2_id": winner_id(sf2),
        "court_id": c3["id"], "referee_id": c3.get("referee_id"),
        "status": "pending", "match_order": base_ord + 2
    }
    db.table("matches").insert([bronze, final]).execute()
