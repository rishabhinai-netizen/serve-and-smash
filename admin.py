import streamlit as st
import streamlit.components.v1 as components
import json
import random
from utils.db import (
    get_state, update_state, get_all_users, get_teams, create_teams,
    get_courts, assign_referee_to_court, get_matches, create_matches,
    get_leaderboard, get_qualified_teams, check_group_stage_complete,
    create_knockout_matches, create_final_matches, get_teams_simple
)
from utils.schedule import build_court_schedule, TEAM_NAMES

TEAM_LABELS = ["Team A","Team B","Team C","Team D","Team E","Team F","Team G"]
TEAM_COLORS = ["#ff3c3c","#ffb800","#00e5ff","#a855f7","#22c55e","#f97316","#ec4899"]


def show_admin():
    state = get_state()
    st.markdown('<div class="section-title">⚙️ ADMIN DASHBOARD</div>', unsafe_allow_html=True)

    # Phase tabs
    phase = state["phase"]
    tabs = st.tabs(["👥 Users", "🎡 Team Assignment", "🏟️ Courts & Referees", "📅 Schedule", "🏆 Leaderboard", "🥊 Knockout"])

    # ─── USERS TAB ────────────────────────────────────────────────────────────
    with tabs[0]:
        st.markdown("### Registered Participants")
        users = get_all_users()
        players = [u for u in users if u["role"] == "player"]
        refs = [u for u in users if u["role"] == "referee"]
        admins = [u for u in users if u["role"] == "admin"]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**🏸 Players ({len(players)}/14)**")
            for p in players:
                st.markdown(f"<div class='match-row' style='background:#0d1a1a;border-left:3px solid #00e5ff'>"
                          f"<span style='color:#00e5ff'>👤</span> {p['name']}<br>"
                          f"<span style='color:#8888aa;font-size:12px'>{p['mobile']}</span></div>",
                          unsafe_allow_html=True)
        with col2:
            st.markdown(f"**🎯 Referees ({len(refs)}/2)**")
            for r in refs:
                st.markdown(f"<div class='match-row' style='background:#1a1500;border-left:3px solid #ffb800'>"
                          f"<span style='color:#ffb800'>🎯</span> {r['name']}<br>"
                          f"<span style='color:#8888aa;font-size:12px'>{r['mobile']}</span></div>",
                          unsafe_allow_html=True)
        with col3:
            st.markdown(f"**⚙️ Admin ({len(admins)}/1)**")
            for a in admins:
                st.markdown(f"<div class='match-row' style='background:#1a0a0a;border-left:3px solid #ff3c3c'>"
                          f"<span style='color:#ff3c3c'>⚙️</span> {a['name']}<br>"
                          f"<span style='color:#8888aa;font-size:12px'>{a['mobile']}</span></div>",
                          unsafe_allow_html=True)

        if len(players) < 14 or len(refs) < 2 or len(admins) < 1:
            needed = []
            if len(players) < 14: needed.append(f"{14 - len(players)} more player(s)")
            if len(refs) < 2: needed.append(f"{2 - len(refs)} more referee(s)")
            st.warning(f"⚠️ Waiting for: {', '.join(needed)}")
        else:
            st.success("✅ All 17 participants registered! Ready to assign teams.")

    # ─── TEAM ASSIGNMENT TAB ──────────────────────────────────────────────────
    with tabs[1]:
        teams = get_teams()

        if state["teams_assigned"] and teams:
            st.success("✅ Teams already assigned!")
            _show_teams(teams)
            return

        users = get_all_users()
        players = [u for u in users if u["role"] == "player"]

        if len(players) < 14:
            st.warning(f"⚠️ Need 14 players. Currently {len(players)} registered.")
            return

        st.markdown("### 🎡 Spin the Wheel — Team Assignment")
        st.info("Press **SPIN** to randomly assign all 14 players into 7 teams of 2. The wheel will spin through all players!")

        player_names = [p["name"] for p in players]

        # Animated Spin Wheel via HTML/JS
        wheel_html = _build_wheel_html(player_names)
        result = components.html(wheel_html, height=600, scrolling=False)

        st.markdown("---")
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("⚡ AUTO-ASSIGN TEAMS (Randomize)", type="primary", use_container_width=True,
                        disabled=state["teams_assigned"]):
                _assign_teams(players)
                st.rerun()

        if state.get("teams_assigned"):
            teams = get_teams()
            _show_teams(teams)

    # ─── COURTS TAB ──────────────────────────────────────────────────────────
    with tabs[2]:
        st.markdown("### 🏟️ Assign Referees to Courts")
        courts = get_courts()
        users = get_all_users()
        refs = [u for u in users if u["role"] == "referee"]

        if not refs:
            st.warning("No referees registered yet.")
            return

        ref_options = {r["id"]: r["name"] for r in refs}
        
        for court in courts:
            current_ref = court.get("users", {})
            current_name = current_ref.get("name", "Unassigned") if current_ref else "Unassigned"
            
            col1, col2, col3 = st.columns([1, 2, 1])
            col1.markdown(f"**🏟️ {court['name']}**")
            col2.markdown(f"Current: `{current_name}`")
            
            with col3:
                selected = st.selectbox(
                    f"Assign to {court['name']}",
                    options=list(ref_options.keys()),
                    format_func=lambda x: ref_options[x],
                    key=f"court_{court['id']}"
                )
                if st.button(f"✅ Assign", key=f"btn_{court['id']}"):
                    assign_referee_to_court(court["id"], selected)
                    st.success(f"✅ {ref_options[selected]} assigned to {court['name']}")
                    st.rerun()

        courts = get_courts()
        all_assigned = all(c.get("referee_id") for c in courts)
        if all_assigned:
            st.success("✅ Both courts have referees assigned!")
        
    # ─── SCHEDULE TAB ─────────────────────────────────────────────────────────
    with tabs[3]:
        st.markdown("### 📅 Group Stage Schedule")
        
        if not state["teams_assigned"]:
            st.warning("⚠️ Assign teams first before generating schedule.")
            return

        existing = get_matches(stage="group")

        if not existing:
            courts = get_courts()
            all_courts_assigned = all(c.get("referee_id") for c in courts)
            if not all_courts_assigned:
                st.warning("⚠️ Please assign referees to both courts first.")
                return

            st.info("📋 **21 matches** will be generated (7 teams × 6 matches each = C(7,2) = 21 unique matchups).\n\nNo team will play more than 2 matches back-to-back.")

            if st.button("🗓️ GENERATE MATCH SCHEDULE", type="primary"):
                _generate_schedule(courts)
                update_state(phase="group_stage", schedule_generated=True)
                st.success("✅ Schedule generated! 21 group stage matches ready.")
                st.rerun()
        else:
            _show_schedule(existing, editable=False)

            # Check completion
            if check_group_stage_complete():
                st.success("🎉 All group stage matches complete! Check Leaderboard tab.")
                if not state["group_stage_complete"]:
                    update_state(group_stage_complete=True)
            else:
                done = sum(1 for m in existing if m["status"] == "completed")
                st.info(f"Progress: **{done}/21** matches completed")

    # ─── LEADERBOARD TAB ──────────────────────────────────────────────────────
    with tabs[4]:
        st.markdown("### 🏆 Group Stage Leaderboard")
        _show_leaderboard()

    # ─── KNOCKOUT TAB ─────────────────────────────────────────────────────────
    with tabs[5]:
        st.markdown("### 🥊 Knockout Stage")
        _show_knockout(state)


