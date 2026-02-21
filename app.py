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
    page_title="🏸 Serve & Smash",
    page_icon="🏸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Rajdhani:wght@500;600;700&family=Space+Mono&display=swap');
html, body, [class*="css"] { font-family: 'Rajdhani', sans-serif; }
.stApp { background: linear-gradient(135deg, #0a0a0f 0%, #0d0d1a 100%); }
.hero-header {
    text-align: center; padding: 2rem 0 1rem;
    background: linear-gradient(180deg, rgba(255,60,60,0.08) 0%, transparent 100%);
    border-bottom: 1px solid rgba(255,255,255,0.06); margin-bottom: 2rem;
}
.hero-title {
    font-family: 'Bebas Neue', cursive;
    font-size: clamp(48px, 8vw, 80px); letter-spacing: 8px;
    background: linear-gradient(135deg, #ff3c3c, #ffb800);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin: 0; line-height: 1;
}
.hero-sub { font-family: 'Space Mono', monospace; color: #8888aa; font-size: 11px; letter-spacing: 5px; margin-top: 8px; }
.section-title { font-family: 'Bebas Neue', cursive; font-size: 24px; letter-spacing: 4px; color: #ffb800; margin-bottom: 1rem; }
.match-row {
    background: #1a1a25; border: 1px solid rgba(255,255,255,0.07);
    padding: 12px 20px; margin-bottom: 6px;
    display: flex; align-items: center; justify-content: space-between; font-size: 15px;
}
.match-live { border-left: 3px solid #ff3c3c; }
.match-done { border-left: 3px solid #22c55e; opacity: 0.8; }
.lb-row {
    display: grid; grid-template-columns: 40px 1fr 60px 50px 50px 80px 80px 80px;
    gap: 8px; padding: 10px 16px; background: #1a1a25;
    border: 1px solid rgba(255,255,255,0.07); margin-bottom: 4px; align-items: center; font-size: 14px;
}
.lb-header { background: #22223a; font-family: 'Space Mono', monospace; font-size: 10px; letter-spacing: 2px; color: #8888aa; }
.lb-qualified { border-left: 3px solid #ffb800; }
section[data-testid="stSidebar"] { background: #0d0d1a; border-right: 1px solid rgba(255,255,255,0.07); }
</style>
""", unsafe_allow_html=True)

# ─── Supabase Client ─────────────────────────────────────────────────────────
@st.cache_resource
def get_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

# ─── DB Helpers ───────────────────────────────────────────────────────────────
def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()
def check_pw(pw, h): return hash_pw(pw) == h

def signup_user(name, mobile, password, role):
    try:
        r = get_client().table("users").insert({"name": name, "mobile": mobile, "password_hash": hash_pw(password), "role": role}).execute()
        return r.data[0], None
    except Exception as e:
        return None, str(e)

def login_user(mobile, password):
    r = get_client().table("users").select("*").eq("mobile", mobile).execute()
    if not r.data: return None, "Mobile number not found"
    u = r.data[0]
    if not check_pw(password, u["password_hash"]): return None, "Incorrect password"
    return u, None

def count_by_role():
    r = get_client().table("users").select("role").execute()
    c = {"player": 0, "referee": 0, "admin": 0}
    for row in r.data: c[row["role"]] += 1
    return c

def get_all_users():
    return get_client().table("users").select("*").order("created_at").execute().data

def get_state():
    return get_client().table("tournament_state").select("*").eq("id", 1).execute().data[0]

def update_state(**kwargs):
    get_client().table("tournament_state").update(kwargs).eq("id", 1).execute()

def get_teams():
    return get_client().table("teams").select(
        "*, p1:users!teams_player1_id_fkey(id,name), p2:users!teams_player2_id_fkey(id,name)"
    ).order("name").execute().data

def get_teams_simple():
    return get_client().table("teams").select("id, name").order("name").execute().data

def create_teams(assignments):
    get_client().table("teams").insert(assignments).execute()

def get_courts():
    return get_client().table("courts").select("*, ref:users(id,name)").execute().data

def assign_referee_to_court(court_id, referee_id):
    get_client().table("courts").update({"referee_id": referee_id}).eq("id", court_id).execute()

def get_matches(stage=None):
    q = get_client().table("matches").select(
        "*, team1:teams!matches_team1_id_fkey(id,name), "
        "team2:teams!matches_team2_id_fkey(id,name), "
        "court:courts(name), winner:teams!matches_winner_id_fkey(id,name)"
    ).order("match_order")
    if stage: q = q.eq("stage", stage)
    return q.execute().data

def create_matches(matches):
    get_client().table("matches").insert(matches).execute()

def start_match(match_id):
    get_client().table("matches").update({"status": "live"}).eq("id", match_id).execute()

def add_score(match_id, field, current, t1_id, t2_id):
    new_score = current + 1
    get_client().table("matches").update({field: new_score}).eq("id", match_id).execute()
    if new_score >= 15:
        winner_id = t1_id if field == "score_team1" else t2_id
        get_client().table("matches").update({"winner_id": winner_id, "status": "completed"}).eq("id", match_id).execute()
        return True, winner_id
    return False, None

def get_live_matches():
    return get_client().table("matches").select(
        "*, team1:teams!matches_team1_id_fkey(id,name), "
        "team2:teams!matches_team2_id_fkey(id,name), court:courts(name)"
    ).eq("status", "live").execute().data

def get_referee_match(referee_id):
    court_res = get_client().table("courts").select("id, name").eq("referee_id", referee_id).execute()
    if not court_res.data: return None, None
    court = court_res.data[0]
    match_res = get_client().table("matches").select(
        "*, team1:teams!matches_team1_id_fkey(id,name), "
        "team2:teams!matches_team2_id_fkey(id,name), court:courts(name)"
    ).eq("court_id", court["id"]).in_("status", ["pending", "live"]).order("match_order").limit(1).execute()
    return (match_res.data[0] if match_res.data else None), court

def get_leaderboard():
    rows = get_client().table("leaderboard").select("*").execute().data
    for r in rows:
        r["score_diff"] = r["score_for"] - r["score_against"]
    return rows

def check_group_stage_complete():
    res = get_client().table("matches").select("id").eq("stage", "group").neq("status", "completed").execute()
    return len(res.data) == 0

def get_qualified_teams():
    rows = get_leaderboard()
    rows.sort(key=lambda x: (x["won"], x["score_diff"], x["score_for"]), reverse=True)
    return rows[:4], rows[4:]

def create_knockout_matches(top4):
    courts = get_courts()
    c2 = next(c for c in courts if c["name"] == "Court 2")
    c3 = next(c for c in courts if c["name"] == "Court 3")
    max_n = get_client().table("matches").select("match_number").order("match_number", desc=True).limit(1).execute()
    max_o = get_client().table("matches").select("match_order").order("match_order", desc=True).limit(1).execute()
    base = max_n.data[0]["match_number"] if max_n.data else 21
    base_o = max_o.data[0]["match_order"] if max_o.data else 21
    get_client().table("matches").insert([
        {"match_number": base+1, "stage": "semifinal", "team1_id": top4[0]["id"], "team2_id": top4[3]["id"],
         "court_id": c2["id"], "referee_id": c2.get("referee_id"), "status": "pending", "match_order": base_o+1},
        {"match_number": base+2, "stage": "semifinal", "team1_id": top4[1]["id"], "team2_id": top4[2]["id"],
         "court_id": c3["id"], "referee_id": c3.get("referee_id"), "status": "pending", "match_order": base_o+2},
    ]).execute()

def create_final_matches(sf_matches):
    courts = get_courts()
    c2 = next(c for c in courts if c["name"] == "Court 2")
    c3 = next(c for c in courts if c["name"] == "Court 3")
    max_n = get_client().table("matches").select("match_number").order("match_number", desc=True).limit(1).execute()
    max_o = get_client().table("matches").select("match_order").order("match_order", desc=True).limit(1).execute()
    base = max_n.data[0]["match_number"]
    base_o = max_o.data[0]["match_order"]
    sf = sorted(sf_matches, key=lambda x: x["match_number"])
    def loser(m):
        t1 = (m.get("team1") or {}).get("id")
        t2 = (m.get("team2") or {}).get("id")
        w = m.get("winner_id") or ((m.get("winner") or {}).get("id"))
        return t1 if w == t2 else t2
    def winner(m):
        return m.get("winner_id") or ((m.get("winner") or {}).get("id"))
    get_client().table("matches").insert([
        {"match_number": base+1, "stage": "third_place", "team1_id": loser(sf[0]), "team2_id": loser(sf[1]),
         "court_id": c2["id"], "referee_id": c2.get("referee_id"), "status": "pending", "match_order": base_o+1},
        {"match_number": base+2, "stage": "final", "team1_id": winner(sf[0]), "team2_id": winner(sf[1]),
         "court_id": c3["id"], "referee_id": c3.get("referee_id"), "status": "pending", "match_order": base_o+2},
    ]).execute()

# ─── Schedule Logic ───────────────────────────────────────────────────────────
TEAM_LABELS = ["Team A","Team B","Team C","Team D","Team E","Team F","Team G"]
TEAM_COLORS = ["#ff3c3c","#ffb800","#00e5ff","#a855f7","#22c55e","#f97316","#ec4899"]

def build_schedule(team_names, court_names):
    all_pairs = list(combinations(team_names, 2))
    random.shuffle(all_pairs)
    consecutive = {t: 0 for t in team_names}
    last_played = {t: -1 for t in team_names}
    schedule = []
    remaining = list(all_pairs)
    slot = 0
    while remaining and slot < 200:
        busy = set()
        for court in court_names:
            if not remaining: break
            best, best_score = None, -1
            for pair in remaining:
                t1, t2 = pair
                if t1 in busy or t2 in busy: continue
                c1 = consecutive[t1] if last_played[t1] == slot - 1 else 0
                c2 = consecutive[t2] if last_played[t2] == slot - 1 else 0
                if c1 >= 2 or c2 >= 2: continue
                score = (slot - last_played[t1]) + (slot - last_played[t2])
                if score > best_score:
                    best_score = score
                    best = pair
            if best:
                remaining.remove(best)
                schedule.append({"team1": best[0], "team2": best[1], "court_name": court, "match_order": len(schedule)+1})
                busy.add(best[0]); busy.add(best[1])
        playing = {m["team1"] for m in schedule[-len(court_names):]} | {m["team2"] for m in schedule[-len(court_names):]}
        for t in team_names:
            if t in playing:
                consecutive[t] = (consecutive[t]+1) if last_played[t] == slot-1 else 1
                last_played[t] = slot
        slot += 1
    for pair in remaining:
        schedule.append({"team1": pair[0], "team2": pair[1], "court_name": court_names[len(schedule)%len(court_names)], "match_order": len(schedule)+1})
    return schedule

# ─── UI Helpers ───────────────────────────────────────────────────────────────
def render_match_row(m, highlight_team_id=None):
    t1 = m.get("team1") or {}
    t2 = m.get("team2") or {}
    court = m.get("court") or {}
    winner = m.get("winner") or {}
    status = m.get("status", "pending")
    cls = "match-live" if status == "live" else "match-done" if status == "completed" else ""
    score = f"<span style='font-family:Space Mono,monospace;color:#ffb800;font-weight:700'>{m['score_team1']}—{m['score_team2']}</span>" if status != "pending" else "<span style='color:#8888aa;font-size:13px'>UPCOMING</span>"
    win_label = f" 🏆 <span style='color:#22c55e'>{winner.get('name','')}</span>" if winner.get("name") and status == "completed" else ""
    stage_label = {"group":"GROUP","semifinal":"SEMI","third_place":"3RD","final":"FINAL"}.get(m.get("stage",""),"")
    st.markdown(f"""
    <div class='match-row {cls}'>
        <span style='color:#8888aa;font-family:Space Mono,monospace;font-size:10px;'>#{m['match_number']} {stage_label}</span>
        <span style='font-weight:700;font-size:16px;margin:0 12px;'>
            {t1.get('name','?')} <span style='color:#8888aa;font-size:12px'>VS</span> {t2.get('name','?')}{win_label}
        </span>
        {score}
        <span style='color:#00e5ff;font-family:Space Mono,monospace;font-size:11px;margin-left:12px'>{court.get('name','?')}</span>
        <span style='color:{"#ff3c3c" if status=="live" else "#22c55e" if status=="completed" else "#8888aa"};font-size:10px;margin-left:8px'>
            {"🔴 LIVE" if status=="live" else "✅ DONE" if status=="completed" else "⏳"}
        </span>
    </div>""", unsafe_allow_html=True)

def render_leaderboard(rows, my_team_name=None):
    rows = sorted(rows, key=lambda x: (x["won"], x["score_diff"], x["score_for"]), reverse=True)
    pos_icons = {1:"🥇",2:"🥈",3:"🥉",4:"🏅"}
    st.markdown("""<div class='lb-row lb-header'>
        <div>POS</div><div>TEAM</div><div>MP</div><div>W</div><div>L</div><div>SF</div><div>SA</div><div>DIFF</div>
    </div>""", unsafe_allow_html=True)
    for i, row in enumerate(rows):
        pos = i+1
        diff = row["score_diff"]
        diff_str = f"+{diff}" if diff > 0 else str(diff)
        diff_color = "#22c55e" if diff > 0 else "#ef4444" if diff < 0 else "#8888aa"
        is_mine = my_team_name and row["team_name"] == my_team_name
        st.markdown(f"""<div class='lb-row {"lb-qualified" if pos<=4 else ""}' style='{"background:#1a1a00;border:1px solid #ffb800;" if is_mine else ""}'>
            <div style='font-size:18px'>{pos_icons.get(pos,str(pos))}</div>
            <div style='font-weight:700;{"color:#ffb800;" if is_mine else ""}'>{row['team_name']} {"⭐" if is_mine else ""}</div>
            <div style='color:#8888aa'>{row['matches_played']}</div>
            <div style='color:#22c55e;font-weight:700'>{row['won']}</div>
            <div style='color:#ef4444'>{row['lost']}</div>
            <div style='color:#00e5ff'>{row['score_for']}</div>
            <div style='color:#ff8888'>{row['score_against']}</div>
            <div style='color:{diff_color};font-weight:700'>{diff_str}</div>
        </div>""", unsafe_allow_html=True)
    st.caption("🏅 Top 4 qualify | SF=Score For | SA=Score Against | ⭐=Your team")

# ─── Spin Wheel HTML ──────────────────────────────────────────────────────────
def spin_wheel_html(player_names):
    colors = ["#ff3c3c","#ffb800","#00e5ff","#a855f7","#22c55e","#f97316","#ec4899","#06b6d4","#84cc16","#f43f5e","#8b5cf6","#14b8a6","#fb923c","#64748b"]
    names_json = json.dumps(player_names)
    colors_json = json.dumps(colors[:len(player_names)])
    return f"""<!DOCTYPE html><html><head>
<style>
  body{{background:#0a0a0f;display:flex;flex-direction:column;align-items:center;justify-content:center;height:560px;margin:0;font-family:Rajdhani,sans-serif;}}
  canvas{{border-radius:50%;box-shadow:0 0 60px rgba(255,60,60,0.4);}}
  #spinBtn{{margin-top:16px;background:linear-gradient(135deg,#ff3c3c,#ff6b6b);color:white;border:none;
    padding:14px 48px;font-size:20px;font-weight:700;letter-spacing:4px;cursor:pointer;
    clip-path:polygon(12px 0%,100% 0%,calc(100% - 12px) 100%,0% 100%);transition:all 0.2s;}}
  #spinBtn:hover{{background:linear-gradient(135deg,#ff5555,#ff8888);transform:scale(1.05);}}
  #spinBtn:disabled{{background:#333;cursor:not-allowed;transform:none;}}
  #result{{margin-top:12px;font-size:20px;font-weight:700;color:#ffb800;letter-spacing:3px;min-height:28px;text-align:center;}}
  .wrap{{position:relative;}}
  .ptr{{position:absolute;top:50%;right:-22px;transform:translateY(-50%);width:0;height:0;
    border-top:16px solid transparent;border-bottom:16px solid transparent;border-left:28px solid #ffb800;}}
</style></head><body>
<div class="wrap"><canvas id="wh" width="320" height="320"></canvas><div class="ptr"></div></div>
<button id="spinBtn" onclick="spin()">🎡 SPIN THE WHEEL</button>
<div id="result"></div>
<script>
const names={names_json},colors={colors_json};
const cv=document.getElementById('wh'),ctx=cv.getContext('2d');
let cur=0,spinning=false,rem=[...names];
function draw(a){{
  const cx=160,cy=160,r=156,disp=rem.length>0?rem:names,arc=2*Math.PI/disp.length;
  ctx.clearRect(0,0,320,320);
  for(let i=0;i<disp.length;i++){{
    const s=a+i*arc;
    ctx.beginPath();ctx.moveTo(cx,cy);ctx.arc(cx,cy,r,s,s+arc);ctx.closePath();
    ctx.fillStyle=colors[i%colors.length];ctx.fill();
    ctx.strokeStyle='rgba(0,0,0,0.3)';ctx.lineWidth=2;ctx.stroke();
    ctx.save();ctx.translate(cx,cy);ctx.rotate(s+arc/2);ctx.textAlign='right';
    ctx.fillStyle='#fff';ctx.font='bold '+Math.min(13,200/disp.length+7)+'px Rajdhani,sans-serif';
    ctx.shadowColor='rgba(0,0,0,0.8)';ctx.shadowBlur=4;
    const n=disp[i];ctx.fillText(n.length>12?n.substring(0,11)+'…':n,r-8,5);ctx.restore();
  }}
  ctx.beginPath();ctx.arc(cx,cy,22,0,2*Math.PI);
  ctx.fillStyle='#0a0a0f';ctx.fill();ctx.strokeStyle='#ffb800';ctx.lineWidth=3;ctx.stroke();
  ctx.fillStyle='#ffb800';ctx.font='bold 16px Rajdhani';ctx.textAlign='center';ctx.fillText('🏸',cx,cy+5);
}}
function spin(){{
  if(spinning||rem.length===0)return;
  spinning=true;document.getElementById('spinBtn').disabled=true;
  document.getElementById('result').textContent='🎡 Spinning...';
  const extra=(5+Math.random()*5)*2*Math.PI,stop=Math.random()*2*Math.PI,total=extra+stop;
  const dur=4000,t0=performance.now(),a0=cur;
  function anim(now){{
    const el=now-t0,t=Math.min(el/dur,1),e=1-Math.pow(1-t,4);
    cur=a0+total*e;draw(cur);
    if(t<1){{requestAnimationFrame(anim);return;}}
    spinning=false;
    const disp=rem,arc=2*Math.PI/disp.length;
    const norm=(((-cur)%(2*Math.PI))+2*Math.PI)%(2*Math.PI);
    const idx=Math.floor(norm/arc)%disp.length;
    const w=disp[idx];
    document.getElementById('result').textContent='🏸 Selected: '+w;
    rem=rem.filter(n=>n!==w);
    setTimeout(()=>{{
      if(rem.length>0){{document.getElementById('spinBtn').disabled=false;document.getElementById('spinBtn').textContent='🎡 SPIN AGAIN ('+rem.length+' left)';}}
      else{{document.getElementById('spinBtn').textContent='✅ All Players Spun!';document.getElementById('result').textContent='🎉 All players shown! Click Auto-Assign to save teams.';}}
      draw(cur);
    }},1500);
  }}
  requestAnimationFrame(anim);
}}
draw(0);
</script></body></html>"""

# ─── PAGES ────────────────────────────────────────────────────────────────────

LIMITS = {"player": 14, "referee": 2, "admin": 1}

def page_signup():
    state = get_state()
    if state["signups_frozen"]:
        st.error("🔒 All slots filled — signups are closed! Please login.")
        return
    counts = count_by_role()
    available = [r for r in ("admin","referee","player") if counts[r] < LIMITS[r]]
    if not available:
        update_state(signups_frozen=True)
        st.error("🔒 All slots are now full!")
        return

    st.markdown('<div class="section-title">📝 SIGN UP</div>', unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    c1.metric("Players", f"{counts['player']}/14")
    c2.metric("Referees", f"{counts['referee']}/2")
    c3.metric("Admin", f"{counts['admin']}/1")
    st.markdown("---")

    with st.form("signup", clear_on_submit=True):
        name = st.text_input("Full Name")
        mobile = st.text_input("Mobile Number (10 digits — this is your username)", max_chars=10)
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")
        role = st.selectbox("Category", available, format_func=lambda x: {"player":"🏸 Player","referee":"🎯 Referee","admin":"⚙️ Admin"}[x])
        submitted = st.form_submit_button("🚀 REGISTER", use_container_width=True)

    if submitted:
        errs = []
        if not name.strip(): errs.append("Name required.")
        if not mobile.isdigit() or len(mobile) != 10: errs.append("Valid 10-digit mobile required.")
        if len(password) < 6: errs.append("Password min 6 chars.")
        if password != confirm: errs.append("Passwords don't match.")
        if errs:
            for e in errs: st.error(e)
        else:
            user, err = signup_user(name.strip(), mobile.strip(), password, role)
            if err:
                st.error("❌ Mobile already registered!" if "unique" in err.lower() or "duplicate" in err.lower() else f"❌ {err}")
            else:
                st.success(f"✅ Registered as **{role}**! Please login.")
                new_counts = count_by_role()
                if new_counts["player"] >= 14 and new_counts["referee"] >= 2 and new_counts["admin"] >= 1:
                    update_state(signups_frozen=True)
                st.rerun()

def page_login():
    st.markdown('<div class="section-title">🔐 LOGIN</div>', unsafe_allow_html=True)
    with st.form("login"):
        mobile = st.text_input("Mobile Number")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("🔑 LOGIN", use_container_width=True)
    if submitted:
        if not mobile or not password:
            st.error("Enter both fields.")
        else:
            user, err = login_user(mobile.strip(), password)
            if err: st.error(f"❌ {err}")
            else:
                st.session_state.user = user
                st.success(f"✅ Welcome, **{user['name']}**!")
                st.rerun()

def page_admin():
    state = get_state()
    st.markdown('<div class="section-title">⚙️ ADMIN DASHBOARD</div>', unsafe_allow_html=True)
    tabs = st.tabs(["👥 Users","🎡 Teams","🏟️ Courts","📅 Schedule","🏆 Leaderboard","🥊 Knockout"])

    # USERS
    with tabs[0]:
        users = get_all_users()
        players = [u for u in users if u["role"]=="player"]
        refs = [u for u in users if u["role"]=="referee"]
        admins = [u for u in users if u["role"]=="admin"]
        c1,c2,c3 = st.columns(3)
        with c1:
            st.markdown(f"**🏸 Players ({len(players)}/14)**")
            for p in players:
                st.markdown(f"<div class='match-row' style='background:#0d1a1a;border-left:3px solid #00e5ff'>"
                            f"<span style='color:#00e5ff'>👤</span> {p['name']}<br>"
                            f"<span style='color:#8888aa;font-size:12px'>{p['mobile']}</span></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"**🎯 Referees ({len(refs)}/2)**")
            for r in refs:
                st.markdown(f"<div class='match-row' style='background:#1a1500;border-left:3px solid #ffb800'>"
                            f"<span style='color:#ffb800'>🎯</span> {r['name']}<br>"
                            f"<span style='color:#8888aa;font-size:12px'>{r['mobile']}</span></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"**⚙️ Admin ({len(admins)}/1)**")
            for a in admins:
                st.markdown(f"<div class='match-row' style='background:#1a0a0a;border-left:3px solid #ff3c3c'>"
                            f"<span style='color:#ff3c3c'>⚙️</span> {a['name']}<br>"
                            f"<span style='color:#8888aa;font-size:12px'>{a['mobile']}</span></div>", unsafe_allow_html=True)
        needed = []
        if len(players)<14: needed.append(f"{14-len(players)} player(s)")
        if len(refs)<2: needed.append(f"{2-len(refs)} referee(s)")
        if needed: st.warning(f"⚠️ Still waiting for: {', '.join(needed)}")
        else: st.success("✅ All 17 participants registered!")

    # TEAMS
    with tabs[1]:
        teams = get_teams()
        if state["teams_assigned"] and teams:
            st.success("✅ Teams already assigned!")
            _show_teams_grid(teams)
        else:
            users = get_all_users()
            players = [u for u in users if u["role"]=="player"]
            if len(players) < 14:
                st.warning(f"Need 14 players. Currently {len(players)}.")
            else:
                st.markdown("### 🎡 Spin the Wheel")
                st.info("The wheel shows all 14 players. Press SPIN to cycle through — then click **Auto-Assign** to save 7 random teams.")
                components.html(spin_wheel_html([p["name"] for p in players]), height=580)
                st.markdown("---")
                if st.button("⚡ AUTO-ASSIGN TEAMS (Random Draw)", type="primary", use_container_width=True):
                    shuffled = random.sample(players, len(players))
                    assignments = [{"name": TEAM_LABELS[i], "player1_id": shuffled[i*2]["id"], "player2_id": shuffled[i*2+1]["id"]} for i in range(7)]
                    create_teams(assignments)
                    update_state(teams_assigned=True)
                    st.success("✅ Teams assigned!")
                    st.rerun()

    # COURTS
    with tabs[2]:
        st.markdown("### 🏟️ Assign Referees to Courts")
        courts = get_courts()
        users = get_all_users()
        refs = [u for u in users if u["role"]=="referee"]
        ref_opts = {r["id"]: r["name"] for r in refs}
        for court in courts:
            ref_info = court.get("ref") or {}
            current = ref_info.get("name","Unassigned") if isinstance(ref_info,dict) else "Unassigned"
            c1,c2,c3 = st.columns([1,2,1])
            c1.markdown(f"**🏟️ {court['name']}**")
            c2.markdown(f"Current: `{current}`")
            with c3:
                sel = st.selectbox(f"Assign", list(ref_opts.keys()), format_func=lambda x: ref_opts[x], key=f"c_{court['id']}")
                if st.button("✅ Assign", key=f"b_{court['id']}"):
                    assign_referee_to_court(court["id"], sel)
                    st.success(f"✅ {ref_opts[sel]} → {court['name']}")
                    st.rerun()
        if all(c.get("referee_id") for c in courts):
            st.success("✅ Both courts assigned!")

    # SCHEDULE
    with tabs[3]:
        st.markdown("### 📅 Group Stage Schedule")
        if not state["teams_assigned"]:
            st.warning("Assign teams first.")
        else:
            existing = get_matches("group")
            if not existing:
                courts = get_courts()
                if not all(c.get("referee_id") for c in courts):
                    st.warning("Assign referees to courts first.")
                else:
                    st.info("21 matches will be generated across both courts. No team plays 3+ back-to-back.")
                    if st.button("🗓️ GENERATE MATCH SCHEDULE", type="primary"):
                        court_names = [c["name"] for c in courts]
                        court_map = {c["name"]: c for c in courts}
                        team_map = {t["name"]: t["id"] for t in get_teams_simple()}
                        sched = build_schedule(TEAM_LABELS, court_names)
                        matches = [{"match_number": i+1, "stage": "group",
                                    "team1_id": team_map[s["team1"]], "team2_id": team_map[s["team2"]],
                                    "court_id": court_map[s["court_name"]]["id"],
                                    "referee_id": court_map[s["court_name"]].get("referee_id"),
                                    "status": "pending", "match_order": i+1} for i,s in enumerate(sched)]
                        create_matches(matches)
                        update_state(phase="group_stage", schedule_generated=True)
                        st.success("✅ 21 matches generated!")
                        st.rerun()
            else:
                done = sum(1 for m in existing if m["status"]=="completed")
                st.info(f"Progress: **{done}/21** completed")
                for i in range(0, len(existing), 2):
                    slot = existing[i:i+2]
                    st.markdown(f"<div style='color:#8888aa;font-family:Space Mono,monospace;font-size:10px;letter-spacing:3px;margin:10px 0 4px'>SLOT {i//2+1}</div>", unsafe_allow_html=True)
                    for m in slot: render_match_row(m)
                if done == 21 and not state["group_stage_complete"]:
                    update_state(group_stage_complete=True)
                    st.success("🎉 Group stage complete!")

    # LEADERBOARD
    with tabs[4]:
        st.markdown("### 🏆 Group Stage Leaderboard")
        rows = get_leaderboard()
        if not rows: st.info("No data yet.")
        else: render_leaderboard(rows)

    # KNOCKOUT
    with tabs[5]:
        st.markdown("### 🥊 Knockout Stage")
        if not state["group_stage_complete"]:
            all_group = get_matches("group")
            done = sum(1 for m in all_group if m["status"]=="completed")
            st.warning(f"Group stage not complete. ({done}/21 done)")
            return
        sf = get_matches("semifinal")
        tp = get_matches("third_place")
        fn = get_matches("final")
        if not sf:
            top4, _ = get_qualified_teams()
            st.markdown("### Top 4 Qualified Teams")
            for i,t in enumerate(top4):
                seed = ["1st 🥇","2nd 🥈","3rd 🥉","4th 🏅"][i]
                diff = t["score_diff"]; diff_s = f"+{diff}" if diff>0 else str(diff)
                st.markdown(f"<div class='match-row lb-qualified'><span style='color:#ffb800;font-family:Bebas Neue,cursive;font-size:20px'>{seed}</span><span style='font-weight:700;font-size:18px;margin-left:16px'>{t['team_name']}</span><span style='color:#8888aa;font-size:13px;margin-left:16px'>W:{t['won']} | Diff:{diff_s}</span></div>", unsafe_allow_html=True)
            st.info("**SF1:** Seed 1 vs Seed 4 | **SF2:** Seed 2 vs Seed 3")
            if st.button("🥊 CREATE SEMIFINAL MATCHES", type="primary"):
                create_knockout_matches(top4)
                update_state(phase="semifinals")
                st.rerun()
        else:
            st.markdown("#### Semifinals")
            for m in sf: render_match_row(m)
            sf_done = all(m["status"]=="completed" for m in sf)
            if sf_done and not tp and not fn:
                if st.button("🏆 CREATE FINAL & 3RD PLACE", type="primary"):
                    create_final_matches(sf)
                    update_state(semifinals_complete=True, phase="final")
                    st.rerun()
            if tp:
                st.markdown("#### 🥉 3rd Place Match")
                for m in tp: render_match_row(m)
            if fn:
                st.markdown("#### 🏆 GRAND FINAL")
                for m in fn: render_match_row(m)
                if all(m["status"]=="completed" for m in fn):
                    w = (fn[0].get("winner") or {}).get("name","")
                    if w:
                        st.balloons()
                        st.markdown(f"<div style='text-align:center;padding:32px;background:linear-gradient(135deg,#1a1200,#2a1a00);border:2px solid #ffb800;margin-top:16px'><div style='font-family:Bebas Neue,cursive;font-size:14px;letter-spacing:8px;color:#ffb800'>🏆 TOURNAMENT CHAMPION 🏆</div><div style='font-family:Bebas Neue,cursive;font-size:56px;background:linear-gradient(135deg,#ffd700,#ffb800);-webkit-background-clip:text;-webkit-text-fill-color:transparent'>{w}</div></div>", unsafe_allow_html=True)
                        update_state(phase="completed")

def page_referee():
    user = st.session_state.user
    st.markdown(f'<div class="section-title">🎯 REFEREE — {user["name"]}</div>', unsafe_allow_html=True)
    match, court = get_referee_match(user["id"])
    if court is None:
        st.warning("⚠️ You haven't been assigned to a court yet. Wait for Admin.")
        return
    st.markdown(f"<div style='background:#1a1500;border-left:3px solid #ffb800;padding:12px 20px;margin-bottom:20px'><span style='color:#8888aa;font-size:11px;font-family:Space Mono,monospace'>ASSIGNED COURT</span><br><span style='font-family:Bebas Neue,cursive;font-size:28px;letter-spacing:4px;color:#ffb800'>🏟️ {court['name']}</span></div>", unsafe_allow_html=True)
    if match is None:
        st.success("✅ No pending matches on your court right now.")
        return
    t1 = match.get("team1") or {}
    t2 = match.get("team2") or {}
    status = match.get("status","pending")
    s1, s2 = match.get("score_team1",0), match.get("score_team2",0)
    st.markdown(f"<div style='text-align:center;padding:8px 0 16px'><span style='color:#8888aa;font-family:Space Mono,monospace;font-size:11px'>MATCH #{match['match_number']} • {match.get('stage','').upper().replace('_',' ')}</span></div>", unsafe_allow_html=True)
    c1,cv,c2 = st.columns([2,1,2])
    with c1:
        st.markdown(f"<div style='text-align:center;background:#1a0a0a;border:1px solid rgba(255,60,60,0.3);padding:20px'><div style='font-family:Bebas Neue,cursive;font-size:20px;letter-spacing:3px;color:#ff3c3c'>{t1.get('name','Team 1')}</div><div style='font-family:Bebas Neue,cursive;font-size:72px;color:#ff3c3c;line-height:1'>{s1}</div></div>", unsafe_allow_html=True)
    with cv:
        st.markdown("<div style='text-align:center;padding:28px 0'><div style='font-family:Bebas Neue,cursive;font-size:28px;color:#8888aa;letter-spacing:4px'>VS</div><div style='font-size:11px;color:#8888aa;font-family:Space Mono,monospace;margin-top:8px'>FIRST TO 15</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div style='text-align:center;background:#0a0a1a;border:1px solid rgba(0,229,255,0.3);padding:20px'><div style='font-family:Bebas Neue,cursive;font-size:20px;letter-spacing:3px;color:#00e5ff'>{t2.get('name','Team 2')}</div><div style='font-family:Bebas Neue,cursive;font-size:72px;color:#00e5ff;line-height:1'>{s2}</div></div>", unsafe_allow_html=True)
    st.markdown("---")
    if status == "completed":
        w = match.get("winner") or {}
        st.success(f"🏆 Match Complete! Winner: **{w.get('name','?')}**")
        if match.get("stage")=="group" and check_group_stage_complete():
            update_state(group_stage_complete=True)
        if st.button("➡️ Next Match"): st.rerun()
        return
    if status == "pending":
        if st.button("🚀 START MATCH", type="primary", use_container_width=True):
            start_match(match["id"]); st.rerun()
        return
    # LIVE
    st.markdown("<div style='text-align:center;padding:8px;background:rgba(255,60,60,0.1);border:1px solid rgba(255,60,60,0.3);margin-bottom:16px'><span style='color:#ff3c3c;font-family:Space Mono,monospace;font-size:12px;letter-spacing:3px'>● LIVE MATCH</span></div>", unsafe_allow_html=True)
    b1,_,b2 = st.columns([2,1,2])
    with b1:
        if st.button(f"➕ +1 for {t1.get('name','Team 1')}", type="primary", use_container_width=True, key="s1"):
            won,_ = add_score(match["id"],"score_team1",s1,t1.get("id"),t2.get("id"))
            if won: st.balloons(); st.success(f"🏆 {t1.get('name')} WINS!")
            st.rerun()
    with b2:
        if st.button(f"➕ +1 for {t2.get('name','Team 2')}", type="primary", use_container_width=True, key="s2"):
            won,_ = add_score(match["id"],"score_team2",s2,t1.get("id"),t2.get("id"))
            if won: st.balloons(); st.success(f"🏆 {t2.get('name')} WINS!")
            st.rerun()
    st.markdown("#### Score Progress (first to 15 wins)")
    pc1,pc2 = st.columns(2)
    with pc1:
        st.markdown(f"**{t1.get('name')}** — {s1}/15")
        st.progress(min(s1/15,1.0))
    with pc2:
        st.markdown(f"**{t2.get('name')}** — {s2}/15")
        st.progress(min(s2/15,1.0))
    time.sleep(2); st.rerun()

def page_player():
    user = st.session_state.user
    st.markdown(f'<div class="section-title">🏸 PLAYER — {user["name"]}</div>', unsafe_allow_html=True)
    teams = get_teams()
    my_team = None
    for t in teams:
        p1 = t.get("p1") or {}; p2 = t.get("p2") or {}
        if user["id"] in (p1.get("id"), p2.get("id")):
            my_team = t; break
    tabs = st.tabs(["🔴 Live Matches","📅 My Schedule","🏆 Leaderboard","👥 All Teams"])
    with tabs[0]:
        st.markdown("### 🔴 Live Matches")
        live = get_live_matches()
        if not live:
            st.info("⏳ No live matches right now.")
        else:
            cols = st.columns(min(len(live),2))
            for i,m in enumerate(live[:2]):
                t1=m.get("team1") or {}; t2=m.get("team2") or {}; court=m.get("court") or {}
                with cols[i]:
                    st.markdown(f"<div style='background:#0d0d1a;border:1px solid rgba(255,60,60,0.4);border-top:3px solid #ff3c3c;padding:20px;text-align:center'><div style='color:#00e5ff;font-family:Space Mono,monospace;font-size:11px;letter-spacing:3px;margin-bottom:12px'>🏟️ {court.get('name','?')} • #{m['match_number']}</div><div style='display:flex;justify-content:space-around;align-items:center'><div><div style='font-family:Bebas Neue,cursive;font-size:20px;color:#ff3c3c'>{t1.get('name','?')}</div><div style='font-family:Bebas Neue,cursive;font-size:64px;color:#ff3c3c;line-height:1'>{m['score_team1']}</div></div><div style='font-family:Bebas Neue,cursive;font-size:24px;color:#8888aa'>VS</div><div><div style='font-family:Bebas Neue,cursive;font-size:20px;color:#00e5ff'>{t2.get('name','?')}</div><div style='font-family:Bebas Neue,cursive;font-size:64px;color:#00e5ff;line-height:1'>{m['score_team2']}</div></div></div><div style='margin-top:12px;color:#ff3c3c;font-family:Space Mono,monospace;font-size:10px;letter-spacing:3px'>● LIVE</div></div>", unsafe_allow_html=True)
        st.caption("🔄 Auto-refreshes every 3s")
        time.sleep(3); st.rerun()
    with tabs[1]:
        if not my_team:
            st.info("Teams not assigned yet.")
        else:
            st.markdown(f"### Your Team: **{my_team['name']}**")
            all_matches = get_matches()
            my_matches = sorted([m for m in all_matches if (m.get("team1") or {}).get("id")==my_team["id"] or (m.get("team2") or {}).get("id")==my_team["id"]], key=lambda x: x["match_order"])
            if not my_matches: st.info("Schedule not generated yet.")
            else:
                for m in my_matches: render_match_row(m, my_team["id"])
                won = sum(1 for m in my_matches if (m.get("winner") or {}).get("id")==my_team["id"] and m["status"]=="completed")
                played = sum(1 for m in my_matches if m["status"]=="completed")
                st.markdown(f"**Record:** {won}W / {played-won}L from {played} played")
    with tabs[2]:
        rows = get_leaderboard()
        if not rows: st.info("No data yet.")
        else: render_leaderboard(rows, my_team["name"] if my_team else None)
    with tabs[3]:
        if not teams: st.info("Teams not assigned yet.")
        else:
            cols = st.columns(4)
            for i,t in enumerate(teams):
                p1=t.get("p1") or {}; p2=t.get("p2") or {}
                color = TEAM_COLORS[i%len(TEAM_COLORS)]
                is_mine = my_team and t["name"]==my_team["name"]
                with cols[i%4]:
                    mine_border = "outline:2px solid #ffb800;" if is_mine else ""
                    mine_star = "&#11088;" if is_mine else ""
                    p1n = p1.get("name", "?")
                    p2n = p2.get("name", "?")
                    tn = t["name"]
                    html_card = (
                        f"<div style='background:#1a1a25;border:1px solid rgba(255,255,255,0.08);"
                        f"border-left:3px solid {color};padding:14px;margin-bottom:12px;{mine_border}>"
                        f"<div style='font-family:Bebas Neue,cursive;font-size:22px;letter-spacing:3px;color:{color}'>"
                        f"{tn} {mine_star}</div>"
                        f"<div style='color:#e0e0f0;font-size:14px;margin-top:6px'>&#127992; {p1n}</div>"
                        f"<div style='color:#e0e0f0;font-size:14px'>&#127992; {p2n}</div></div>"
                    )
                    st.markdown(html_card, unsafe_allow_html=True)
                    html = (
                        f"<div style='background:#1a1a25;border:1px solid rgba(255,255,255,0.08);"
                        f"border-left:3px solid {color};padding:14px;margin-bottom:12px;{mine_border}'>"
                        f"<div style='font-family:Bebas Neue,cursive;font-size:22px;letter-spacing:3px;color:{color}'>"
                        f"{tn} {mine_star}</div>"
                        f"<div style='color:#e0e0f0;font-size:14px;margin-top:6px'>&#127992; {p1n}</div>"
                        f"<div style='color:#e0e0f0;font-size:14px'>&#127992; {p2n}</div></div>"
                    )
                    st.markdown(html, unsafe_allow_html=True)

def _show_teams_grid(teams):
    cols = st.columns(4)
    for i,t in enumerate(teams):
        p1=t.get("p1") or {}; p2=t.get("p2") or {}
        color = TEAM_COLORS[i%len(TEAM_COLORS)]
        with cols[i%4]:
            st.markdown(f"<div style='background:#1a1a25;border:1px solid rgba(255,255,255,0.08);border-left:3px solid {color};padding:14px;margin-bottom:12px'><div style='font-family:Bebas Neue,cursive;font-size:22px;letter-spacing:3px;color:{color}'>{t['name']}</div><div style='color:#e0e0f0;font-size:14px;margin-top:6px'>🏸 {p1.get('name','?')}</div><div style='color:#e0e0f0;font-size:14px'>🏸 {p2.get('name','?')}</div></div>", unsafe_allow_html=True)

# ─── Session Init ─────────────────────────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("""<div class="hero-header">
  <div class="hero-title">🏸 SERVE &amp; SMASH</div>
  <div class="hero-sub">Badminton Tournament Management System</div>
</div>""", unsafe_allow_html=True)

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏸 Navigation")
    try:
        state = get_state()
        counts = count_by_role()
        st.markdown(f"**Players:** {counts['player']}/14")
        st.markdown(f"**Referees:** {counts['referee']}/2")
        st.markdown(f"**Admin:** {counts['admin']}/1")
        st.markdown(f"**Phase:** `{state['phase'].upper()}`")
    except Exception as e:
        st.error(f"DB connection issue: {e}")
    st.markdown("---")
    if st.session_state.user:
        u = st.session_state.user
        st.success(f"✅ **{u['name']}**\n`{u['role'].upper()}`")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.rerun()
    else:
        st.info("Please sign up or log in.")

# ─── Router ───────────────────────────────────────────────────────────────────
user = st.session_state.user
if user is None:
    t1, t2 = st.tabs(["📝 SIGN UP", "🔐 LOGIN"])
    with t1: page_signup()
    with t2: page_login()
else:
    role = user["role"]
    if role == "admin": page_admin()
    elif role == "referee": page_referee()
    elif role == "player": page_player()
