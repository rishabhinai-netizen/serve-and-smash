import hashlib
import json
import random

import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client

st.set_page_config(page_title="Serve & Smash | Pickleball",page_icon="🏓",layout="wide",initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Space Grotesk',sans-serif;}
.stApp{background:#f0f4f8;}.block-container{padding-top:.5rem;max-width:1140px;}
section[data-testid="stSidebar"]{background:#fff;border-right:1px solid #e2e8f0;}
header[data-testid="stHeader"]{background:transparent;}
div[data-testid="stDecoration"]{display:none;}
.hero{background:linear-gradient(135deg,#0f172a 0%,#1e40af 55%,#0ea5e9 100%);border-radius:16px;padding:28px 34px;margin-bottom:20px;color:#fff;display:flex;align-items:center;gap:18px;box-shadow:0 8px 32px rgba(30,64,175,.28);}
.hero-icon{font-size:50px;line-height:1;filter:drop-shadow(0 4px 8px rgba(0,0,0,.3));}
.hero-title{font-family:'Inter',sans-serif;font-size:26px;font-weight:900;letter-spacing:-.5px;margin:0;}
.hero-sub{font-size:12px;color:rgba(255,255,255,.7);margin-top:3px;}
.phase-pill{display:inline-block;background:rgba(255,255,255,.15);color:#fff;font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase;padding:3px 12px;border-radius:20px;margin-top:8px;border:1px solid rgba(255,255,255,.25);}
.stitle{font-family:'Inter',sans-serif;font-size:16px;font-weight:800;color:#0f172a;margin-bottom:12px;}
.mrow{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:11px 14px;margin-bottom:6px;display:flex;align-items:center;gap:10px;font-size:14px;}
.mrow.live{border-left:4px solid #ef4444;background:#fff5f5;}
.mrow.completed{border-left:4px solid #22c55e;background:#f0fdf4;}
.mrow.pending{border-left:4px solid #94a3b8;}
.mrow-teams{font-size:14px;font-weight:700;color:#0f172a;flex:1;}
.mrow-players{font-size:11px;color:#94a3b8;margin-top:2px;}
.mrow-vs{color:#cbd5e1;font-size:11px;margin:0 5px;}
.mrow-score{font-family:'Inter',sans-serif;font-size:16px;font-weight:900;color:#0f172a;min-width:60px;text-align:center;}
.badge-live{font-size:10px;font-weight:700;color:#ef4444;background:#fee2e2;padding:3px 9px;border-radius:20px;animation:blink 1.2s infinite;white-space:nowrap;}
.badge-done{font-size:10px;font-weight:600;color:#15803d;background:#dcfce7;padding:3px 9px;border-radius:20px;white-space:nowrap;}
.badge-pending{font-size:10px;font-weight:600;color:#64748b;background:#f1f5f9;padding:3px 9px;border-radius:20px;white-space:nowrap;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.5}}
.court-hdr{font-size:12px;font-weight:800;color:#2563eb;letter-spacing:2px;text-transform:uppercase;margin:16px 0 8px;padding-bottom:6px;border-bottom:2px solid #eff6ff;}
.sbox{background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:18px;text-align:center;}
.sbox-name{font-size:12px;font-weight:700;color:#64748b;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;}
.sbox-num{font-family:'Inter',sans-serif;font-size:84px;font-weight:900;line-height:1;}
.score-red{color:#dc2626;}.score-blue{color:#1d4ed8;}
.live-card{background:#fff;border:1px solid #e2e8f0;border-top:4px solid #ef4444;border-radius:14px;padding:20px;text-align:center;box-shadow:0 2px 12px rgba(239,68,68,.1);margin-bottom:14px;}
.live-teams{display:flex;justify-content:space-around;align-items:center;margin:8px 0;}
.live-team-name{font-size:13px;font-weight:800;color:#0f172a;text-transform:uppercase;}
.live-team-players{font-size:11px;color:#94a3b8;margin:3px 0 6px;}
.live-score{font-family:'Inter',sans-serif;font-size:68px;font-weight:900;line-height:1;}
.lb-head{display:grid;grid-template-columns:36px 1fr 52px 40px 40px 64px 64px 64px;gap:4px;padding:7px 12px;background:#f8fafc;border-radius:8px 8px 0 0;font-size:10px;font-weight:700;color:#64748b;letter-spacing:1.5px;text-transform:uppercase;border:1px solid #e2e8f0;}
.lb-row{display:grid;grid-template-columns:36px 1fr 52px 40px 40px 64px 64px 64px;gap:4px;padding:10px 12px;background:#fff;border:1px solid #e2e8f0;border-top:none;font-size:13px;align-items:center;}
.lb-row:last-child{border-radius:0 0 8px 8px;}
.lb-row.qual{border-left:3px solid #f59e0b;background:#fffbeb;}
.lb-row.mine{background:#eff6ff;border-left:3px solid #2563eb;}
.bracket-match{background:#fff;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.06);margin-bottom:12px;}
.bracket-hdr{background:linear-gradient(135deg,#1e40af,#2563eb);color:#fff;padding:8px 14px;font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;}
.bracket-team{display:flex;justify-content:space-between;align-items:center;padding:11px 14px;border-bottom:1px solid #f1f5f9;font-size:14px;font-weight:700;color:#0f172a;}
.bracket-team.winner{background:#f0fdf4;color:#15803d;}
.bracket-team.loser{background:#fafafa;color:#94a3b8;}
.bracket-seed{font-size:10px;font-weight:600;color:#94a3b8;background:#f8fafc;padding:2px 7px;border-radius:20px;margin-right:6px;}
.bracket-sc{font-family:'Inter',sans-serif;font-size:18px;font-weight:900;}
.moment-chip{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700;margin:2px;}
.m-good{background:#fef9c3;color:#854d0e;border:1px solid #fde68a;}
.m-rally{background:#dbeafe;color:#1d4ed8;border:1px solid #bfdbfe;}
.m-comeback{background:#fce7f3;color:#9d174d;border:1px solid #fbcfe8;}
.dispute-box{background:#fff7ed;border:1px solid #fed7aa;border-radius:10px;padding:14px 18px;margin:8px 0;}
.dispute-resolved-box{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:12px 16px;margin:6px 0;font-size:13px;color:#15803d;}
.frozen-banner{background:#fff1f2;border:2px solid #fca5a5;border-radius:12px;padding:20px;text-align:center;margin:12px 0;}
.frozen-title{font-size:18px;font-weight:800;color:#dc2626;margin-bottom:6px;}
.uchip{background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:9px 13px;margin-bottom:5px;}
.uchip-name{font-size:14px;font-weight:700;color:#0f172a;}
.sb-stat{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #f1f5f9;font-size:13px;}
.sb-lbl{color:#64748b;font-weight:500;}.sb-val{font-weight:700;color:#0f172a;}
.match-complete{background:linear-gradient(135deg,#0f172a,#1e40af);border-radius:16px;padding:32px;text-align:center;color:#fff;box-shadow:0 8px 32px rgba(30,64,175,.3);margin:12px 0;}
.mc-label{font-size:11px;font-weight:700;letter-spacing:3px;color:#fbbf24;text-transform:uppercase;margin-bottom:6px;}
.mc-winner{font-family:'Inter',sans-serif;font-size:36px;font-weight:900;letter-spacing:-.5px;}
.mc-score{font-size:24px;font-weight:800;color:rgba(255,255,255,.8);margin-top:6px;}
.moment-broadcast{background:linear-gradient(135deg,#1e40af,#7c3aed);color:#fff;border-radius:10px;padding:12px 16px;margin:4px 0;display:flex;align-items:center;gap:10px;}
.mb-icon{font-size:24px;}.mb-text{font-size:13px;font-weight:700;}
.mb-sub{font-size:11px;color:rgba(255,255,255,.75);margin-top:2px;}
.award-card{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:18px;margin-bottom:12px;}
.award-winner-box{background:linear-gradient(135deg,#fef3c7,#fde68a);border:1px solid #f59e0b;border-radius:10px;padding:14px;text-align:center;margin-top:10px;}
.award-winner-name{font-size:18px;font-weight:900;color:#92400e;}
.vote-option{background:#fff;border:2px solid #e2e8f0;border-radius:10px;padding:10px 14px;margin-bottom:6px;cursor:pointer;transition:all .15s;}
.vote-option:hover{border-color:#2563eb;background:#eff6ff;}
.vote-option.selected{border-color:#2563eb;background:#eff6ff;}
.history-card{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px 16px;margin-bottom:8px;}
</style>
""", unsafe_allow_html=True)

# ─── DB — fresh client each call prevents HTTP/2 stale socket (Errno 11) ──────
def get_db() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def hp(pw): return hashlib.sha256(pw.encode()).hexdigest()

# ─── Constants ────────────────────────────────────────────────────────────────
TEAM_NAMES = [
    "Vedant's Kitchens","Vedu's Rally Crew","Dink with Vedant",
    "Pickleball Warriors","Drop Shot Society","Baseline Rebels","Spin Doctors"
]
TEAM_LETTERS = ["A","B","C","D","E","F","G"]
TEAM_COLORS  = ["#2563eb","#dc2626","#16a34a","#9333ea","#ea580c","#0891b2","#be185d"]
LIMITS = {"player":14,"referee":2,"admin":1}

# Fixed schedule (A=index0 … G=index6) — exactly as specified
FIXED_SCHEDULE = [
    ("A","B","Court 2"),("E","F","Court 2"),("B","C","Court 2"),("F","G","Court 2"),
    ("A","C","Court 2"),("C","E","Court 2"),("B","G","Court 2"),("B","E","Court 2"),
    ("A","D","Court 2"),("B","F","Court 2"),("A","E","Court 2"),
    ("C","D","Court 3"),("G","A","Court 3"),("D","E","Court 3"),("B","D","Court 3"),
    ("E","G","Court 3"),("A","F","Court 3"),("D","F","Court 3"),("C","G","Court 3"),
    ("C","F","Court 3"),("D","G","Court 3"),
]

# ─── DB helpers ───────────────────────────────────────────────────────────────
def signup_user(name, mobile, password, role):
    try:
        r = get_db().table("users").insert({"name":name,"mobile":mobile,
            "password_hash":hp(password),"role":role}).execute()
        return r.data[0], None
    except Exception as e:
        return None, str(e)

def login_user(mobile, password):
    r = get_db().table("users").select("*").eq("mobile",mobile).execute()
    if not r.data: return None,"Mobile not registered."
    u = r.data[0]
    if hp(password) != u["password_hash"]: return None,"Wrong password."
    return u, None

def count_by_role():
    r = get_db().table("users").select("role").execute()
    c = {"player":0,"referee":0,"admin":0}
    for row in r.data: c[row["role"]] = c.get(row["role"],0)+1
    return c

def get_all_users():
    return get_db().table("users").select("id,name,role,created_at").order("created_at").execute().data

def get_state():
    return get_db().table("tournament_state").select("*").eq("id",1).execute().data[0]

def update_state(**kw):
    get_db().table("tournament_state").update(kw).eq("id",1).execute()

def get_teams():
    return get_db().table("teams").select(
        "*, p1:users!teams_player1_id_fkey(id,name), p2:users!teams_player2_id_fkey(id,name)"
    ).order("name").execute().data

def get_teams_simple():
    return get_db().table("teams").select("id,name").order("name").execute().data

def create_teams(assignments):
    get_db().table("teams").insert(assignments).execute()

def get_courts():
    return get_db().table("courts").select("*, ref:users(id,name)").execute().data

def auto_assign_referees():
    refs = get_db().table("users").select("id,name").eq("role","referee").order("created_at").execute().data
    courts = get_courts()
    c2 = next((c for c in courts if c["name"]=="Court 2"),None)
    c3 = next((c for c in courts if c["name"]=="Court 3"),None)
    if len(refs)>=1 and c2: get_db().table("courts").update({"referee_id":refs[0]["id"]}).eq("id",c2["id"]).execute()
    if len(refs)>=2 and c3: get_db().table("courts").update({"referee_id":refs[1]["id"]}).eq("id",c3["id"]).execute()

def _ms():
    return ("*, "
        "team1:teams!matches_team1_id_fkey(id,name,p1:users!teams_player1_id_fkey(id,name),p2:users!teams_player2_id_fkey(id,name)),"
        "team2:teams!matches_team2_id_fkey(id,name,p1:users!teams_player1_id_fkey(id,name),p2:users!teams_player2_id_fkey(id,name)),"
        "court:courts(id,name),winner:teams!matches_winner_id_fkey(id,name)")

def get_matches(stage=None):
    q = get_db().table("matches").select(_ms()).order("match_order")
    if stage: q = q.eq("stage",stage)
    return q.execute().data

def get_live_matches():
    return get_db().table("matches").select(_ms()).eq("status","live").execute().data

def get_court_matches(court_id):
    return get_db().table("matches").select(_ms()).eq("court_id",court_id).order("match_order").execute().data

def get_referee_active_match(court_id):
    r = get_db().table("matches").select(_ms()).eq("court_id",court_id)\
        .in_("status",["pending","live"]).order("match_order").limit(1).execute()
    return r.data[0] if r.data else None

def get_referee_court(ref_id):
    r = get_db().table("courts").select("id,name").eq("referee_id",ref_id).execute()
    return r.data[0] if r.data else None

def create_matches(matches):
    get_db().table("matches").insert(matches).execute()

def start_match(mid):
    get_db().table("matches").update({"status":"live","score_history":"[]"}).eq("id",mid).execute()

def add_score(mid, field, s1, s2, t1id, t2id, history):
    ns1 = s1+(1 if field=="score_team1" else 0)
    ns2 = s2+(1 if field=="score_team2" else 0)
    hist2 = list(history)+[{"t1":s1,"t2":s2}]
    won = ns1>=15 or ns2>=15
    wid = (t1id if ns1>=15 else t2id) if won else None
    payload = {"score_team1":ns1,"score_team2":ns2,"score_history":json.dumps(hist2)}
    if won: payload["winner_id"]=wid; payload["status"]="completed"
    get_db().table("matches").update(payload).eq("id",mid).execute()
    return won, wid, ns1, ns2

def undo_score(mid, history):
    if not history: return
    prev = history[-1]
    get_db().table("matches").update({
        "score_team1":prev["t1"],"score_team2":prev["t2"],
        "score_history":json.dumps(history[:-1]),"winner_id":None,"status":"live"
    }).eq("id",mid).execute()

def get_leaderboard():
    rows = get_db().table("leaderboard").select("*").execute().data
    for r in rows: r["score_diff"] = r["score_for"]-r["score_against"]
    return rows

def check_group_done():
    r = get_db().table("matches").select("id").eq("stage","group").neq("status","completed").execute()
    return len(r.data)==0

def get_top4():
    rows = get_leaderboard()
    rows.sort(key=lambda x:(x["won"],x["score_diff"],x["score_for"]),reverse=True)
    return rows[:4], rows[4:]

def create_semis(top4):
    courts = get_courts()
    c2 = next(c for c in courts if c["name"]=="Court 2")
    c3 = next(c for c in courts if c["name"]=="Court 3")
    mn = get_db().table("matches").select("match_number").order("match_number",desc=True).limit(1).execute()
    mo = get_db().table("matches").select("match_order").order("match_order",desc=True).limit(1).execute()
    bn = mn.data[0]["match_number"] if mn.data else 21
    bo = mo.data[0]["match_order"] if mo.data else 21
    get_db().table("matches").insert([
        {"match_number":bn+1,"stage":"semifinal","team1_id":top4[0]["id"],"team2_id":top4[3]["id"],
         "court_id":c2["id"],"referee_id":c2.get("referee_id"),"status":"pending","match_order":bo+1},
        {"match_number":bn+2,"stage":"semifinal","team1_id":top4[1]["id"],"team2_id":top4[2]["id"],
         "court_id":c3["id"],"referee_id":c3.get("referee_id"),"status":"pending","match_order":bo+2},
    ]).execute()

def create_finals(sf):
    courts = get_courts()
    c2 = next(c for c in courts if c["name"]=="Court 2")
    c3 = next(c for c in courts if c["name"]=="Court 3")
    mn = get_db().table("matches").select("match_number").order("match_number",desc=True).limit(1).execute()
    mo = get_db().table("matches").select("match_order").order("match_order",desc=True).limit(1).execute()
    bn = mn.data[0]["match_number"]; bo = mo.data[0]["match_order"]
    sfs = sorted(sf,key=lambda x:x["match_number"])
    def loser(m):
        t1=(m.get("team1") or {}).get("id"); t2=(m.get("team2") or {}).get("id")
        w=m.get("winner_id") or (m.get("winner") or {}).get("id")
        return t1 if w==t2 else t2
    def winner(m):
        return m.get("winner_id") or (m.get("winner") or {}).get("id")
    get_db().table("matches").insert([
        {"match_number":bn+1,"stage":"third_place","team1_id":loser(sfs[0]),"team2_id":loser(sfs[1]),
         "court_id":c2["id"],"referee_id":c2.get("referee_id"),"status":"pending","match_order":bo+1},
        {"match_number":bn+2,"stage":"final","team1_id":winner(sfs[0]),"team2_id":winner(sfs[1]),
         "court_id":c3["id"],"referee_id":c3.get("referee_id"),"status":"pending","match_order":bo+2},
    ]).execute()

def add_moment(match_id, mtype, team_id, score_str):
    get_db().table("match_moments").insert({
        "match_id":match_id,"moment_type":mtype,"team_id":team_id,"score_at_time":score_str
    }).execute()

def get_moments(match_id):
    return get_db().table("match_moments").select(
        "*, team:teams(name)"
    ).eq("match_id",match_id).order("created_at").execute().data

def get_all_moments():
    """All moments across all matches for broadcast feed."""
    return get_db().table("match_moments").select(
        "*, team:teams(name), match:matches(match_number,stage)"
    ).order("created_at",desc=True).limit(20).execute().data

def flag_dispute(match_id, ref_id, note):
    get_db().table("match_disputes").insert({
        "match_id":match_id,"referee_id":ref_id,"note":note,"status":"open"
    }).execute()

def get_open_disputes():
    return get_db().table("match_disputes").select(
        "*, match:matches(id,match_number,score_team1,score_team2,"
        "team1:teams!matches_team1_id_fkey(name),"
        "team2:teams!matches_team2_id_fkey(name)),"
        "referee:users(name)"
    ).eq("status","open").execute().data

def get_all_disputes():
    return get_db().table("match_disputes").select(
        "*, match:matches(id,match_number,score_team1,score_team2,"
        "team1:teams!matches_team1_id_fkey(name),"
        "team2:teams!matches_team2_id_fkey(name)),"
        "referee:users(name)"
    ).order("created_at",desc=True).execute().data

def get_referee_open_dispute(court_id):
    """Check if there's an open dispute for ANY match on this court."""
    try:
        # Get all open disputes with their match court_id
        r = get_db().table("match_disputes").select(
            "id, status, note, match_id, match:matches!inner(court_id)"
        ).eq("status","open").execute()
        for d in r.data:
            m = d.get("match") or {}
            if m.get("court_id") == court_id:
                return d
    except Exception:
        pass
    return None

def resolve_dispute(dispute_id, match_id, undo):
    from datetime import datetime
    get_db().table("match_disputes").update({
        "status":"resolved","resolved_at":datetime.utcnow().isoformat()
    }).eq("id",dispute_id).execute()
    if undo and match_id:
        m = get_db().table("matches").select("score_history,score_team1,score_team2")\
            .eq("id",match_id).execute().data[0]
        hist = m.get("score_history") or []
        if isinstance(hist,str): hist = json.loads(hist) if hist else []
        undo_score(match_id,hist)

# Awards / Voting
def get_award_categories():
    return get_db().table("award_categories").select("*").order("created_at").execute().data

def get_my_votes(user_id):
    r = get_db().table("award_votes").select("category_id,voted_team_id").eq("voter_id",user_id).execute()
    return {row["category_id"]: row["voted_team_id"] for row in r.data}

def cast_vote(user_id, category_id, team_id):
    try:
        get_db().table("award_votes").insert({
            "voter_id":user_id,"category_id":category_id,"voted_team_id":team_id
        }).execute()
        return True
    except: return False

def get_vote_results():
    """Tally votes per category."""
    votes = get_db().table("award_votes").select("category_id,voted_team_id,team:teams(name)").execute().data
    cats  = get_award_categories()
    tally = {}
    for v in votes:
        cid = v["category_id"]; tn = (v.get("team") or {}).get("name","?")
        tally.setdefault(cid,{})
        tally[cid][tn] = tally[cid].get(tn,0)+1
    result = {}
    for cat in cats:
        cid = cat["id"]
        counts = tally.get(cid,{})
        winner = max(counts,key=counts.get) if counts else None
        result[cid] = {"cat":cat,"counts":counts,"winner":winner}
    return result

def get_revealed():
    r = get_db().table("award_results_revealed").select("revealed").eq("id",1).execute()
    return r.data[0]["revealed"] if r.data else False

def set_revealed(val):
    get_db().table("award_results_revealed").update({"revealed":val}).eq("id",1).execute()

# History
def get_match_history():
    """All completed matches with moments."""
    return get_db().table("matches").select(_ms()).eq("status","completed").order("match_order").execute().data

# ─── Render helpers ───────────────────────────────────────────────────────────
def _tp(tobj):
    p1=(tobj.get("p1") or {}).get("name","?"); p2=(tobj.get("p2") or {}).get("name","?")
    return p1, p2

def render_match_row(m):
    t1=m.get("team1") or {}; t2=m.get("team2") or {}
    court=m.get("court") or {}; winner=m.get("winner") or {}
    status=m.get("status","pending")
    s1=m.get("score_team1",0); s2=m.get("score_team2",0)
    t1p1,t1p2=_tp(t1); t2p1,t2p2=_tp(t2)
    t1n=t1.get("name","?"); t2n=t2.get("name","?")
    score_str = f"{s1} — {s2}" if status!="pending" else "vs"
    if status=="live": badge='<span class="badge-live">● LIVE</span>'
    elif status=="completed": badge='<span class="badge-done">✓ Done</span>'
    else: badge='<span class="badge-pending">Upcoming</span>'
    win_part=""
    if winner.get("name") and status=="completed":
        win_part=f'&nbsp;<span style="color:#15803d;font-size:12px;font-weight:700">🏆 {winner["name"]}</span>'
    stage_map={"group":"","semifinal":"SEMI · ","third_place":"3RD · ","final":"FINAL · "}
    stage_pre=stage_map.get(m.get("stage",""),"")
    court_name=court.get("name","?")
    st.markdown(
        f'<div class="mrow {status}">'
        f'<div style="flex:1">'
        f'<div class="mrow-teams">{t1n}<span class="mrow-vs">vs</span>{t2n}{win_part}</div>'
        f'<div class="mrow-players">{stage_pre}{court_name} · 🏓{t1p1}&amp;{t1p2} | 🏓{t2p1}&amp;{t2p2}</div>'
        f'</div>'
        f'<span class="mrow-score">{score_str}</span>{badge}</div>',
        unsafe_allow_html=True
    )

def render_schedule_by_court(matches):
    groups={}
    for m in matches:
        cn=(m.get("court") or {}).get("name","Unknown")
        groups.setdefault(cn,[]).append(m)
    for cn,cms in sorted(groups.items()):
        st.markdown(f'<div class="court-hdr">🏟️ {cn}</div>',unsafe_allow_html=True)
        for m in cms: render_match_row(m)

def render_leaderboard(rows, my_team_name=None):
    rows=sorted(rows,key=lambda x:(x["won"],x["score_diff"],x["score_for"]),reverse=True)
    pos_icons={1:"🥇",2:"🥈",3:"🥉",4:"4th"}
    st.markdown('<div class="lb-head"><div>Pos</div><div>Team</div><div>P</div><div>W</div><div>L</div><div>For</div><div>Agn</div><div>Diff</div></div>',unsafe_allow_html=True)
    for i,row in enumerate(rows):
        pos=i+1; diff=row["score_diff"]; ds=("+" if diff>0 else "")+str(diff)
        dc="#15803d" if diff>0 else "#dc2626" if diff<0 else "#64748b"
        is_mine=my_team_name and row["team_name"]==my_team_name
        cls="mine" if is_mine else ("qual" if pos<=4 else "")
        star=" ⭐" if is_mine else ""
        st.markdown(
            f'<div class="lb-row {cls}">'
            f'<div style="font-weight:800">{pos_icons.get(pos,str(pos))}</div>'
            f'<div style="font-weight:700">{row["team_name"]}{star}</div>'
            f'<div style="color:#64748b">{row["matches_played"]}</div>'
            f'<div style="color:#15803d;font-weight:700">{row["won"]}</div>'
            f'<div style="color:#dc2626">{row["lost"]}</div>'
            f'<div style="color:#2563eb">{row["score_for"]}</div>'
            f'<div style="color:#7c3aed">{row["score_against"]}</div>'
            f'<div style="color:{dc};font-weight:700">{ds}</div></div>',
            unsafe_allow_html=True
        )
    st.caption("🏅 Top 4 qualify" + (" | ⭐ = Your team" if my_team_name else ""))

def render_bracket(matches, title):
    st.markdown(f'<div class="stitle">🏆 {title}</div>',unsafe_allow_html=True)
    for m in matches:
        t1=m.get("team1") or {}; t2=m.get("team2") or {}
        winner=m.get("winner") or {}; status=m.get("status","pending")
        s1=m.get("score_team1",0); s2=m.get("score_team2",0)
        court=m.get("court") or {}
        t1c="winner" if winner.get("id")==t1.get("id") and status=="completed" else ("loser" if status=="completed" else "")
        t2c="winner" if winner.get("id")==t2.get("id") and status=="completed" else ("loser" if status=="completed" else "")
        def sc(c): return "#15803d" if c=="winner" else "#94a3b8" if c=="loser" else "#0f172a"
        stage_map={"semifinal":"Semifinal","third_place":"3rd Place","final":"Grand Final"}
        st.markdown(
            f'<div class="bracket-match">'
            f'<div class="bracket-hdr">{stage_map.get(m.get("stage",""),"Match")} · #{m["match_number"]} · {court.get("name","?")}</div>'
            f'<div class="bracket-team {t1c}"><span>{t1.get("name","?")}</span><span class="bracket-sc" style="color:{sc(t1c)}">{s1}</span></div>'
            f'<div class="bracket-team {t2c}"><span>{t2.get("name","?")}</span><span class="bracket-sc" style="color:{sc(t2c)}">{s2}</span></div>'
            f'</div>',unsafe_allow_html=True
        )

@st.fragment(run_every=5)
def render_live_scores_widget(auto_refresh=True):
    """Renders live scores + highlights. Decorated with @st.fragment(run_every=5)
    so Streamlit re-runs ONLY this fragment every 5 s — zero sleep, zero Errno 11."""
    live = get_live_matches()
    if not live:
        st.info("⏳ No live matches right now.")
    else:
        cols = st.columns(min(len(live),2))
        for i,m in enumerate(live[:2]):
            t1=m.get("team1") or {}; t2=m.get("team2") or {}
            court=m.get("court") or {}
            s1=m.get("score_team1",0); s2=m.get("score_team2",0)
            t1p1,t1p2=_tp(t1); t2p1,t2p2=_tp(t2)
            with cols[i%2]:
                st.markdown(
                    f'<div class="live-card">'
                    f'<div style="font-size:10px;font-weight:800;color:#ef4444;letter-spacing:2px;text-transform:uppercase;margin-bottom:10px">● LIVE · {court.get("name","?")} · Match {m["match_number"]}</div>'
                    f'<div class="live-teams">'
                    f'<div><div class="live-team-name">{t1.get("name","?")}</div>'
                    f'<div class="live-team-players">🏓 {t1p1} &amp; {t1p2}</div>'
                    f'<div class="live-score" style="color:#dc2626">{s1}</div></div>'
                    f'<div style="font-size:20px;font-weight:900;color:#e2e8f0">—</div>'
                    f'<div><div class="live-team-name">{t2.get("name","?")}</div>'
                    f'<div class="live-team-players">🏓 {t2p1} &amp; {t2p2}</div>'
                    f'<div class="live-score" style="color:#1d4ed8">{s2}</div></div>'
                    f'</div><div style="font-size:11px;color:#94a3b8">First to 15 wins</div></div>',
                    unsafe_allow_html=True
                )
    # Moments feed — visible to everyone
    moments = get_all_moments()
    if moments:
        st.markdown("<br>",unsafe_allow_html=True)
        st.markdown('<div class="stitle">🎉 Highlights Feed</div>',unsafe_allow_html=True)
        icons_map={"good_shot":"🎯","great_rally":"🔥","crazy_comeback":"⚡"}
        label_map={"good_shot":"Good Shot","great_rally":"Great Rally","crazy_comeback":"Crazy Comeback!"}
        for mom in moments[:8]:
            mtype=mom["moment_type"]
            team_name=(mom.get("team") or {}).get("name","")
            match_n=(mom.get("match") or {}).get("match_number","?")
            desc=f"{label_map.get(mtype,mtype)}{' — '+team_name if team_name else ''}"
            sub=f"Match {match_n} · at {mom.get('score_at_time','?')}"
            st.markdown(
                f'<div class="moment-broadcast">'
                f'<div class="mb-icon">{icons_map.get(mtype,"🏓")}</div>'
                f'<div><div class="mb-text">{desc}</div><div class="mb-sub">{sub}</div></div>'
                f'</div>',unsafe_allow_html=True
            )
    if auto_refresh:
        st.caption("🔄 Auto-refreshing every 5 seconds")

def show_teams_grid(teams):
    cols=st.columns(4)
    for i,t in enumerate(teams):
        p1n=(t.get("p1") or {}).get("name","?"); p2n=(t.get("p2") or {}).get("name","?")
        color=TEAM_COLORS[i%len(TEAM_COLORS)]
        with cols[i%4]:
            st.markdown(
                f'<div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;border-top:3px solid {color};padding:13px;margin-bottom:10px">'
                f'<div style="font-size:13px;font-weight:800;color:#0f172a;margin-bottom:5px">{t["name"]}</div>'
                f'<div style="font-size:12px;color:#475569">🏓 {p1n}</div>'
                f'<div style="font-size:12px;color:#475569">🏓 {p2n}</div></div>',
                unsafe_allow_html=True
            )

def spin_wheel_html(player_names):
    colors=["#2563eb","#dc2626","#16a34a","#9333ea","#ea580c","#0891b2","#be185d","#b45309","#0f766e","#4338ca","#c2410c","#1d4ed8","#15803d","#7e22ce"]
    nj=json.dumps(player_names); cj=json.dumps(colors[:len(player_names)])
    return f"""<!DOCTYPE html><html><head>
<style>body{{background:#f0f4f8;display:flex;flex-direction:column;align-items:center;justify-content:center;height:520px;margin:0;font-family:'Space Grotesk',system-ui,sans-serif;}}
canvas{{border-radius:50%;box-shadow:0 8px 36px rgba(37,99,235,.28);}}
#result{{margin-top:12px;font-size:15px;font-weight:700;color:#1d4ed8;min-height:22px;text-align:center;}}
#prog{{margin-top:5px;font-size:12px;color:#64748b;text-align:center;}}
.wrap{{position:relative;}}
.ptr{{position:absolute;top:50%;right:-16px;transform:translateY(-50%);width:0;height:0;border-top:12px solid transparent;border-bottom:12px solid transparent;border-left:20px solid #f59e0b;}}
</style></head><body>
<div class="wrap"><canvas id="wh" width="280" height="280"></canvas><div class="ptr"></div></div>
<div id="result">Click the wheel to start!</div><div id="prog"></div>
<script>
const names={nj},colors={cj};
const cv=document.getElementById('wh'),ctx=cv.getContext('2d');
let cur=0,spinning=false,rem=[...names],spinIdx=0;
const teams=["Vedant's Kitchens","Vedu's Rally Crew","Dink with Vedant","Pickleball Warriors","Drop Shot Society","Baseline Rebels","Spin Doctors"];
function draw(a){{const cx=140,cy=140,r=132,disp=rem.length>0?rem:names,arc=2*Math.PI/disp.length;
ctx.clearRect(0,0,280,280);
for(let i=0;i<disp.length;i++){{const s=a+i*arc;ctx.beginPath();ctx.moveTo(cx,cy);ctx.arc(cx,cy,r,s,s+arc);ctx.closePath();
ctx.fillStyle=colors[i%colors.length];ctx.fill();ctx.strokeStyle='rgba(255,255,255,.5)';ctx.lineWidth=2;ctx.stroke();
ctx.save();ctx.translate(cx,cy);ctx.rotate(s+arc/2);ctx.textAlign='right';ctx.fillStyle='#fff';
ctx.font='bold '+Math.min(12,150/disp.length+5)+'px Space Grotesk,system-ui';
const n=disp[i];ctx.fillText(n.length>14?n.substring(0,13)+'…':n,r-7,4);ctx.restore();}}
ctx.beginPath();ctx.arc(cx,cy,16,0,2*Math.PI);ctx.fillStyle='#fff';ctx.fill();}}
function spin(){{if(spinning||rem.length===0)return;spinning=true;
const extra=(4+Math.random()*4)*2*Math.PI,stop=Math.random()*2*Math.PI,total=extra+stop,dur=3200,t0=performance.now(),a0=cur;
function anim(now){{const el=now-t0,t=Math.min(el/dur,1),e=1-Math.pow(1-t,4);cur=a0+total*e;draw(cur);
if(t<1){{requestAnimationFrame(anim);return;}}spinning=false;
const arc=2*Math.PI/rem.length,norm=(((-cur)%(2*Math.PI))+2*Math.PI)%(2*Math.PI);
const idx=Math.floor(norm/arc)%rem.length,w=rem[idx],ti=Math.floor(spinIdx/2);
if(spinIdx%2===0)document.getElementById('result').textContent='🏓 '+w+' → '+teams[ti];
else document.getElementById('result').textContent='🤝 Pair: prev + '+w+' = '+teams[ti];
spinIdx++;rem=rem.filter(n=>n!==w);
document.getElementById('prog').textContent=rem.length>0?rem.length+' left':'✅ All 7 teams formed!';
setTimeout(()=>{{draw(cur);if(rem.length>0)spin();}},1100);}}requestAnimationFrame(anim);}}
cv.addEventListener('click',spin);draw(0);
</script></body></html>"""

# ─── PAGES ────────────────────────────────────────────────────────────────────

def page_signup(state, counts):
    if state["signups_frozen"]:
        st.error("🔒 Signups closed. Please log in."); return
    available=[r for r in ("admin","referee","player") if counts[r]<LIMITS[r]]
    if not available:
        update_state(signups_frozen=True); st.error("All slots filled!"); return
    st.markdown('<div class="stitle">📝 Create Account</div>',unsafe_allow_html=True)
    c1,c2,c3=st.columns(3)
    c1.metric("Players",f"{counts['player']}/14"); c2.metric("Referees",f"{counts['referee']}/2"); c3.metric("Admin",f"{counts['admin']}/1")
    st.markdown("---")
    with st.form("signup",clear_on_submit=True):
        name=st.text_input("Full Name")
        mobile=st.text_input("Mobile (10 digits)",max_chars=10)
        password=st.text_input("Password",type="password",placeholder="Min 6 chars")
        confirm=st.text_input("Confirm Password",type="password")
        role=st.selectbox("Register As",available,format_func=lambda x:{"player":"🏓 Player","referee":"🎯 Referee","admin":"⚙️ Admin"}[x])
        sub=st.form_submit_button("Register",type="primary",use_container_width=True)
    if sub:
        errs=[]
        if not name.strip(): errs.append("Name required.")
        if not mobile.isdigit() or len(mobile)!=10: errs.append("Valid 10-digit mobile required.")
        if len(password)<6: errs.append("Password min 6 characters.")
        if password!=confirm: errs.append("Passwords don't match.")
        if errs:
            for e in errs: st.error(e)
        else:
            user,err=signup_user(name.strip(),mobile.strip(),password,role)
            if err:
                st.error("Mobile already registered." if "unique" in err.lower() or "duplicate" in err.lower() else f"Error: {err}")
            else:
                st.success(f"✅ Registered as **{role}**! Switch to Login tab.")
                nc=count_by_role()
                if nc["player"]>=14 and nc["referee"]>=2 and nc["admin"]>=1:
                    update_state(signups_frozen=True); auto_assign_referees()
                st.rerun()

def page_login():
    st.markdown('<div class="stitle">🔐 Login</div>',unsafe_allow_html=True)
    with st.form("login"):
        mobile=st.text_input("Mobile Number")
        password=st.text_input("Password",type="password")
        sub=st.form_submit_button("Login",type="primary",use_container_width=True)
    if sub:
        if not mobile or not password: st.error("Fill in both fields.")
        else:
            user,err=login_user(mobile.strip(),password)
            if err: st.error(err)
            else: st.session_state.user=user; st.rerun()

# ── ADMIN ─────────────────────────────────────────────────────────────────────
def page_admin(state):
    tabs=st.tabs(["🔴 Live","👥 Participants","🎡 Teams","📅 Schedule","🏆 Standings","🥊 Knockout","🚨 Disputes","🏅 Awards","📜 History"])

    with tabs[0]:
        st.markdown('<div class="stitle">🔴 Live Scores</div>',unsafe_allow_html=True)
        render_live_scores_widget(auto_refresh=True)

    with tabs[1]:
        st.markdown('<div class="stitle">👥 Participants</div>',unsafe_allow_html=True)
        users=get_all_users()
        players=[u for u in users if u["role"]=="player"]
        refs=[u for u in users if u["role"]=="referee"]
        admins=[u for u in users if u["role"]=="admin"]
        c1,c2,c3=st.columns(3)
        with c1:
            st.markdown(f"**🏓 Players ({len(players)}/14)**")
            for p in players: st.markdown(f'<div class="uchip"><div class="uchip-name">{p["name"]}</div></div>',unsafe_allow_html=True)
        with c2:
            st.markdown(f"**🎯 Referees ({len(refs)}/2)**")
            for r in refs: st.markdown(f'<div class="uchip"><div class="uchip-name">{r["name"]}</div></div>',unsafe_allow_html=True)
            courts=get_courts()
            for court in courts:
                ri=court.get("ref") or {}; rn=ri.get("name","Unassigned") if isinstance(ri,dict) else "Unassigned"
                st.caption(f"🏟️ {court['name']} → **{rn}**")
        with c3:
            st.markdown(f"**⚙️ Admin ({len(admins)}/1)**")
            for a in admins: st.markdown(f'<div class="uchip"><div class="uchip-name">{a["name"]}</div></div>',unsafe_allow_html=True)
        needed=[]
        if len(players)<14: needed.append(f"{14-len(players)} more player(s)")
        if len(refs)<2: needed.append(f"{2-len(refs)} more referee(s)")
        if needed: st.warning(f"Waiting for: {', '.join(needed)}")
        else: st.success("✅ All 17 registered!")

    with tabs[2]:
        st.markdown('<div class="stitle">🎡 Team Assignment</div>',unsafe_allow_html=True)
        teams=get_teams()
        if state["teams_assigned"] and teams:
            st.success("✅ Teams assigned."); show_teams_grid(teams)
        else:
            users=get_all_users(); players=[u for u in users if u["role"]=="player"]
            if len(players)<14: st.warning(f"Need 14 players. Currently {len(players)}.")
            else:
                st.info("🎡 Spin assigns all 14 players to 7 teams with actual team names.")
                components.html(spin_wheel_html([p["name"] for p in players]),height=520)
                st.markdown("---")
                if "pending_teams" not in st.session_state:
                    shuffled=random.sample(players,len(players))
                    st.session_state.pending_teams=[
                        {"name":TEAM_NAMES[i],"player1_id":shuffled[i*2]["id"],"player2_id":shuffled[i*2+1]["id"],
                         "p1n":shuffled[i*2]["name"],"p2n":shuffled[i*2+1]["name"]}
                        for i in range(7)]
                st.markdown("**Teams preview:**")
                gcols=st.columns(4)
                for idx,t in enumerate(st.session_state.pending_teams):
                    with gcols[idx%4]: st.markdown(f'**{t["name"]}**<br><small>{t["p1n"]} & {t["p2n"]}</small>',unsafe_allow_html=True)
                ca,cb=st.columns([2,1])
                with ca:
                    if st.button("✅ Confirm & Save Teams",type="primary",use_container_width=True):
                        create_teams([{"name":t["name"],"player1_id":t["player1_id"],"player2_id":t["player2_id"]} for t in st.session_state.pending_teams])
                        update_state(teams_assigned=True); del st.session_state.pending_teams; st.rerun()
                with cb:
                    if st.button("🔀 Re-randomise",use_container_width=True):
                        if "pending_teams" in st.session_state: del st.session_state.pending_teams
                        st.rerun()

    with tabs[3]:
        st.markdown('<div class="stitle">📅 Schedule</div>',unsafe_allow_html=True)
        if not state["teams_assigned"]: st.warning("Assign teams first.")
        else:
            existing=get_matches("group")
            if not existing:
                courts=get_courts()
                if not all(c.get("referee_id") for c in courts):
                    st.info("Auto-assigning referees…"); auto_assign_referees(); st.rerun()
                st.info("21 matches fixed schedule across Court 2 and Court 3.")
                if st.button("Generate Match Schedule",type="primary"):
                    courts=get_courts(); court_map={c["name"]:c for c in courts}
                    teams_db=get_teams_simple(); team_map={t["name"]:t["id"] for t in teams_db}
                    # Map letter to full name
                    letter_to_name={l:TEAM_NAMES[i] for i,l in enumerate(TEAM_LETTERS)}
                    matches=[]
                    for i,(ta,tb,court_name) in enumerate(FIXED_SCHEDULE):
                        tna=letter_to_name[ta]; tnb=letter_to_name[tb]
                        if tna not in team_map or tnb not in team_map:
                            st.error(f"Team {tna} or {tnb} not found in DB. Check team names."); break
                        matches.append({"match_number":i+1,"stage":"group",
                            "team1_id":team_map[tna],"team2_id":team_map[tnb],
                            "court_id":court_map[court_name]["id"],
                            "referee_id":court_map[court_name].get("referee_id"),
                            "status":"pending","match_order":i+1})
                    if len(matches)==21:
                        create_matches(matches); update_state(phase="group_stage",schedule_generated=True)
                        st.success("✅ 21 matches generated!"); st.rerun()
            else:
                done=sum(1 for m in existing if m["status"]=="completed")
                live=sum(1 for m in existing if m["status"]=="live")
                c1,c2,c3=st.columns(3)
                c1.metric("Total",21); c2.metric("Done",done); c3.metric("Live",live)
                st.markdown("---"); render_schedule_by_court(existing)
                if done==21 and not state["group_stage_complete"]:
                    update_state(group_stage_complete=True); st.success("🎉 Group stage complete!")

    with tabs[4]:
        st.markdown('<div class="stitle">🏆 Standings</div>',unsafe_allow_html=True)
        rows=get_leaderboard()
        if not rows: st.info("No data yet.")
        else: render_leaderboard(rows)

    with tabs[5]:
        st.markdown('<div class="stitle">🥊 Knockout</div>',unsafe_allow_html=True)
        if not state["group_stage_complete"]:
            all_g=get_matches("group"); done=sum(1 for m in all_g if m["status"]=="completed")
            st.warning(f"Group stage not complete. ({done}/21 done)")
        else:
            sf=get_matches("semifinal"); tp=get_matches("third_place"); fn=get_matches("final")
            if not sf:
                top4,_=get_top4(); seeds=["1st 🥇","2nd 🥈","3rd 🥉","4th"]
                col1,col2=st.columns(2)
                for col,idxs,title in [(col1,[0,3],"Semifinal 1 — Court 2"),(col2,[1,2],"Semifinal 2 — Court 3")]:
                    with col:
                        rows_html=""
                        for idx in idxs:
                            t=top4[idx]; diff=t["score_diff"]; ds=("+" if diff>0 else "")+str(diff)
                            rows_html+=f'<div class="bracket-team"><span><span class="bracket-seed">{seeds[idx]}</span>{t["team_name"]}</span><span style="font-size:12px;color:#64748b">W:{t["won"]} Diff:{ds}</span></div>'
                        st.markdown(f'<div class="bracket-match"><div class="bracket-hdr">{title}</div>{rows_html}</div>',unsafe_allow_html=True)
                st.markdown("<br>",unsafe_allow_html=True)
                if st.button("🥊 Create Semis",type="primary"): create_semis(top4); update_state(phase="semifinals"); st.rerun()
            else:
                render_bracket(sf,"Semifinals")
                sf_done=all(m["status"]=="completed" for m in sf)
                if sf_done and not tp and not fn:
                    if st.button("🏆 Create Final & 3rd Place",type="primary"):
                        create_finals(sf); update_state(semifinals_complete=True,phase="final"); st.rerun()
                if tp: st.markdown("<br>",unsafe_allow_html=True); render_bracket(tp,"3rd Place 🥉")
                if fn:
                    st.markdown("<br>",unsafe_allow_html=True); render_bracket(fn,"Grand Final 🏆")
                    if all(m["status"]=="completed" for m in fn):
                        w=(fn[0].get("winner") or {}).get("name","")
                        if w:
                            st.balloons()
                            st.markdown(f'<div class="match-complete"><div class="mc-label">🏆 Tournament Champion 🏆</div><div class="mc-winner">{w}</div><div style="font-size:36px;margin-top:10px">🏓🎉🏆</div></div>',unsafe_allow_html=True)
                            update_state(phase="completed")

    with tabs[6]:
        st.markdown('<div class="stitle">🚨 Disputes</div>',unsafe_allow_html=True)
        # Open disputes first
        disputes=get_open_disputes()
        if not disputes: st.success("✅ No open disputes.")
        else:
            st.markdown("**⚠️ Open Disputes — Action Required**")
            for d in disputes:
                match=d.get("match") or {}; referee=d.get("referee") or {}
                t1n=(match.get("team1") or {}).get("name","?"); t2n=(match.get("team2") or {}).get("name","?")
                st.markdown(
                    f'<div class="dispute-box"><div style="font-weight:700;color:#b45309">⚠️ Match {match.get("match_number","?")}: {t1n} vs {t2n}</div>'
                    f'<div style="font-size:13px;color:#92400e">By: <strong>{referee.get("name","?")}</strong> | Note: {d.get("note","")}</div>'
                    f'<div style="font-size:12px;color:#b45309">Score: {match.get("score_team1",0)}—{match.get("score_team2",0)}</div></div>',
                    unsafe_allow_html=True
                )
                c1,c2=st.columns(2)
                with c1:
                    if st.button("✅ Keep score",key=f"res_{d['id']}"): resolve_dispute(d["id"],match.get("id"),undo=False); st.rerun()
                with c2:
                    if st.button("↩️ Undo point",key=f"und_{d['id']}",type="primary"): resolve_dispute(d["id"],match.get("id"),undo=True); st.rerun()
                st.markdown("---")
        # Past disputes
        all_d=get_all_disputes()
        resolved=[d for d in all_d if d.get("status")=="resolved"]
        if resolved:
            with st.expander(f"📋 Past Disputes ({len(resolved)} resolved)"):
                for d in resolved:
                    match=d.get("match") or {}; referee=d.get("referee") or {}
                    t1n=(match.get("team1") or {}).get("name","?"); t2n=(match.get("team2") or {}).get("name","?")
                    st.markdown(
                        f'<div class="dispute-resolved-box">✅ Match {match.get("match_number","?")}: {t1n} vs {t2n} — resolved | By {referee.get("name","?")} | Note: {d.get("note","")}</div>',
                        unsafe_allow_html=True
                    )

    with tabs[7]:
        st.markdown('<div class="stitle">🏅 Awards & Nominations</div>',unsafe_allow_html=True)
        revealed=get_revealed()
        col_rev,_=st.columns([2,3])
        with col_rev:
            if not revealed:
                if st.button("🎉 Reveal Results to Everyone",type="primary"): set_revealed(True); st.rerun()
            else:
                st.success("✅ Results are public!")
                if st.button("🔒 Hide Results"): set_revealed(False); st.rerun()
        st.markdown("---")
        results=get_vote_results(); teams=get_teams()
        for cid,r in results.items():
            cat=r["cat"]; counts=r["counts"]; winner=r["winner"]
            total_votes=sum(counts.values())
            st.markdown(
                f'<div class="award-card">'
                f'<div style="font-size:18px;font-weight:800;color:#0f172a">{cat["emoji"]} {cat["name"]}</div>'
                f'<div style="font-size:12px;color:#64748b;margin-bottom:8px">{cat.get("description","")}</div>'
                f'<div style="font-size:12px;color:#64748b">{total_votes} vote(s)</div>',
                unsafe_allow_html=True
            )
            if counts:
                for tn,cnt in sorted(counts.items(),key=lambda x:-x[1]):
                    pct=int(cnt/total_votes*100) if total_votes else 0
                    bar_w=max(pct,2)
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0">'
                        f'<div style="font-size:13px;font-weight:600;width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{tn}</div>'
                        f'<div style="flex:1;background:#f1f5f9;border-radius:4px;height:8px">'
                        f'<div style="width:{bar_w}%;background:#2563eb;border-radius:4px;height:8px"></div></div>'
                        f'<div style="font-size:12px;color:#64748b;width:36px">{cnt}</div></div>',
                        unsafe_allow_html=True
                    )
            if revealed and winner:
                st.markdown(f'<div class="award-winner-box"><div style="font-size:11px;font-weight:700;color:#92400e;letter-spacing:2px;text-transform:uppercase;margin-bottom:4px">🏅 WINNER</div><div class="award-winner-name">🏆 {winner}</div></div>',unsafe_allow_html=True)
            st.markdown("</div>",unsafe_allow_html=True)

    with tabs[8]:
        st.markdown('<div class="stitle">📜 Match History</div>',unsafe_allow_html=True)
        history=get_match_history()
        if not history: st.info("No completed matches yet.")
        else:
            st.markdown(f"**{len(history)} matches completed**")
            for m in history:
                t1=m.get("team1") or {}; t2=m.get("team2") or {}
                winner=m.get("winner") or {}; court=m.get("court") or {}
                s1=m.get("score_team1",0); s2=m.get("score_team2",0)
                t1n=t1.get("name","?"); t2n=t2.get("name","?")
                wn=winner.get("name","?"); cn=court.get("name","?")
                stage_map={"group":"Group","semifinal":"Semi","third_place":"3rd Place","final":"Final"}
                st.markdown(
                    f'<div class="history-card">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center">'
                    f'<div><div style="font-size:15px;font-weight:700">{t1n} <span style="color:#cbd5e1">vs</span> {t2n}</div>'
                    f'<div style="font-size:12px;color:#64748b">{stage_map.get(m.get("stage",""),"?")} · {cn} · Match {m["match_number"]}</div></div>'
                    f'<div style="text-align:right"><div style="font-family:Inter,sans-serif;font-size:22px;font-weight:900">{s1}—{s2}</div>'
                    f'<div style="font-size:12px;color:#15803d;font-weight:700">🏆 {wn}</div></div></div>',
                    unsafe_allow_html=True
                )
                moments=get_moments(m["id"])
                if moments:
                    mom_html="".join([
                        f'<span class="moment-chip m-{"good" if mm["moment_type"]=="good_shot" else "rally" if mm["moment_type"]=="great_rally" else "comeback"}">'
                        f'{"🎯" if mm["moment_type"]=="good_shot" else "🔥" if mm["moment_type"]=="great_rally" else "⚡"} '
                        f'{(mm.get("team") or {}).get("name","")} @{mm.get("score_at_time","")}</span>'
                        for mm in moments
                    ])
                    st.markdown(f'<div style="margin-top:6px">{mom_html}</div></div>',unsafe_allow_html=True)
                else:
                    st.markdown("</div>",unsafe_allow_html=True)

# ── REFEREE ───────────────────────────────────────────────────────────────────
def page_referee(user):
    st.markdown(f'<div class="stitle">🎯 Referee — {user["name"]}</div>',unsafe_allow_html=True)
    court=get_referee_court(user["id"])
    if court is None: st.warning("Not assigned to a court yet."); return

    st.markdown(
        f'<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:10px 18px;margin-bottom:16px;display:inline-block;">'
        f'<span style="font-size:11px;font-weight:700;color:#2563eb;letter-spacing:1.5px;text-transform:uppercase">Your Court</span><br>'
        f'<span style="font-size:20px;font-weight:900;color:#0f172a">🏟️ {court["name"]}</span></div>',
        unsafe_allow_html=True
    )

    # All court matches — history
    all_court_m=get_court_matches(court["id"])
    if all_court_m:
        with st.expander(f"📋 All {len(all_court_m)} matches on {court['name']}",expanded=False):
            for cm in all_court_m: render_match_row(cm)

    match=get_referee_active_match(court["id"])
    if match is None: st.success(f"✅ All matches on {court['name']} complete!"); return

    t1=match.get("team1") or {}; t2=match.get("team2") or {}
    status=match.get("status","pending")
    s1=match.get("score_team1",0); s2=match.get("score_team2",0)
    history=match.get("score_history") or []
    if isinstance(history,str): history=json.loads(history) if history else []

    # Check for open dispute — freeze scoring if yes
    open_dispute=get_referee_open_dispute(court["id"])

    stage_map={"group":"Group Stage","semifinal":"Semifinal","third_place":"3rd Place","final":"Grand Final"}
    st.markdown(
        f'<div style="text-align:center;margin-bottom:14px"><span style="font-size:12px;font-weight:600;color:#64748b;letter-spacing:1px">'
        f'MATCH {match["match_number"]} · {stage_map.get(match.get("stage",""),"")}&nbsp;·&nbsp;{court["name"]}</span></div>',
        unsafe_allow_html=True
    )

    # Score boxes
    sc1,scv,sc2=st.columns([5,2,5])
    with sc1:
        st.markdown(f'<div class="sbox"><div class="sbox-name">{t1.get("name","Team 1")}</div><div class="sbox-num score-red">{s1}</div></div>',unsafe_allow_html=True)
    with scv:
        label="FINAL" if status=="completed" else ("LIVE" if status=="live" else "READY")
        color="#ef4444" if status=="live" else "#94a3b8"
        st.markdown(f'<div style="text-align:center;padding:28px 0"><div style="font-size:14px;font-weight:900;color:{color}">{label}</div><div style="font-size:10px;font-weight:700;color:#e2e8f0;margin-top:4px;letter-spacing:1px">FIRST TO 15</div></div>',unsafe_allow_html=True)
    with sc2:
        st.markdown(f'<div class="sbox"><div class="sbox-name">{t2.get("name","Team 2")}</div><div class="sbox-num score-blue">{s2}</div></div>',unsafe_allow_html=True)

    st.markdown("<br>",unsafe_allow_html=True)

    if status=="completed":
        w=match.get("winner") or {}
        st.markdown(f'<div class="match-complete"><div class="mc-label">Match Complete</div><div class="mc-winner">🏆 {w.get("name","?")} Wins!</div><div class="mc-score">{s1} — {s2}</div></div>',unsafe_allow_html=True)
        st.balloons()
        if match.get("stage")=="group" and check_group_done(): update_state(group_stage_complete=True)
        moments=get_moments(match["id"])
        if moments:
            st.markdown("**🎯 Match Highlights:**")
            icons_map={"good_shot":"🎯","great_rally":"🔥","crazy_comeback":"⚡"}
            css_map={"good_shot":"m-good","great_rally":"m-rally","crazy_comeback":"m-comeback"}
            label_map={"good_shot":"Good Shot","great_rally":"Great Rally","crazy_comeback":"Crazy Comeback"}
            for mom in moments:
                mtype=mom["moment_type"]; tn=(mom.get("team") or {}).get("name","")
                st.markdown(f'<span class="moment-chip {css_map.get(mtype,"m-good")}">{icons_map.get(mtype,"🏓")} {label_map.get(mtype,mtype)}{" — "+tn if tn else ""}</span> @{mom.get("score_at_time","")}',unsafe_allow_html=True)
        if st.button("➡️ Next Match",type="primary",use_container_width=True): st.rerun()
        return

    if status=="pending":
        if open_dispute:
            st.markdown(f'<div class="frozen-banner"><div class="frozen-title">🚨 Dispute Pending</div><div>Admin must resolve the dispute before this match can start.</div></div>',unsafe_allow_html=True)
        else:
            if st.button("▶️ Start Match",type="primary",use_container_width=True):
                start_match(match["id"]); st.rerun()
        return

    # LIVE
    st.markdown('<div style="text-align:center;padding:7px;background:#fee2e2;border:1px solid #fecaca;border-radius:8px;margin-bottom:14px"><span style="color:#dc2626;font-weight:700;font-size:12px;letter-spacing:2px">● LIVE MATCH</span></div>',unsafe_allow_html=True)

    # FROZEN check — if open dispute, freeze scoring
    if open_dispute:
        st.markdown(
            f'<div class="frozen-banner">'
            f'<div class="frozen-title">🚫 Scoring Frozen</div>'
            f'<div style="font-size:14px;color:#7f1d1d;margin-top:4px">A dispute has been flagged. Scoring is paused until admin resolves it.</div>'
            f'<div style="font-size:13px;color:#b45309;margin-top:6px;font-style:italic">Note: "{open_dispute.get("note","")}"</div>'
            f'</div>',
            unsafe_allow_html=True
        )
        # Still show dispute status, no score buttons
        with st.expander("⚠️ Dispute Status"):
            st.warning("Waiting for admin to review and resolve this dispute.")
        return

    undo_key=f"undone_{match['id']}"
    already_undone=st.session_state.get(undo_key,False)
    b1,bundo,b2=st.columns([4,2,4])
    with b1:
        if st.button(f"➕ +1 → {t1.get('name','T1')}",type="primary",use_container_width=True,key="pt1"):
            st.session_state[undo_key]=False
            won,_,ns1,ns2=add_score(match["id"],"score_team1",s1,s2,t1.get("id"),t2.get("id"),history)
            if won: st.balloons()
            st.rerun()
    with bundo:
        if st.button("↩️ Undo",use_container_width=True,key="undo_pt",disabled=len(history)==0 or already_undone):
            undo_score(match["id"],history); st.session_state[undo_key]=True; st.rerun()
    with b2:
        if st.button(f"➕ +1 → {t2.get('name','T2')}",type="secondary",use_container_width=True,key="pt2"):
            st.session_state[undo_key]=False
            won,_,ns1,ns2=add_score(match["id"],"score_team2",s1,s2,t1.get("id"),t2.get("id"),history)
            if won: st.balloons()
            st.rerun()
    if already_undone: st.caption("↩️ Undo used — score a point to re-enable")

    st.markdown("<br>",unsafe_allow_html=True)
    pc1,pc2=st.columns(2)
    with pc1: st.markdown(f"**{t1.get('name')}** — {s1}/15"); st.progress(min(s1/15,1.0))
    with pc2: st.markdown(f"**{t2.get('name')}** — {s2}/15"); st.progress(min(s2/15,1.0))

    st.markdown("---")
    st.markdown("**🎯 Tag a Moment**")
    score_str=f"{s1}—{s2}"
    t1n=t1.get("name","T1"); t2n=t2.get("name","T2")
    mg1,mg2,mg3,mg4=st.columns(4)
    with mg1:
        if st.button(f"🎯 Shot: {t1n}",use_container_width=True,key="gs1"): add_moment(match["id"],"good_shot",t1.get("id"),score_str); st.rerun()
    with mg2:
        if st.button(f"🎯 Shot: {t2n}",use_container_width=True,key="gs2"): add_moment(match["id"],"good_shot",t2.get("id"),score_str); st.rerun()
    with mg3:
        if st.button("🔥 Great Rally",use_container_width=True,key="gr"): add_moment(match["id"],"great_rally",None,score_str); st.rerun()
    with mg4:
        if st.button("⚡ Comeback",use_container_width=True,key="cc"): add_moment(match["id"],"crazy_comeback",None,score_str); st.rerun()

    st.markdown("---")

    # Show current dispute status if any
    cur_dispute=get_referee_open_dispute(court["id"])
    if cur_dispute:
        st.markdown(f'<div class="dispute-box">⚠️ <strong>Active dispute flagged</strong> — awaiting admin resolution<br><small>Note: {cur_dispute.get("note","")}</small></div>',unsafe_allow_html=True)
    else:
        with st.expander("⚠️ Flag a Dispute"):
            note=st.text_input("Describe dispute",key="dispute_note",placeholder="e.g. ball landed out")
            if st.button("🚩 Flag to Admin",type="secondary"):
                if note.strip(): flag_dispute(match["id"],user["id"],note.strip()); st.warning("⚠️ Flagged!"); st.rerun()
                else: st.error("Enter a note first.")

# ── PLAYER ────────────────────────────────────────────────────────────────────
def page_player(user):
    st.markdown(f'<div class="stitle">🏓 Welcome, {user["name"]}</div>',unsafe_allow_html=True)
    teams=get_teams(); my_team=None
    for t in teams:
        p1=t.get("p1") or {}; p2=t.get("p2") or {}
        if user["id"] in (p1.get("id"),p2.get("id")): my_team=t; break

    if my_team:
        idx=next((i for i,n in enumerate(TEAM_NAMES) if n==my_team["name"]),0)
        color=TEAM_COLORS[idx%len(TEAM_COLORS)]
        p1n=(my_team.get("p1") or {}).get("name","?"); p2n=(my_team.get("p2") or {}).get("name","?")
        st.markdown(
            f'<div style="background:{color}14;border:1px solid {color}40;border-left:4px solid {color};border-radius:10px;padding:12px 16px;margin-bottom:16px;display:flex;align-items:center;gap:14px">'
            f'<div style="font-size:26px">🏓</div>'
            f'<div><div style="font-size:15px;font-weight:900;color:#0f172a">{my_team["name"]}</div>'
            f'<div style="font-size:12px;color:#64748b">{p1n} &amp; {p2n}</div></div></div>',
            unsafe_allow_html=True
        )

    tabs=st.tabs(["🔴 Live","📅 Schedule","📅 My Matches","🏆 Standings","🏅 Awards","📜 History"])

    with tabs[0]:
        st.markdown('<div class="stitle">🔴 Live Scores & Highlights</div>',unsafe_allow_html=True)
        render_live_scores_widget(auto_refresh=True)

    with tabs[1]:
        st.markdown('<div class="stitle">📅 Full Schedule</div>',unsafe_allow_html=True)
        all_m=get_matches()
        if not all_m: st.info("Schedule not generated yet.")
        else:
            done=sum(1 for m in all_m if m["status"]=="completed"); live=sum(1 for m in all_m if m["status"]=="live")
            c1,c2,c3=st.columns(3); c1.metric("Total",len(all_m)); c2.metric("Done",done); c3.metric("Live",live)
            st.markdown("---"); render_schedule_by_court(all_m)

    with tabs[2]:
        st.markdown('<div class="stitle">📅 My Matches</div>',unsafe_allow_html=True)
        if not my_team: st.info("Teams not assigned yet.")
        else:
            all_m=get_matches()
            my_m=sorted([m for m in all_m if (m.get("team1") or {}).get("id")==my_team["id"] or (m.get("team2") or {}).get("id")==my_team["id"]],key=lambda x:x["match_order"])
            if not my_m: st.info("Schedule not generated yet.")
            else:
                for m in my_m: render_match_row(m)
                won=sum(1 for m in my_m if (m.get("winner") or {}).get("id")==my_team["id"] and m["status"]=="completed")
                played=sum(1 for m in my_m if m["status"]=="completed")
                st.markdown(f"<br>**{won}W / {played-won}L** from {played} played · {len(my_m)-played} remaining",unsafe_allow_html=True)

    with tabs[3]:
        st.markdown('<div class="stitle">🏆 Standings</div>',unsafe_allow_html=True)
        rows=get_leaderboard()
        if not rows: st.info("No data yet.")
        else: render_leaderboard(rows,my_team["name"] if my_team else None)

    with tabs[4]:
        st.markdown('<div class="stitle">🏅 Awards & Voting</div>',unsafe_allow_html=True)
        revealed=get_revealed()
        if revealed:
            st.success("🎉 Results are out!")
            results=get_vote_results()
            for cid,r in results.items():
                cat=r["cat"]; winner=r["winner"]; counts=r["counts"]
                st.markdown(
                    f'<div class="award-card">'
                    f'<div style="font-size:17px;font-weight:800">{cat["emoji"]} {cat["name"]}</div>'
                    f'<div style="font-size:12px;color:#64748b;margin-bottom:8px">{cat.get("description","")}</div>',
                    unsafe_allow_html=True
                )
                if winner:
                    st.markdown(f'<div class="award-winner-box"><div style="font-size:11px;font-weight:700;color:#92400e;letter-spacing:2px;text-transform:uppercase">🏅 WINNER</div><div class="award-winner-name">🏆 {winner}</div></div>',unsafe_allow_html=True)
                st.markdown("</div>",unsafe_allow_html=True)
        else:
            cats=get_award_categories()
            if not cats: st.info("No award categories yet.")
            else:
                teams=get_teams()
                if not teams: st.info("Teams not assigned yet.")
                else:
                    my_votes=get_my_votes(user["id"])
                    locked=all(cat["id"] in my_votes for cat in cats)
                    if locked: st.success("✅ You've submitted all your votes! Results will be revealed by admin.")
                    else: st.info("🗳️ Cast your votes below. **One vote per category. No self-voting.**")
                    for cat in cats:
                        st.markdown(
                            f'<div class="award-card">'
                            f'<div style="font-size:17px;font-weight:800">{cat["emoji"]} {cat["name"]}</div>'
                            f'<div style="font-size:12px;color:#64748b;margin-bottom:10px">{cat.get("description","")}</div>',
                            unsafe_allow_html=True
                        )
                        if cat["id"] in my_votes:
                            voted_tid=my_votes[cat["id"]]
                            voted_name=next((t["name"] for t in teams if t["id"]==voted_tid),"?")
                            st.success(f"✅ Voted: **{voted_name}**")
                        else:
                            # Filter out my own team (no self-voting)
                            eligible=[t for t in teams if not my_team or t["id"]!=my_team["id"]]
                            vote_key=f"vote_{cat['id']}"
                            choice=st.selectbox(
                                f"Vote for best {cat['name']}",
                                options=[""]+[t["name"] for t in eligible],
                                key=vote_key,
                                label_visibility="collapsed"
                            )
                            if choice and st.button(f"Submit vote",key=f"submit_{cat['id']}",type="primary"):
                                tid=next((t["id"] for t in eligible if t["name"]==choice),None)
                                if tid:
                                    ok=cast_vote(user["id"],cat["id"],tid)
                                    if ok: st.success("✅ Vote cast!"); st.rerun()
                                    else: st.error("Already voted or error.")
                        st.markdown("</div>",unsafe_allow_html=True)

    with tabs[5]:
        st.markdown('<div class="stitle">📜 Match History</div>',unsafe_allow_html=True)
        history=get_match_history()
        if not history: st.info("No completed matches yet.")
        else:
            for m in history:
                t1=m.get("team1") or {}; t2=m.get("team2") or {}
                winner=m.get("winner") or {}; court=m.get("court") or {}
                s1=m.get("score_team1",0); s2=m.get("score_team2",0)
                t1n=t1.get("name","?"); t2n=t2.get("name","?"); wn=winner.get("name","?")
                stage_map={"group":"Group","semifinal":"Semi","third_place":"3rd","final":"Final"}
                st.markdown(
                    f'<div class="history-card">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center">'
                    f'<div><div style="font-size:15px;font-weight:700">{t1n} <span style="color:#cbd5e1">vs</span> {t2n}</div>'
                    f'<div style="font-size:11px;color:#64748b">{stage_map.get(m.get("stage",""),"?")} · {court.get("name","?")} · Match {m["match_number"]}</div></div>'
                    f'<div style="text-align:right"><div style="font-family:Inter;font-size:22px;font-weight:900">{s1}—{s2}</div>'
                    f'<div style="font-size:12px;color:#15803d;font-weight:700">🏆 {wn}</div></div></div>',
                    unsafe_allow_html=True
                )
                moments=get_moments(m["id"])
                if moments:
                    icons_map={"good_shot":"🎯","great_rally":"🔥","crazy_comeback":"⚡"}
                    css_map={"good_shot":"m-good","great_rally":"m-rally","crazy_comeback":"m-comeback"}
                    mom_html="".join([
                        f'<span class="moment-chip {css_map.get(mm["moment_type"],"m-good")}">{icons_map.get(mm["moment_type"],"🏓")} {(mm.get("team") or {}).get("name","")} @{mm.get("score_at_time","")}</span>'
                        for mm in moments])
                    st.markdown(f'<div style="margin-top:6px">{mom_html}</div>',unsafe_allow_html=True)
                st.markdown("</div>",unsafe_allow_html=True)

# ─── Init ─────────────────────────────────────────────────────────────────────
if "user" not in st.session_state: st.session_state.user=None

try:
    _state=get_state(); _counts=count_by_role()
    _phase=_state["phase"].replace("_"," ").title()
except Exception as _e:
    st.error(f"⚠️ Cannot connect to database. Error: {_e}"); st.stop()

with st.sidebar:
    st.markdown("### 🏓 Serve & Smash")
    st.markdown(
        f'<div class="sb-stat"><span class="sb-lbl">Players</span><span class="sb-val">{_counts["player"]}/14</span></div>'
        f'<div class="sb-stat"><span class="sb-lbl">Referees</span><span class="sb-val">{_counts["referee"]}/2</span></div>'
        f'<div class="sb-stat"><span class="sb-lbl">Admin</span><span class="sb-val">{_counts["admin"]}/1</span></div>'
        f'<div class="sb-stat"><span class="sb-lbl">Phase</span><span class="sb-val">{_phase}</span></div>',
        unsafe_allow_html=True
    )
    st.markdown("---")
    if st.session_state.user:
        u=st.session_state.user
        icons={"player":"🏓","referee":"🎯","admin":"⚙️"}
        st.success(f'{icons.get(u["role"],"👤")} **{u["name"]}** ({u["role"].title()})')
        if st.button("Logout",use_container_width=True): st.session_state.user=None; st.rerun()
    else: st.info("Sign up or log in below.")

st.markdown(
    f'<div class="hero"><div class="hero-icon">🏓</div><div>'
    f'<div class="hero-title">Serve &amp; Smash</div>'
    f'<div class="hero-sub">Pickleball Tournament Management System</div>'
    f'<div class="phase-pill">{_phase}</div>'
    f'</div></div>',unsafe_allow_html=True
)

user=st.session_state.user
if user is None:
    ta,tb=st.tabs(["📝 Sign Up","🔐 Login"])
    with ta: page_signup(_state,_counts)
    with tb: page_login()
else:
    role=user["role"]
    if role=="admin": page_admin(_state)
    elif role=="referee": page_referee(user)
    elif role=="player": page_player(user)