def _assign_teams(players):
    shuffled = random.sample(players, len(players))
    assignments = []
    for i, label in enumerate(TEAM_LABELS):
        p1 = shuffled[i * 2]
        p2 = shuffled[i * 2 + 1]
        assignments.append({
            "name": label,
            "player1_id": p1["id"],
            "player2_id": p2["id"]
        })
    create_teams(assignments)
    update_state(teams_assigned=True)
    st.success("✅ Teams assigned!")


def _generate_schedule(courts):
    court_names = [c["name"] for c in courts]
    court_map = {c["name"]: c for c in courts}
    teams_db = get_teams_simple()
    team_map = {t["name"]: t["id"] for t in teams_db}

    schedule = build_court_schedule(TEAM_LABELS, court_names)

    matches = []
    for i, slot in enumerate(schedule):
        court = court_map[slot["court_name"]]
        matches.append({
            "match_number": i + 1,
            "stage": "group",
            "team1_id": team_map[slot["team1"]],
            "team2_id": team_map[slot["team2"]],
            "court_id": court["id"],
            "referee_id": court.get("referee_id"),
            "status": "pending",
            "match_order": i + 1
        })
    create_matches(matches)


def _show_teams(teams):
    st.markdown("### 🏅 Assigned Teams")
    cols = st.columns(4)
    for i, team in enumerate(teams):
        with cols[i % 4]:
            p1 = team.get("users!teams_player1_id_fkey", {}) or {}
            p2 = team.get("users!teams_player2_id_fkey", {}) or {}
            p1_name = p1.get("name", "?") if isinstance(p1, dict) else "?"
            p2_name = p2.get("name", "?") if isinstance(p2, dict) else "?"
            color = TEAM_COLORS[i % len(TEAM_COLORS)]
            st.markdown(f"""
            <div style='background:#1a1a25;border:1px solid rgba(255,255,255,0.08);
                        border-left:3px solid {color};padding:14px;margin-bottom:12px;'>
                <div style='font-family:Bebas Neue,cursive;font-size:22px;letter-spacing:3px;color:{color};'>
                    {team['name']}
                </div>
                <div style='color:#e0e0f0;margin-top:6px;font-size:15px;'>🏸 {p1_name}</div>
                <div style='color:#e0e0f0;font-size:15px;'>🏸 {p2_name}</div>
            </div>
            """, unsafe_allow_html=True)


