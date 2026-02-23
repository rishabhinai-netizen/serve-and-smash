import hashlib
import random
import time
import json
from itertools import combinations
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Serve & Smash | Pickleball Tournament",
    page_icon="🏓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }
.stApp { background: #f0f4f8; }
.block-container { padding-top: 0.5rem; max-width: 1100px; }
section[data-testid="stSidebar"] { background: #fff; border-right: 1px solid #e2e8f0; }
header[data-testid="stHeader"] { background: transparent; }
div[data-testid="stDecoration"] { display: none; }

/* Hero */
.hero {
    background: linear-gradient(135deg, #0f172a 0%, #1e40af 60%, #0ea5e9 100%);
    border-radius: 16px; padding: 32px 36px; margin-bottom: 24px; color: #fff;
    display: flex; align-items: center; gap: 20px;
    box-shadow: 0 8px 32px rgba(30,64,175,0.3);
}
.hero-icon { font-size: 54px; line-height:1; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3)); }
.hero-title { font-family:'Inter',sans-serif; font-size:30px; font-weight:900; letter-spacing:-0.5px; margin:0; }
.hero-sub { font-size:13px; color:rgba(255,255,255,0.7); margin-top:3px; letter-spacing:.5px; }
.phase-pill {
    display:inline-block; background:rgba(255,255,255,0.15); color:#fff;
    font-size:10px; font-weight:700; letter-spacing:2px; text-transform:uppercase;
    padding:3px 12px; border-radius:20px; margin-top:8px; border:1px solid rgba(255,255,255,0.25);
}

/* Section title */
.stitle { font-family:'Inter',sans-serif; font-size:17px; font-weight:800; color:#0f172a; margin-bottom:14px; display:flex; align-items:center; gap:8px; }

/* Cards */
.card { background:#fff; border:1px solid #e2e8f0; border-radius:12px; padding:22px; margin-bottom:14px; box-shadow:0 1px 4px rgba(0,0,0,0.05); }

/* Match row */
.mrow {
    background:#fff; border:1px solid #e2e8f0; border-radius:10px;
    padding:12px 16px; margin-bottom:6px; display:flex; align-items:center; gap:10px;
    transition: box-shadow .15s; font-size:14px;
}
.mrow:hover { box-shadow:0 3px 10px rgba(0,0,0,0.08); }
.mrow.live { border-left:4px solid #ef4444; background:#fff5f5; }
.mrow.completed { border-left:4px solid #22c55e; background:#f0fdf4; }
.mrow.pending { border-left:4px solid #94a3b8; }
.mrow-num { font-size:10px; font-weight:700; color:#94a3b8; letter-spacing:1px; min-width:52px; }
.mrow-teams { font-size:15px; font-weight:700; color:#0f172a; flex:1; }
.mrow-vs { color:#cbd5e1; font-size:12px; margin:0 6px; }
.mrow-score { font-family:'Inter',sans-serif; font-size:17px; font-weight:900; color:#0f172a; min-width:64px; text-align:center; }
.mrow-court { font-size:11px; font-weight:700; color:#2563eb; background:#eff6ff; padding:3px 9px; border-radius:20px; }
.badge-live { font-size:10px; font-weight:700; color:#ef4444; background:#fee2e2; padding:3px 9px; border-radius:20px; animation:blink 1.2s infinite; }
.badge-done { font-size:10px; font-weight:600; color:#15803d; background:#dcfce7; padding:3px 9px; border-radius:20px; }
.badge-pending { font-size:10px; font-weight:600; color:#64748b; background:#f1f5f9; padding:3px 9px; border-radius:20px; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.5} }

/* Court block */
.court-block { background:#fff; border:1px solid #e2e8f0; border-radius:12px; padding:18px; margin-bottom:14px; }
.court-title { font-size:13px; font-weight:800; color:#2563eb; letter-spacing:1.5px; text-transform:uppercase; margin-bottom:12px; padding-bottom:8px; border-bottom:2px solid #eff6ff; }

/* Leaderboard */
.lb-head { display:grid; grid-template-columns:36px 1fr 52px 40px 40px 64px 64px 64px; gap:4px; padding:8px 12px; background:#f8fafc; border-radius:8px 8px 0 0; font-size:10px; font-weight:700; color:#64748b; letter-spacing:1.5px; text-transform:uppercase; border:1px solid #e2e8f0; }
.lb-row { display:grid; grid-template-columns:36px 1fr 52px 40px 40px 64px 64px 64px; gap:4px; padding:11px 12px; background:#fff; border:1px solid #e2e8f0; border-top:none; font-size:13px; align-items:center; transition:background .1s; }
.lb-row:hover { background:#fafbff; }
.lb-row.qual { border-left:3px solid #f59e0b; background:#fffbeb; }
.lb-row.mine { background:#eff6ff; border-left:3px solid #2563eb; }

/* Score boxes */
.sbox { background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px; padding:20px; text-align:center; }
.sbox-name { font-size:13px; font-weight:700; color:#64748b; letter-spacing:1px; text-transform:uppercase; margin-bottom:6px; }
.sbox-num { font-family:'Inter',sans-serif; font-size:88px; font-weight:900; line-height:1; }
.score-red { color:#dc2626; }
.score-blue { color:#1d4ed8; }

/* Bracket */
.bracket-wrap { display:flex; flex-direction:column; gap:16px; margin-top:16px; }
.bracket-match {
    background:#fff; border:1px solid #e2e8f0; border-radius:12px; overflow:hidden;
    box-shadow:0 2px 8px rgba(0,0,0,0.06);
}
.bracket-header { background:linear-gradient(135deg,#1e40af,#2563eb); color:#fff; padding:8px 16px; font-size:11px; font-weight:700; letter-spacing:2px; text-transform:uppercase; }
.bracket-team { display:flex; justify-content:space-between; align-items:center; padding:12px 16px; border-bottom:1px solid #f1f5f9; font-size:15px; font-weight:700; color:#0f172a; }
.bracket-team.winner { background:#f0fdf4; color:#15803d; }
.bracket-team.loser { background:#fafafa; color:#94a3b8; }
.bracket-seed { font-size:11px; font-weight:600; color:#94a3b8; background:#f8fafc; padding:2px 8px; border-radius:20px; margin-right:8px; }
.bracket-score { font-family:'Inter',sans-serif; font-size:20px; font-weight:900; }

/* Moments */
.moment-chip { display:inline-block; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:700; margin:3px; }
.moment-good { background:#fef9c3; color:#854d0e; border:1px solid #fde68a; }
.moment-rally { background:#dbeafe; color:#1d4ed8; border:1px solid #bfdbfe; }
.moment-comeback { background:#fce7f3; color:#9d174d; border:1px solid #fbcfe8; }

/* Dispute */
.dispute-banner { background:#fff7ed; border:1px solid #fed7aa; border-radius:10px; padding:14px 18px; margin:12px 0; }

/* User chip */
.uchip { background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:10px 14px; margin-bottom:6px; }
.uchip-name { font-size:14px; font-weight:700; color:#0f172a; }
.uchip-mob { font-size:12px; color:#64748b; margin-top:1px; }

/* Slot label */
.slot-lbl { font-size:10px; font-weight:800; color:#94a3b8; letter-spacing:2.5px; text-transform:uppercase; margin:14px 0 6px; }

/* Sidebar */
.sb-stat { display:flex; justify-content:space-between; padding:7px 0; border-bottom:1px solid #f1f5f9; font-size:13px; }
.sb-lbl { color:#64748b; font-weight:500; }
.sb-val { font-weight:700; color:#0f172a; }

/* Confetti overlay */
@keyframes fadeInUp { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }
.anim-in { animation: fadeInUp .4s ease both; }
</style>
""", unsafe_allow_html=True)

# ─── DB Client ────────────────────────────────────────────────────────────────
@st.cache_resource
def get_db() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def hp(pw): return hashlib.sha256(pw.encode()).hexdigest()

# ─── DB Helpers ───────────────────────────────────────────────────────────────
def signup_user(name, mobile, password, role):
    try:
        r = get_db().table("users").insert({"name":name,"mobile":mobile,"password_hash":hp(password),"role":role}).execute()
        return r.data[0], None
    except Exception as e:
        return None, str(e)

def login_user(mobile, password):
    r = get_db().table("users").select("*").eq("mobile", mobile).execute()
    if not r.data: return None, "Mobile number not registered."
    u = r.data[0]
    if hp(password) != u["password_hash"]: return None, "Incorrect password."
    return u, None

def count_by_role():
    r = get_db().table("users").select("role").execute()
    c = {"player":0,"referee":0,"admin":0}
    for row in r.data: c[row["role"]] += 1
    return c

def get_all_users():
    return get_db().table("users").select("*").order("created_at").execute().data

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
    """Assign first referee → Court 2, second → Court 3 by signup order"""
    refs = get_db().table("users").select("id,name").eq("role","referee").order("created_at").execute().data
    courts = get_courts()
    c2 = next((c for c in courts if c["name"]=="Court 2"), None)
    c3 = next((c for c in courts if c["name"]=="Court 3"), None)
    if len(refs) >= 1 and c2:
        get_db().table("courts").update({"referee_id": refs[0]["id"]}).eq("id", c2["id"]).execute()
    if len(refs) >= 2 and c3:
        get_db().table("courts").update({"referee_id": refs[1]["id"]}).eq("id", c3["id"]).execute()

def get_matches(stage=None):
    q = get_db().table("matches").select(
        "*, team1:teams!matches_team1_id_fkey(id,name),"
        "team2:teams!matches_team2_id_fkey(id,name),"
        "court:courts(name),winner:teams!matches_winner_id_fkey(id,name)"
    ).order("match_order")
    if stage: q = q.eq("stage", stage)
    return q.execute().data

def create_matches(matches):
    get_db().table("matches").insert(matches).execute()

def start_match(mid):
    get_db().table("matches").update({"status":"live","score_history":[]}).eq("id",mid).execute()

def add_score(mid, field, s1, s2, t1id, t2id, history):
    new_s1 = s1 + (1 if field == "score_team1" else 0)
    new_s2 = s2 + (1 if field == "score_team2" else 0)
    new_hist = list(history) + [{"t1": s1, "t2": s2}]
    won = new_s1 >= 15 or new_s2 >= 15
    wid = (t1id if new_s1 >= 15 else t2id) if won else None
    # Single atomic DB write — avoids partial state on slow connections
    payload = {
        "score_team1": new_s1,
        "score_team2": new_s2,
        "score_history": json.dumps(new_hist)
    }
    if won:
        payload["winner_id"] = wid
        payload["status"] = "completed"
    get_db().table("matches").update(payload).eq("id", mid).execute()
    return won, wid

def undo_score(mid, history):
    if not history: return
    prev = history[-1]
    new_hist = history[:-1]
    get_db().table("matches").update({
        "score_team1": prev["t1"],
        "score_team2": prev["t2"],
        "score_history": json.dumps(new_hist),
        "winner_id": None,
        "status": "live"
    }).eq("id", mid).execute()

def get_live_matches():
    return get_db().table("matches").select(
        "*, team1:teams!matches_team1_id_fkey(id,name),"
        "team2:teams!matches_team2_id_fkey(id,name),court:courts(name)"
    ).eq("status","live").execute().data

def get_referee_match(ref_id):
    cr = get_db().table("courts").select("id,name").eq("referee_id",ref_id).execute()
    if not cr.data: return None, None
    court = cr.data[0]
    mr = get_db().table("matches").select(
        "*, team1:teams!matches_team1_id_fkey(id,name),"
        "team2:teams!matches_team2_id_fkey(id,name),court:courts(name)"
    ).eq("court_id",court["id"]).in_("status",["pending","live"]).order("match_order").limit(1).execute()
    return (mr.data[0] if mr.data else None), court

def get_leaderboard():
    rows = get_db().table("leaderboard").select("*").execute().data
    for r in rows: r["score_diff"] = r["score_for"] - r["score_against"]
    return rows

def check_group_done():
    r = get_db().table("matches").select("id").eq("stage","group").neq("status","completed").execute()
    return len(r.data) == 0

def get_top4():
    rows = get_leaderboard()
    rows.sort(key=lambda x:(x["won"],x["score_diff"],x["score_for"]), reverse=True)
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
    bn = mn.data[0]["match_number"]
    bo = mo.data[0]["match_order"]
    sfs = sorted(sf, key=lambda x: x["match_number"])
    def loser(m):
        t1=(m.get("team1") or {}).get("id")
        t2=(m.get("team2") or {}).get("id")
        w=m.get("winner_id") or ((m.get("winner") or {}).get("id"))
        return t1 if w==t2 else t2
    def winner(m):
        return m.get("winner_id") or ((m.get("winner") or {}).get("id"))
    get_db().table("matches").insert([
        {"match_number":bn+1,"stage":"third_place","team1_id":loser(sfs[0]),"team2_id":loser(sfs[1]),
         "court_id":c2["id"],"referee_id":c2.get("referee_id"),"status":"pending","match_order":bo+1},
        {"match_number":bn+2,"stage":"final","team1_id":winner(sfs[0]),"team2_id":winner(sfs[1]),
         "court_id":c3["id"],"referee_id":c3.get("referee_id"),"status":"pending","match_order":bo+2},
    ]).execute()

def add_moment(match_id, moment_type, team_id, score_str):
    get_db().table("match_moments").insert({
        "match_id":match_id,"moment_type":moment_type,
        "team_id":team_id,"score_at_time":score_str
    }).execute()

def get_moments(match_id):
    return get_db().table("match_moments").select("*").eq("match_id",match_id).order("created_at").execute().data

def flag_dispute(match_id, referee_id, note):
    get_db().table("match_disputes").insert({
        "match_id":match_id,"referee_id":referee_id,"note":note,"status":"open"
    }).execute()

def get_open_disputes():
    return get_db().table("match_disputes").select(
        "*, match:matches(match_number,score_team1,score_team2,"
        "team1:teams!matches_team1_id_fkey(name),"
        "team2:teams!matches_team2_id_fkey(name)),"
        "referee:users(name)"
    ).eq("status","open").execute().data

def resolve_dispute(dispute_id, match_id, undo):
    get_db().table("match_disputes").update({"status":"resolved"}).eq("id",dispute_id).execute()
    if undo:
        m = get_db().table("matches").select("score_history,score_team1,score_team2").eq("id",match_id).execute().data[0]
        hist = m.get("score_history") or []
        if isinstance(hist, str): hist = json.loads(hist)
        undo_score(match_id, hist)

# ─── Schedule ──────────────────────────────────────────────────────────────────
TEAM_LABELS = ["Team A","Team B","Team C","Team D","Team E","Team F","Team G"]
TEAM_COLORS = ["#2563eb","#dc2626","#16a34a","#9333ea","#ea580c","#0891b2","#be185d"]
LIMITS = {"player":14,"referee":2,"admin":1}

def build_schedule(team_names, court_names):
    all_pairs = list(combinations(team_names, 2))
    random.shuffle(all_pairs)
    consecutive = {t:0 for t in team_names}
    last_played = {t:-1 for t in team_names}
    schedule, remaining, slot = [], list(all_pairs), 0
    while remaining and slot < 300:
        busy, slot_m = set(), []
        for court in court_names:
            if not remaining: break
            best, best_sc = None, -1
            for pair in remaining:
                t1,t2 = pair
                if t1 in busy or t2 in busy: continue
                c1 = consecutive[t1] if last_played[t1]==slot-1 else 0
                c2 = consecutive[t2] if last_played[t2]==slot-1 else 0
                if c1>=2 or c2>=2: continue
                sc = (slot-last_played[t1])+(slot-last_played[t2])
                if sc > best_sc: best_sc,best = sc,pair
            if best:
                remaining.remove(best)
                slot_m.append({"team1":best[0],"team2":best[1],"court_name":court,"match_order":len(schedule)+len(slot_m)+1})
                busy.add(best[0]); busy.add(best[1])
        playing = {sm["team1"] for sm in slot_m}|{sm["team2"] for sm in slot_m}
        for t in team_names:
            if t in playing:
                consecutive[t]=(consecutive[t]+1) if last_played[t]==slot-1 else 1
                last_played[t]=slot
        schedule.extend(slot_m)
        slot+=1
    for pair in remaining:
        schedule.append({"team1":pair[0],"team2":pair[1],"court_name":court_names[len(schedule)%len(court_names)],"match_order":len(schedule)+1})
    return schedule

# ─── Spin Wheel HTML ──────────────────────────────────────────────────────────
def spin_wheel_html(player_names):
    colors = ["#2563eb","#dc2626","#16a34a","#9333ea","#ea580c","#0891b2","#be185d","#b45309","#0f766e","#4338ca","#c2410c","#1d4ed8","#15803d","#7e22ce"]
    nj = json.dumps(player_names)
    cj = json.dumps(colors[:len(player_names)])
    return f"""<!DOCTYPE html><html><head>
<style>
body{{background:#f0f4f8;display:flex;flex-direction:column;align-items:center;justify-content:center;height:540px;margin:0;font-family:'Space Grotesk',system-ui,sans-serif;}}
canvas{{border-radius:50%;box-shadow:0 8px 40px rgba(37,99,235,0.3);}}
#result{{margin-top:14px;font-size:17px;font-weight:700;color:#1d4ed8;min-height:26px;text-align:center;letter-spacing:.3px;}}
#progress{{margin-top:8px;font-size:12px;color:#64748b;text-align:center;}}
.wrap{{position:relative;}}
.ptr{{position:absolute;top:50%;right:-18px;transform:translateY(-50%);width:0;height:0;border-top:13px solid transparent;border-bottom:13px solid transparent;border-left:22px solid #f59e0b;filter:drop-shadow(0 2px 4px rgba(245,158,11,0.5));}}
</style></head><body>
<div class="wrap"><canvas id="wh" width="290" height="290"></canvas><div class="ptr"></div></div>
<div id="result">Click anywhere to start spinning!</div>
<div id="progress"></div>
<script>
const names={nj},colors={cj};
const cv=document.getElementById('wh'),ctx=cv.getContext('2d');
let cur=0,spinning=false,rem=[...names],spinIdx=0,allAssigned=[];
const teams=['Team A','Team B','Team C','Team D','Team E','Team F','Team G'];

function draw(a){{
  const cx=145,cy=145,r=138,disp=rem.length>0?rem:names,arc=2*Math.PI/disp.length;
  ctx.clearRect(0,0,290,290);
  for(let i=0;i<disp.length;i++){{
    const s=a+i*arc;
    ctx.beginPath();ctx.moveTo(cx,cy);ctx.arc(cx,cy,r,s,s+arc);ctx.closePath();
    ctx.fillStyle=colors[i%colors.length];ctx.fill();
    ctx.strokeStyle='rgba(255,255,255,0.6)';ctx.lineWidth=2;ctx.stroke();
    ctx.save();ctx.translate(cx,cy);ctx.rotate(s+arc/2);ctx.textAlign='right';
    ctx.fillStyle='#fff';ctx.font='bold '+Math.min(12,160/disp.length+6)+'px Space Grotesk,system-ui';
    ctx.shadowColor='rgba(0,0,0,0.4)';ctx.shadowBlur=3;
    const n=disp[i];ctx.fillText(n.length>14?n.substring(0,13)+'…':n,r-8,4);ctx.restore();
  }}
  ctx.beginPath();ctx.arc(cx,cy,18,0,2*Math.PI);
  ctx.fillStyle='#fff';ctx.fill();ctx.strokeStyle='#e2e8f0';ctx.lineWidth=2;ctx.stroke();
  ctx.fillStyle='#2563eb';ctx.font='bold 12px system-ui';ctx.textAlign='center';ctx.fillText('🏓',cx,cy+4);
}}

function spin(){{
  if(spinning||rem.length===0)return;
  spinning=true;
  const extra=(4+Math.random()*4)*2*Math.PI,stop=Math.random()*2*Math.PI;
  const total=extra+stop,dur=3500,t0=performance.now(),a0=cur;
  function anim(now){{
    const el=now-t0,t=Math.min(el/dur,1),e=1-Math.pow(1-t,4);
    cur=a0+total*e;draw(cur);
    if(t<1){{requestAnimationFrame(anim);return;}}
    spinning=false;
    const arc=2*Math.PI/rem.length;
    const norm=(((-cur)%(2*Math.PI))+2*Math.PI)%(2*Math.PI);
    const idx=Math.floor(norm/arc)%rem.length;
    const w=rem[idx];
    if(spinIdx%2===0){{allAssigned.push(w);document.getElementById('result').textContent='🏓 '+w+' → '+teams[Math.floor(spinIdx/2)];}}
    else{{const prev=allAssigned[allAssigned.length-1];document.getElementById('result').textContent='🤝 '+prev+' & '+w+' = '+teams[Math.floor(spinIdx/2)];}}
    spinIdx++;
    rem=rem.filter(n=>n!==w);
    document.getElementById('progress').textContent=rem.length>0?rem.length+' players remaining':'🎉 All teams assigned! The system has saved them.';
    setTimeout(()=>{{draw(cur);if(rem.length>0)spin();}},1200);
  }}
  requestAnimationFrame(anim);
}}

document.body.addEventListener('click',()=>{{if(!spinning&&rem.length>0)spin();}});
draw(0);
</script></body></html>"""

# ─── Confetti HTML ────────────────────────────────────────────────────────────
def confetti_html(message="", color="#2563eb"):
    return f"""<div style='text-align:center;padding:20px;background:linear-gradient(135deg,#0f172a,#1e40af);
    border-radius:16px;color:#fff;animation:fadeInUp .5s ease;'>
    <div style='font-size:48px;margin-bottom:8px;filter:drop-shadow(0 4px 8px rgba(0,0,0,0.3))'>🏆</div>
    <div style='font-family:Inter,sans-serif;font-size:22px;font-weight:900;letter-spacing:-0.5px;'>{message}</div>
    </div>"""

# ─── Render Helpers ───────────────────────────────────────────────────────────
def render_match(m):
    t1=(m.get("team1") or {})
    t2=(m.get("team2") or {})
    court=(m.get("court") or {})
    winner=(m.get("winner") or {})
    status=m.get("status","pending")
    s1=m.get("score_team1",0); s2=m.get("score_team2",0)
    stage_map={"group":"GROUP","semifinal":"SEMI","third_place":"3RD","final":"FINAL"}
    stage_lbl=stage_map.get(m.get("stage",""),"")
    score_str=f"{s1} — {s2}" if status!="pending" else "—"
    win_str=""
    if winner.get("name") and status=="completed":
        win_str=f" &nbsp;<span style='color:#15803d;font-size:13px'>🏆 {winner['name']}</span>"
    badge={"live":"<span class='badge-live'>● LIVE</span>","completed":"<span class='badge-done'>✓ Done</span>","pending":"<span class='badge-pending'>Upcoming</span>"}[status]
    st.markdown(f"""
    <div class='mrow {status}'>
        <span class='mrow-num'>#{m['match_number']} {stage_lbl}</span>
        <span class='mrow-teams'>{t1.get('name','?')} <span class='mrow-vs'>vs</span> {t2.get('name','?')}{win_str}</span>
        <span class='mrow-score'>{score_str}</span>
        <span class='mrow-court'>{court.get('name','?')}</span>
        {badge}
    </div>""", unsafe_allow_html=True)

def render_leaderboard(rows, my_team_name=None):
    rows=sorted(rows,key=lambda x:(x["won"],x["score_diff"],x["score_for"]),reverse=True)
    pos_icons={1:"🥇",2:"🥈",3:"🥉",4:"4th"}
    st.markdown("""<div class='lb-head'>
    <div>Pos</div><div>Team</div><div>Played</div><div>W</div><div>L</div>
    <div>For</div><div>Agn</div><div>Diff</div></div>""", unsafe_allow_html=True)
    for i,row in enumerate(rows):
        pos=i+1
        diff=row["score_diff"]
        ds=("+" if diff>0 else "")+str(diff)
        dc="#15803d" if diff>0 else "#dc2626" if diff<0 else "#64748b"
        is_mine=my_team_name and row["team_name"]==my_team_name
        cls="mine" if is_mine else ("qual" if pos<=4 else "")
        star=" ⭐" if is_mine else ""
        st.markdown(f"""<div class='lb-row {cls}'>
        <div style='font-weight:800;color:#0f172a'>{pos_icons.get(pos,str(pos))}</div>
        <div style='font-weight:700;color:#0f172a'>{row['team_name']}{star}</div>
        <div style='color:#64748b'>{row['matches_played']}</div>
        <div style='color:#15803d;font-weight:700'>{row['won']}</div>
        <div style='color:#dc2626'>{row['lost']}</div>
        <div style='color:#2563eb'>{row['score_for']}</div>
        <div style='color:#7c3aed'>{row['score_against']}</div>
        <div style='color:{dc};font-weight:700'>{ds}</div>
        </div>""", unsafe_allow_html=True)
    st.caption("🏅 Top 4 qualify for Semifinals | ⭐ = Your team")

def render_bracket(matches, title):
    st.markdown(f"<div class='stitle'>🏆 {title}</div>", unsafe_allow_html=True)
    for m in matches:
        t1=(m.get("team1") or {})
        t2=(m.get("team2") or {})
        winner=(m.get("winner") or {})
        status=m.get("status","pending")
        s1=m.get("score_team1",0); s2=m.get("score_team2",0)
        t1_cls="winner" if winner.get("id")==t1.get("id") and status=="completed" else ("loser" if status=="completed" else "")
        t2_cls="winner" if winner.get("id")==t2.get("id") and status=="completed" else ("loser" if status=="completed" else "")
        stage_map={"semifinal":"Semifinal","third_place":"3rd Place Match","final":"Grand Final"}
        st.markdown(f"""
        <div class='bracket-match'>
            <div class='bracket-header'>{stage_map.get(m.get('stage',''),'Match')} · Match #{m['match_number']} · {(m.get('court') or {}).get('name','?')}</div>
            <div class='bracket-team {t1_cls}'>
                <span>{t1.get('name','?')}</span>
                <span class='bracket-score' style='color:{"#15803d" if t1_cls=="winner" else "#94a3b8" if t1_cls=="loser" else "#0f172a"}'>{s1}</span>
            </div>
            <div class='bracket-team {t2_cls}'>
                <span>{t2.get('name','?')}</span>
                <span class='bracket-score' style='color:{"#15803d" if t2_cls=="winner" else "#94a3b8" if t2_cls=="loser" else "#0f172a"}'>{s2}</span>
            </div>
        </div>""", unsafe_allow_html=True)

def show_teams_grid(teams):
    cols=st.columns(4)
    for i,t in enumerate(teams):
        p1=t.get("p1") or {}; p2=t.get("p2") or {}
        color=TEAM_COLORS[i%len(TEAM_COLORS)]
        p1n=p1.get("name","?"); p2n=p2.get("name","?"); tn=t["name"]
        with cols[i%4]:
            st.markdown(f"""<div style='background:#fff;border:1px solid #e2e8f0;border-radius:10px;
            border-top:3px solid {color};padding:14px;margin-bottom:12px;box-shadow:0 1px 4px rgba(0,0,0,0.05)'>
            <div style='font-size:15px;font-weight:800;color:#0f172a;margin-bottom:6px'>{tn}</div>
            <div style='font-size:13px;color:#475569;padding:2px 0'>🏓 {p1n}</div>
            <div style='font-size:13px;color:#475569;padding:2px 0'>🏓 {p2n}</div>
            </div>""", unsafe_allow_html=True)

# ─── PAGES ────────────────────────────────────────────────────────────────────

def page_signup(state, counts):
    if state["signups_frozen"]:
        st.error("🔒 Signups are closed — all slots are filled. Please log in.")
        return
    available=[r for r in ("admin","referee","player") if counts[r]<LIMITS[r]]
    if not available:
        update_state(signups_frozen=True)
        st.error("All slots filled!")
        return
    st.markdown("<div class='stitle'>📝 Create Your Account</div>", unsafe_allow_html=True)
    c1,c2,c3=st.columns(3)
    c1.metric("Players",f"{counts['player']} / 14")
    c2.metric("Referees",f"{counts['referee']} / 2")
    c3.metric("Admin",f"{counts['admin']} / 1")
    st.markdown("---")
    with st.form("signup",clear_on_submit=True):
        name=st.text_input("Full Name")
        mobile=st.text_input("Mobile Number — 10 digits (your login username)",max_chars=10)
        password=st.text_input("Password",type="password",placeholder="Min 6 characters")
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
                st.success(f"✅ Registered as **{role}**! Please switch to the Login tab.")
                nc=count_by_role()
                if nc["player"]>=14 and nc["referee"]>=2 and nc["admin"]>=1:
                    update_state(signups_frozen=True)
                    auto_assign_referees()
                st.rerun()

def page_login():
    st.markdown("<div class='stitle'>🔐 Login</div>", unsafe_allow_html=True)
    with st.form("login"):
        mobile=st.text_input("Mobile Number")
        password=st.text_input("Password",type="password")
        sub=st.form_submit_button("Login",type="primary",use_container_width=True)
    if sub:
        if not mobile or not password:
            st.error("Fill in both fields.")
        else:
            user,err=login_user(mobile.strip(),password)
            if err: st.error(err)
            else:
                st.session_state.user=user
                st.rerun()

def page_admin(state):
    tabs=st.tabs(["👥 Participants","🎡 Teams","📅 Schedule","🏆 Leaderboard","🥊 Knockout","🚨 Disputes"])

    # ── PARTICIPANTS ──────────────────────────────────────────────────────────
    with tabs[0]:
        st.markdown("<div class='stitle'>👥 Registered Participants</div>", unsafe_allow_html=True)
        users=get_all_users()
        players=[u for u in users if u["role"]=="player"]
        refs=[u for u in users if u["role"]=="referee"]
        admins=[u for u in users if u["role"]=="admin"]
        c1,c2,c3=st.columns(3)
        with c1:
            st.markdown(f"**🏓 Players ({len(players)}/14)**")
            for p in players:
                st.markdown(f"<div class='uchip'><div class='uchip-name'>{p['name']}</div><div class='uchip-mob'>{p['mobile']}</div></div>",unsafe_allow_html=True)
        with c2:
            st.markdown(f"**🎯 Referees ({len(refs)}/2)**")
            for r in refs:
                st.markdown(f"<div class='uchip'><div class='uchip-name'>{r['name']}</div><div class='uchip-mob'>{r['mobile']}</div></div>",unsafe_allow_html=True)
            courts=get_courts()
            for court in courts:
                ref_info=court.get("ref") or {}
                rn=ref_info.get("name","Unassigned") if isinstance(ref_info,dict) else "Unassigned"
                st.caption(f"🏟️ {court['name']} → **{rn}**")
        with c3:
            st.markdown(f"**⚙️ Admin ({len(admins)}/1)**")
            for a in admins:
                st.markdown(f"<div class='uchip'><div class='uchip-name'>{a['name']}</div><div class='uchip-mob'>{a['mobile']}</div></div>",unsafe_allow_html=True)
        needed=[]
        if len(players)<14: needed.append(f"{14-len(players)} more player(s)")
        if len(refs)<2: needed.append(f"{2-len(refs)} more referee(s)")
        if needed: st.warning(f"Waiting for: {', '.join(needed)}")
        else: st.success("✅ All 17 participants registered!")

    # ── TEAMS ─────────────────────────────────────────────────────────────────
    with tabs[1]:
        st.markdown("<div class='stitle'>🎡 Team Assignment — Spin the Wheel</div>", unsafe_allow_html=True)
        teams=get_teams()
        if state["teams_assigned"] and teams:
            st.success("✅ Teams have been assigned.")
            show_teams_grid(teams)
        else:
            users=get_all_users()
            players=[u for u in users if u["role"]=="player"]
            if len(players)<14:
                st.warning(f"Need 14 players first. Currently {len(players)}.")
            else:
                st.info("🎡 Watch the wheel spin and auto-assign all 7 teams! Then click **Confirm & Save Teams** to lock them in.")
                components.html(spin_wheel_html([p["name"] for p in players]),height=540)
                st.markdown("---")
                # Pre-compute the random assignment so user sees exactly what will be saved
                if "pending_teams" not in st.session_state:
                    shuffled=random.sample(players,len(players))
                    st.session_state.pending_teams=[
                        {"name":TEAM_LABELS[i],"player1_id":shuffled[i*2]["id"],"player2_id":shuffled[i*2+1]["id"],
                         "p1n":shuffled[i*2]["name"],"p2n":shuffled[i*2+1]["name"]}
                        for i in range(7)]
                st.markdown("**Teams that will be saved:**")
                cols_t=st.columns(4)
                for idx,t in enumerate(st.session_state.pending_teams):
                    with cols_t[idx%4]:
                        st.markdown(f"**{t['name']}**: {t['p1n']} & {t['p2n']}")
                col_a,col_b=st.columns([2,1])
                with col_a:
                    if st.button("✅ Confirm & Save Teams",type="primary",use_container_width=True):
                        assignments=[{"name":t["name"],"player1_id":t["player1_id"],"player2_id":t["player2_id"]}
                                     for t in st.session_state.pending_teams]
                        create_teams(assignments)
                        update_state(teams_assigned=True)
                        del st.session_state.pending_teams
                        st.success("✅ Teams saved!")
                        st.rerun()
                with col_b:
                    if st.button("🔀 Re-randomise",use_container_width=True):
                        if "pending_teams" in st.session_state:
                            del st.session_state.pending_teams
                        st.rerun()

    # ── SCHEDULE ──────────────────────────────────────────────────────────────
    with tabs[2]:
        st.markdown("<div class='stitle'>📅 Group Stage Schedule</div>", unsafe_allow_html=True)
        if not state["teams_assigned"]:
            st.warning("Assign teams first.")
        else:
            existing=get_matches("group")
            if not existing:
                courts=get_courts()
                if not all(c.get("referee_id") for c in courts):
                    st.info("Referee court assignments not done yet. Auto-assigning now...")
                    auto_assign_referees()
                    st.rerun()
                st.info("**21 matches** will be generated across Court 2 and Court 3. No team plays 3+ back-to-back.")
                if st.button("Generate Match Schedule",type="primary"):
                    courts=get_courts()
                    court_map={c["name"]:c for c in courts}
                    team_map={t["name"]:t["id"] for t in get_teams_simple()}
                    sched=build_schedule(TEAM_LABELS,[c["name"] for c in courts])
                    matches=[{"match_number":i+1,"stage":"group",
                              "team1_id":team_map[s["team1"]],"team2_id":team_map[s["team2"]],
                              "court_id":court_map[s["court_name"]]["id"],
                              "referee_id":court_map[s["court_name"]].get("referee_id"),
                              "status":"pending","match_order":i+1} for i,s in enumerate(sched)]
                    create_matches(matches)
                    update_state(phase="group_stage",schedule_generated=True)
                    st.success("✅ 21 matches generated!")
                    st.rerun()
            else:
                done=sum(1 for m in existing if m["status"]=="completed")
                live=sum(1 for m in existing if m["status"]=="live")
                c1,c2,c3=st.columns(3)
                c1.metric("Total",21); c2.metric("Done",done); c3.metric("Live",live)
                st.markdown("---")
                # Group by court
                court_groups={}
                for m in existing:
                    cn=(m.get("court") or {}).get("name","Unknown")
                    court_groups.setdefault(cn,[]).append(m)
                for court_name,cms in sorted(court_groups.items()):
                    st.markdown(f"<div class='court-title'>🏟️ {court_name}</div>", unsafe_allow_html=True)
                    for m in cms:
                        t1n=(m.get("team1") or {}).get("name","?")
                        t2n=(m.get("team2") or {}).get("name","?")
                        status=m.get("status","pending")
                        s1=m.get("score_team1",0); s2=m.get("score_team2",0)
                        winner=(m.get("winner") or {})
                        score_str=f"{s1}—{s2}" if status!="pending" else "—"
                        win_badge=""
                        if winner.get("name") and status=="completed":
                            win_badge=f"<span style='color:#15803d;font-size:12px'>🏆 {winner['name']}</span>"
                        badge={"live":"<span class='badge-live'>● LIVE</span>","completed":"<span class='badge-done'>✓ Done</span>","pending":"<span class='badge-pending'>Upcoming</span>"}[status]
                        st.markdown(f"""<div class='mrow {status}'>
                        <span class='mrow-num'>#{m['match_number']}</span>
                        <div style='flex:1'>
                            <div class='mrow-teams'>{t1n} <span class='mrow-vs'>vs</span> {t2n}</div>
                            <div style='font-size:11px;color:#94a3b8;margin-top:3px'>
                                🏓 {t1n} &amp; 🏓 {t2n}
                            </div>
                        </div>
                        <span class='mrow-score'>{score_str}</span>
                        {win_badge}
                        {badge}
                        </div>""", unsafe_allow_html=True)
                if done==21 and not state["group_stage_complete"]:
                    update_state(group_stage_complete=True)
                    st.success("🎉 Group stage complete!")

    # ── LEADERBOARD ───────────────────────────────────────────────────────────
    with tabs[3]:
        st.markdown("<div class='stitle'>🏆 Group Stage Leaderboard</div>", unsafe_allow_html=True)
        rows=get_leaderboard()
        if not rows: st.info("No data yet.")
        else: render_leaderboard(rows)

    # ── KNOCKOUT ──────────────────────────────────────────────────────────────
    with tabs[4]:
        st.markdown("<div class='stitle'>🥊 Knockout Stage</div>", unsafe_allow_html=True)
        if not state["group_stage_complete"]:
            all_g=get_matches("group"); done=sum(1 for m in all_g if m["status"]=="completed")
            st.warning(f"Group stage not complete. ({done}/21 done)")
        else:
            sf=get_matches("semifinal"); tp=get_matches("third_place"); fn=get_matches("final")
            if not sf:
                top4,_=get_top4()
                st.markdown("<div class='stitle'>🏅 Semifinal Bracket</div>", unsafe_allow_html=True)
                # Bracket view
                col1,col2=st.columns(2)
                seeds=["1st 🥇","2nd 🥈","3rd 🥉","4th"]
                with col1:
                    st.markdown("""<div class='bracket-match'>
                    <div class='bracket-header'>Semifinal 1 — Court 2</div>""", unsafe_allow_html=True)
                    for idx in [0,3]:
                        t=top4[idx]; diff=t["score_diff"]; ds=("+" if diff>0 else "")+str(diff)
                        st.markdown(f"""<div class='bracket-team'>
                        <span><span class='bracket-seed'>{seeds[idx]}</span>{t['team_name']}</span>
                        <span style='font-size:12px;color:#64748b'>W:{t['won']} Diff:{ds}</span>
                        </div>""", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                with col2:
                    st.markdown("""<div class='bracket-match'>
                    <div class='bracket-header'>Semifinal 2 — Court 3</div>""", unsafe_allow_html=True)
                    for idx in [1,2]:
                        t=top4[idx]; diff=t["score_diff"]; ds=("+" if diff>0 else "")+str(diff)
                        st.markdown(f"""<div class='bracket-team'>
                        <span><span class='bracket-seed'>{seeds[idx]}</span>{t['team_name']}</span>
                        <span style='font-size:12px;color:#64748b'>W:{t['won']} Diff:{ds}</span>
                        </div>""", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("<br>",unsafe_allow_html=True)
                if st.button("🥊 Create Semifinal Matches",type="primary"):
                    create_semis(top4); update_state(phase="semifinals"); st.rerun()
            else:
                render_bracket(sf,"Semifinals")
                sf_done=all(m["status"]=="completed" for m in sf)
                if sf_done and not tp and not fn:
                    if st.button("🏆 Create Final & 3rd Place",type="primary"):
                        create_finals(sf); update_state(semifinals_complete=True,phase="final"); st.rerun()
                if tp:
                    st.markdown("<br>",unsafe_allow_html=True)
                    render_bracket(tp,"3rd Place Match 🥉")
                if fn:
                    st.markdown("<br>",unsafe_allow_html=True)
                    render_bracket(fn,"Grand Final 🏆")
                    if all(m["status"]=="completed" for m in fn):
                        w=(fn[0].get("winner") or {}).get("name","")
                        if w:
                            st.balloons()
                            st.markdown(f"""<div style='background:linear-gradient(135deg,#0f172a,#1e40af);
                            border-radius:16px;padding:40px;text-align:center;margin-top:20px;color:#fff;
                            box-shadow:0 8px 32px rgba(30,64,175,0.4)'>
                            <div style='font-size:12px;font-weight:700;letter-spacing:4px;color:#fbbf24;margin-bottom:8px'>TOURNAMENT CHAMPION</div>
                            <div style='font-family:Inter,sans-serif;font-size:52px;font-weight:900;letter-spacing:-1px'>{w}</div>
                            <div style='font-size:36px;margin-top:8px'>🏆🎉🏓</div>
                            </div>""", unsafe_allow_html=True)
                            update_state(phase="completed")

    # ── DISPUTES ──────────────────────────────────────────────────────────────
    with tabs[5]:
        st.markdown("<div class='stitle'>🚨 Referee Disputes</div>", unsafe_allow_html=True)
        disputes=get_open_disputes()
        if not disputes:
            st.success("✅ No open disputes.")
        else:
            for d in disputes:
                match=d.get("match") or {}
                referee=d.get("referee") or {}
                t1n=(match.get("team1") or {}).get("name","?")
                t2n=(match.get("team2") or {}).get("name","?")
                st.markdown(f"""<div class='dispute-banner'>
                <div style='font-weight:700;color:#b45309;margin-bottom:4px'>⚠️ Dispute — Match #{match.get('match_number','?')}: {t1n} vs {t2n}</div>
                <div style='font-size:13px;color:#92400e'>Flagged by: <strong>{referee.get('name','?')}</strong></div>
                <div style='font-size:13px;color:#92400e;margin-top:4px'>Note: {d.get('note','No note')}</div>
                <div style='font-size:12px;color:#b45309;margin-top:4px'>Score at flag: {match.get('score_team1',0)}—{match.get('score_team2',0)}</div>
                </div>""", unsafe_allow_html=True)
                c1,c2=st.columns(2)
                with c1:
                    if st.button(f"✅ Resolve (keep score)",key=f"res_{d['id']}"):
                        resolve_dispute(d["id"],match.get("id"),undo=False); st.rerun()
                with c2:
                    if st.button(f"↩️ Resolve + Undo Last Point",key=f"undo_{d['id']}",type="primary"):
                        resolve_dispute(d["id"],match.get("id"),undo=True); st.rerun()
                st.markdown("---")


def page_referee(user):
    st.markdown(f"<div class='stitle'>🎯 Referee Panel — {user['name']}</div>", unsafe_allow_html=True)
    match,court=get_referee_match(user["id"])
    if court is None:
        st.warning("You have not been assigned to a court yet. Wait for the tournament to begin.")
        return
    st.markdown(f"""<div style='background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;
    padding:12px 20px;margin-bottom:18px;display:inline-block;'>
    <span style='font-size:11px;font-weight:700;color:#2563eb;letter-spacing:1.5px;text-transform:uppercase'>Your Court</span><br>
    <span style='font-size:22px;font-weight:900;color:#0f172a;'>🏟️ {court['name']}</span>
    </div>""", unsafe_allow_html=True)

    if match is None:
        # Check if there are completed matches
        all_m=get_matches()
        court_done=[m for m in all_m if (m.get("court") or {}).get("name")==court["name"] and m["status"]=="completed"]
        st.success(f"✅ No pending matches on {court['name']} right now. {len(court_done)} matches completed on this court.")
        return

    t1=match.get("team1") or {}; t2=match.get("team2") or {}
    status=match.get("status","pending")
    s1=match.get("score_team1",0); s2=match.get("score_team2",0)
    history=match.get("score_history") or []
    if isinstance(history,str): history=json.loads(history) if history else []

    stage_map={"group":"Group Stage","semifinal":"Semifinal","third_place":"3rd Place","final":"Grand Final"}
    st.markdown(f"""<div style='text-align:center;margin-bottom:16px;'>
    <span style='font-size:12px;font-weight:600;color:#64748b;letter-spacing:1px;'>
    MATCH #{match['match_number']} &nbsp;·&nbsp; {stage_map.get(match.get('stage',''),'')}&nbsp;·&nbsp; {court['name']}
    </span></div>""", unsafe_allow_html=True)

    # Score display
    c1,cv,c2=st.columns([5,2,5])
    with c1:
        st.markdown(f"""<div class='sbox'>
        <div class='sbox-name'>{t1.get('name','Team 1')}</div>
        <div class='sbox-num score-red'>{s1}</div>
        </div>""", unsafe_allow_html=True)
    with cv:
        st.markdown("""<div style='text-align:center;padding:32px 0'>
        <div style='font-size:18px;font-weight:900;color:#cbd5e1'>VS</div>
        <div style='font-size:10px;font-weight:700;color:#e2e8f0;margin-top:6px;letter-spacing:1px'>FIRST TO 15</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class='sbox'>
        <div class='sbox-name'>{t2.get('name','Team 2')}</div>
        <div class='sbox-num score-blue'>{s2}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if status=="completed":
        w=match.get("winner") or {}
        st.markdown(confetti_html(f"🏆 {w.get('name','?')} Wins!"), unsafe_allow_html=True)
        st.markdown("<br>",unsafe_allow_html=True)
        if match.get("stage")=="group" and check_group_done():
            update_state(group_stage_complete=True)
        if st.button("➡️ Next Match",type="primary",use_container_width=True):
            st.rerun()
        # Show moments log
        moments=get_moments(match["id"])
        if moments:
            st.markdown("**Match Highlights:**")
            for mom in moments:
                mtype=mom["moment_type"]
                icons={"good_shot":"🎯 Good Shot","great_rally":"🔥 Great Rally","crazy_comeback":"⚡ Crazy Comeback"}
                st.markdown(f"<span class='moment-chip moment-{mtype.replace('_','-').split('-')[0]}'>{icons.get(mtype,mtype)}</span> @ {mom['score_at_time']}",unsafe_allow_html=True)
        return

    if status=="pending":
        col1,col2=st.columns([3,1])
        with col1:
            if st.button("▶️ Start Match",type="primary",use_container_width=True):
                start_match(match["id"])
                st.markdown("""<div style='background:linear-gradient(135deg,#0f172a,#1e40af);color:#fff;
                border-radius:12px;padding:20px;text-align:center;'>
                <div style='font-size:28px'>🏓</div>
                <div style='font-weight:800;font-size:18px;margin-top:6px'>Match Started!</div>
                </div>""", unsafe_allow_html=True)
                time.sleep(1)
                st.rerun()
        return

    # LIVE scoring
    st.markdown("""<div style='text-align:center;padding:8px;background:#fee2e2;border:1px solid #fecaca;
    border-radius:8px;margin-bottom:16px;'>
    <span style='color:#dc2626;font-weight:700;font-size:12px;letter-spacing:2px;'>● LIVE MATCH</span>
    </div>""", unsafe_allow_html=True)

    # Score buttons
    b1,bundo,b2=st.columns([4,2,4])
    with b1:
        if st.button(f"➕ Point → {t1.get('name','T1')}",type="primary",use_container_width=True,key="pt1"):
            won,_=add_score(match["id"],"score_team1",s1,s2,t1.get("id"),t2.get("id"),history)
            if won:
                st.balloons()
            st.rerun()
    with bundo:
        if st.button("↩️ Undo",use_container_width=True,key="undo_pt",help="Undo last point",
                     disabled=len(history)==0):
            undo_score(match["id"],history)
            st.rerun()
    with b2:
        if st.button(f"➕ Point → {t2.get('name','T2')}",type="secondary",use_container_width=True,key="pt2"):
            won,_=add_score(match["id"],"score_team2",s1,s2,t1.get("id"),t2.get("id"),history)
            if won:
                st.balloons()
            st.rerun()

    # Progress
    st.markdown("<br>",unsafe_allow_html=True)
    pc1,pc2=st.columns(2)
    with pc1:
        st.markdown(f"**{t1.get('name')}** — {s1} / 15")
        st.progress(min(s1/15,1.0))
    with pc2:
        st.markdown(f"**{t2.get('name')}** — {s2} / 15")
        st.progress(min(s2/15,1.0))

    st.markdown("---")
    # Moments
    st.markdown("**🎯 Tag a Moment**")
    score_str=f"{s1}—{s2}"
    mc1,mc2,mc3,mc4=st.columns(4)
    t1n=t1.get("name","T1"); t2n=t2.get("name","T2")
    with mc1:
        if st.button(f"🎯 Good Shot → {t1n}",use_container_width=True,key="gs_t1"):
            add_moment(match["id"],"good_shot",t1.get("id"),score_str); st.rerun()
    with mc2:
        if st.button(f"🎯 Good Shot → {t2n}",use_container_width=True,key="gs_t2"):
            add_moment(match["id"],"good_shot",t2.get("id"),score_str); st.rerun()
    with mc3:
        if st.button("🔥 Great Rally",use_container_width=True,key="gr"):
            add_moment(match["id"],"great_rally",None,score_str); st.rerun()
    with mc4:
        if st.button("⚡ Crazy Comeback",use_container_width=True,key="cc"):
            add_moment(match["id"],"crazy_comeback",None,score_str); st.rerun()

    # Dispute
    st.markdown("---")
    with st.expander("⚠️ Flag a Dispute"):
        note=st.text_input("Describe the dispute",key="dispute_note",placeholder="e.g. ball landed out, point contested")
        if st.button("🚩 Flag to Admin",type="secondary"):
            if note.strip():
                flag_dispute(match["id"],user["id"],note.strip())
                st.warning("⚠️ Dispute flagged to Admin.")
            else:
                st.error("Please enter a note.")

    # Auto-refresh
    time.sleep(2)
    st.rerun()


def page_player(user):
    st.markdown(f"<div class='stitle'>🏓 Welcome, {user['name']}</div>", unsafe_allow_html=True)
    # Find my team
    teams=get_teams()
    my_team=None
    for t in teams:
        p1=t.get("p1") or {}; p2=t.get("p2") or {}
        if user["id"] in (p1.get("id"),p2.get("id")):
            my_team=t; break

    if my_team:
        color=TEAM_COLORS[TEAM_LABELS.index(my_team["name"]) if my_team["name"] in TEAM_LABELS else 0]
        p1n=(my_team.get("p1") or {}).get("name","?")
        p2n=(my_team.get("p2") or {}).get("name","?")
        st.markdown(f"""<div style='background:{color}15;border:1px solid {color}40;border-left:4px solid {color};
        border-radius:10px;padding:14px 18px;margin-bottom:18px;display:flex;align-items:center;gap:16px;'>
        <div style='font-size:28px'>🏓</div>
        <div>
            <div style='font-size:16px;font-weight:900;color:#0f172a'>{my_team['name']}</div>
            <div style='font-size:13px;color:#64748b;margin-top:2px'>{p1n} &amp; {p2n}</div>
        </div>
        </div>""", unsafe_allow_html=True)

    tabs=st.tabs(["📅 My Schedule","🏆 Standings"])

    with tabs[0]:
        st.markdown("<div class='stitle'>📅 My Match Schedule</div>", unsafe_allow_html=True)
        if not my_team:
            st.info("Teams have not been assigned yet. Check back soon!")
        else:
            all_m=get_matches()
            my_m=sorted([m for m in all_m if
                (m.get("team1") or {}).get("id")==my_team["id"] or
                (m.get("team2") or {}).get("id")==my_team["id"]],
                key=lambda x:x["match_order"])
            if not my_m:
                st.info("Schedule not generated yet.")
            else:
                for m in my_m:
                    render_match(m)
                won=sum(1 for m in my_m if (m.get("winner") or {}).get("id")==my_team["id"] and m["status"]=="completed")
                played=sum(1 for m in my_m if m["status"]=="completed")
                st.markdown(f"<br>**Record: {won}W / {played-won}L** from {played} matches played",unsafe_allow_html=True)

    with tabs[1]:
        st.markdown("<div class='stitle'>🏆 Group Stage Standings</div>", unsafe_allow_html=True)
        rows=get_leaderboard()
        if not rows: st.info("No data yet.")
        else: render_leaderboard(rows, my_team["name"] if my_team else None)


# ─── Session Init ─────────────────────────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user=None

# ─── Load shared data once ────────────────────────────────────────────────────
try:
    _state=get_state()
    _counts=count_by_role()
    _phase=_state["phase"].replace("_"," ").title()
except Exception as _e:
    st.error(f"⚠️ Cannot connect to database. Check your Supabase secrets. Error: {_e}")
    st.stop()

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏓 Serve & Smash")
    st.markdown(f"""
    <div class='sb-stat'><span class='sb-lbl'>Players</span><span class='sb-val'>{_counts['player']} / 14</span></div>
    <div class='sb-stat'><span class='sb-lbl'>Referees</span><span class='sb-val'>{_counts['referee']} / 2</span></div>
    <div class='sb-stat'><span class='sb-lbl'>Admin</span><span class='sb-val'>{_counts['admin']} / 1</span></div>
    <div class='sb-stat'><span class='sb-lbl'>Phase</span><span class='sb-val'>{_phase}</span></div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    if st.session_state.user:
        u=st.session_state.user
        icons={"player":"🏓","referee":"🎯","admin":"⚙️"}
        st.success(f"{icons.get(u['role'],'👤')} **{u['name']}** ({u['role'].title()})")
        if st.button("Logout",use_container_width=True):
            st.session_state.user=None; st.rerun()
    else:
        st.info("Sign up or log in below.")

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class='hero'>
    <div class='hero-icon'>🏓</div>
    <div>
        <div class='hero-title'>Serve &amp; Smash</div>
        <div class='hero-sub'>Pickleball Tournament Management System</div>
        <div class='phase-pill'>{_phase}</div>
    </div>
</div>""", unsafe_allow_html=True)

# ─── Router ───────────────────────────────────────────────────────────────────
user=st.session_state.user
if user is None:
    t1,t2=st.tabs(["📝 Sign Up","🔐 Login"])
    with t1: page_signup(_state,_counts)
    with t2: page_login()
else:
    role=user["role"]
    if role=="admin": page_admin(_state)
    elif role=="referee": page_referee(user)
    elif role=="player": page_player(user)