def _show_schedule(matches, editable=False):
    stage_order = {"group": 1, "semifinal": 2, "third_place": 3, "final": 4}
    matches = sorted(matches, key=lambda x: x["match_order"])
    
    # Group by concurrent slots (every 2)
    for i in range(0, len(matches), 2):
        slot = matches[i:i+2]
        label = f"⏱️ Slot {i//2 + 1}"
        st.markdown(f"<div style='color:#8888aa;font-family:Space Mono,monospace;font-size:11px;"
                   f"letter-spacing:3px;margin:12px 0 6px;'>{label}</div>", unsafe_allow_html=True)
        for m in slot:
            t1 = m.get("team1", {}) or {}
            t2 = m.get("team2", {}) or {}
            court = m.get("court", {}) or {}
            winner = m.get("winner", {}) or {}
            status = m.get("status", "pending")
            
            status_color = {"pending": "#8888aa", "live": "#ff3c3c", "completed": "#22c55e"}[status]
            status_icon = {"pending": "⏳", "live": "🔴 LIVE", "completed": "✅"}[status]

            score = ""
            if status in ("live", "completed"):
                score = f"<span style='font-family:Space Mono,monospace;font-size:14px;color:#ffb800'>"
                score += f"{m['score_team1']} — {m['score_team2']}</span>"
            
            win_label = ""
            if winner and winner.get("name"):
                win_label = f" 🏆 <span style='color:#22c55e'>{winner['name']}</span>"

            st.markdown(f"""
            <div class='match-row {"match-live" if status=="live" else "match-done" if status=="completed" else ""}'>
                <span style='color:#8888aa;font-family:Space Mono,monospace;font-size:11px;'>#{m['match_number']}</span>
                <span style='font-weight:700;font-size:16px;margin:0 12px;'>
                    {t1.get('name','?')} <span style='color:#8888aa;font-size:12px;'>VS</span> {t2.get('name','?')}
                    {win_label}
                </span>
                {score}
                <span style='color:#00e5ff;font-family:Space Mono,monospace;font-size:11px;margin-left:12px;'>
                    {court.get('name','?')}
                </span>
                <span style='color:{status_color};font-family:Space Mono,monospace;font-size:10px;margin-left:12px;'>
                    {status_icon}
                </span>
            </div>
            """, unsafe_allow_html=True)


def _show_leaderboard():
    rows = get_leaderboard()
    if not rows:
        st.info("No match data yet.")
        return

    rows.sort(key=lambda x: (x["won"], x["score_diff"], x["score_for"]), reverse=True)

    pos_icons = {1: "🥇", 2: "🥈", 3: "🥉", 4: "🏅"}

    st.markdown("""
    <div class='lb-row lb-header'>
        <div>POS</div><div>TEAM</div><div>MP</div><div>W</div><div>L</div>
        <div>SF</div><div>SA</div><div>DIFF</div>
    </div>
    """, unsafe_allow_html=True)

    for i, row in enumerate(rows):
        pos = i + 1
        qualified = "lb-qualified" if pos <= 4 else ""
        icon = pos_icons.get(pos, str(pos))
        diff = row["score_diff"]
        diff_color = "#22c55e" if diff > 0 else "#ef4444" if diff < 0 else "#8888aa"
        diff_str = f"+{diff}" if diff > 0 else str(diff)

        st.markdown(f"""
        <div class='lb-row {qualified}'>
            <div class='pos-{min(pos,5)}' style='font-size:18px'>{icon}</div>
            <div style='font-weight:700'>{row['team_name']}</div>
            <div style='color:#8888aa'>{row['matches_played']}</div>
            <div style='color:#22c55e;font-weight:700'>{row['won']}</div>
            <div style='color:#ef4444'>{row['lost']}</div>
            <div style='color:#00e5ff'>{row['score_for']}</div>
            <div style='color:#ff8888'>{row['score_against']}</div>
            <div style='color:{diff_color};font-weight:700'>{diff_str}</div>
        </div>
        """, unsafe_allow_html=True)

    st.caption("🏅 Top 4 qualify for Semifinals | SF = Score For | SA = Score Against")


def _show_knockout(state):
    from utils.db import get_matches
    
    if not state["group_stage_complete"]:
        all_group = get_matches("group")
        done = sum(1 for m in all_group if m["status"] == "completed")
        st.warning(f"⚠️ Group stage not complete yet. ({done}/21 done)")
        return

    sf_matches = get_matches("semifinal")
    tp_matches = get_matches("third_place")
    final_matches = get_matches("final")

    if not sf_matches:
        st.markdown("### 🏆 Top 4 Teams Qualified for Semifinals")
        top4, rest = get_qualified_teams()

        for i, team in enumerate(top4):
            seed = ["1st 🥇", "2nd 🥈", "3rd 🥉", "4th 🏅"][i]
            diff = team["score_diff"]
            diff_str = f"+{diff}" if diff > 0 else str(diff)
            st.markdown(f"""
            <div class='match-row lb-qualified'>
                <span style='color:#ffb800;font-family:Bebas Neue,cursive;font-size:20px;'>{seed}</span>
                <span style='font-weight:700;font-size:18px;margin-left:16px;'>{team['team_name']}</span>
                <span style='color:#8888aa;font-size:13px;margin-left:16px;'>
                    W:{team['won']} | Diff:{diff_str}
                </span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.info("**Semifinal 1:** 1st vs 4th | **Semifinal 2:** 2nd vs 3rd")
        if st.button("🥊 CREATE SEMIFINAL MATCHES", type="primary"):
            create_knockout_matches(top4)
            update_state(phase="semifinals")
            st.success("✅ Semifinal matches created!")
            st.rerun()
    else:
        st.markdown("### 🥊 Knockout Bracket")
        _show_schedule(sf_matches)

        sf_done = all(m["status"] == "completed" for m in sf_matches)

        if sf_done and not tp_matches and not final_matches:
            if st.button("🏆 CREATE FINAL & 3RD PLACE MATCH", type="primary"):
                create_final_matches(sf_matches)
                update_state(semifinals_complete=True, phase="final")
                st.success("✅ Final and 3rd place match created!")
                st.rerun()
        
        if tp_matches:
            st.markdown("### 🥉 3rd Place Match")
            _show_schedule(tp_matches)
        
        if final_matches:
            st.markdown("### 🏆 GRAND FINAL")
            _show_schedule(final_matches)

            if all(m["status"] == "completed" for m in final_matches):
                winner = final_matches[0].get("winner", {}) or {}
                if winner:
                    st.balloons()
                    st.markdown(f"""
                    <div style='text-align:center;padding:40px;background:linear-gradient(135deg,#1a1200,#2a1a00);
                                border:2px solid #ffb800;margin-top:20px;'>
                        <div style='font-family:Bebas Neue,cursive;font-size:16px;letter-spacing:8px;color:#ffb800;'>
                            🏆 TOURNAMENT CHAMPION 🏆
                        </div>
                        <div style='font-family:Bebas Neue,cursive;font-size:64px;letter-spacing:6px;
                                    background:linear-gradient(135deg,#ffd700,#ffb800);
                                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;'>
                            {winner.get('name','?')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    update_state(phase="completed")


def _build_wheel_html(player_names):
    """Build animated spin wheel HTML"""
    n = len(player_names)
    colors = [
        "#ff3c3c","#ffb800","#00e5ff","#a855f7","#22c55e","#f97316","#ec4899",
        "#06b6d4","#84cc16","#f43f5e","#8b5cf6","#14b8a6","#fb923c","#64748b"
    ]
    
    names_json = json.dumps(player_names)
    colors_json = json.dumps(colors[:n])

    return f"""
<!DOCTYPE html>
<html>
<head>
<style>
  body {{ background: #0a0a0f; display: flex; flex-direction: column; align-items: center;
          justify-content: center; height: 580px; margin: 0; font-family: 'Rajdhani', sans-serif; }}
  canvas {{ border-radius: 50%; box-shadow: 0 0 60px rgba(255,60,60,0.4); }}
  #spinBtn {{
    margin-top: 20px;
    background: linear-gradient(135deg, #ff3c3c, #ff6b6b);
    color: white; border: none; padding: 14px 48px;
    font-size: 20px; font-weight: 700; letter-spacing: 4px;
    cursor: pointer; clip-path: polygon(12px 0%,100% 0%,calc(100% - 12px) 100%,0% 100%);
    transition: all 0.2s;
  }}
  #spinBtn:hover {{ background: linear-gradient(135deg,#ff5555,#ff8888); transform:scale(1.05); }}
  #spinBtn:disabled {{ background: #333; cursor: not-allowed; transform: none; }}
  #result {{
    margin-top: 16px; font-size: 22px; font-weight: 700; color: #ffb800;
    letter-spacing: 3px; min-height: 30px; text-align: center;
  }}
  .pointer {{
    position: absolute; top: 50%; right: -24px; transform: translateY(-50%);
    width: 0; height: 0;
    border-top: 18px solid transparent;
    border-bottom: 18px solid transparent;
    border-left: 32px solid #ffb800;
  }}
  .wheel-wrap {{ position: relative; }}
</style>
</head>
<body>
<div class="wheel-wrap">
  <canvas id="wheel" width="340" height="340"></canvas>
  <div class="pointer"></div>
</div>
<button id="spinBtn" onclick="spin()">🎡 SPIN THE WHEEL</button>
<div id="result"></div>
<script>
const names = {names_json};
const colors = {colors_json};
const canvas = document.getElementById('wheel');
const ctx = canvas.getContext('2d');
const total = names.length;
const arc = (2 * Math.PI) / total;
let currentAngle = 0;
let spinning = false;
let remaining = [...names];

function drawWheel(angle) {{
  const cx = canvas.width / 2, cy = canvas.height / 2, r = cx - 4;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const displayNames = remaining.length > 0 ? remaining : names;
  const displayArc = (2 * Math.PI) / displayNames.length;
  for (let i = 0; i < displayNames.length; i++) {{
    const startAngle = angle + i * displayArc;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, r, startAngle, startAngle + displayArc);
    ctx.closePath();
    ctx.fillStyle = colors[i % colors.length];
    ctx.fill();
    ctx.strokeStyle = 'rgba(0,0,0,0.3)';
    ctx.lineWidth = 2;
    ctx.stroke();
    // Text
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(startAngle + displayArc / 2);
    ctx.textAlign = 'right';
    ctx.fillStyle = '#fff';
    ctx.font = 'bold ' + Math.min(13, 200/displayNames.length + 7) + 'px Rajdhani,sans-serif';
    ctx.shadowColor = 'rgba(0,0,0,0.8)';
    ctx.shadowBlur = 4;
    const name = displayNames[i];
    ctx.fillText(name.length > 12 ? name.substring(0,11)+'…' : name, r - 10, 5);
    ctx.restore();
  }}
  // Center circle
  ctx.beginPath();
  ctx.arc(cx, cy, 24, 0, 2 * Math.PI);
  ctx.fillStyle = '#0a0a0f';
  ctx.fill();
  ctx.strokeStyle = '#ffb800';
  ctx.lineWidth = 3;
  ctx.stroke();
  ctx.fillStyle = '#ffb800';
  ctx.font = 'bold 18px Rajdhani';
  ctx.textAlign = 'center';
  ctx.fillText('🏸', cx, cy + 6);
}}

function spin() {{
  if (spinning || remaining.length === 0) return;
  spinning = true;
  document.getElementById('spinBtn').disabled = true;
  document.getElementById('result').textContent = '🎡 Spinning...';
  
  const extraSpins = (5 + Math.random() * 5) * 2 * Math.PI;
  const stopAngle = Math.random() * 2 * Math.PI;
  const totalRotation = extraSpins + stopAngle;
  const duration = 4000;
  const startTime = performance.now();
  const startAngle = currentAngle;

  function animate(now) {{
    const elapsed = now - startTime;
    const t = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - t, 4);
    currentAngle = startAngle + totalRotation * eased;
    drawWheel(currentAngle);
    if (t < 1) {{
      requestAnimationFrame(animate);
    }} else {{
      spinning = false;
      // Determine winner
      const displayNames = remaining;
      const displayArc = (2 * Math.PI) / displayNames.length;
      // The pointer is at angle 0 (right side), wheel is rotated by currentAngle
      // Winner is at pointer position
      const normalized = (((-currentAngle) % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI);
      const idx = Math.floor(normalized / displayArc) % displayNames.length;
      const winner = displayNames[idx];
      document.getElementById('result').textContent = '🏸 Selected: ' + winner;
      remaining = remaining.filter(n => n !== winner);
      setTimeout(() => {{
        if (remaining.length > 0) {{
          document.getElementById('spinBtn').disabled = false;
          document.getElementById('spinBtn').textContent = '🎡 SPIN AGAIN (' + remaining.length + ' left)';
        }} else {{
          document.getElementById('spinBtn').textContent = '✅ All Players Assigned!';
          document.getElementById('result').textContent = '🎉 All players have been assigned!';
        }}
        drawWheel(currentAngle);
      }}, 1500);
    }}
  }}
  requestAnimationFrame(animate);
}}

drawWheel(0);
</script>
</body>
</html>
"""
