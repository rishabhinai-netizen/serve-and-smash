import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import time
from utils.db import (
    get_matches, get_leaderboard, get_teams, get_live_matches, get_state, get_all_users
)


def show_player():
    user = st.session_state.user
    st.markdown(f'<div class="section-title">🏸 PLAYER DASHBOARD — {user["name"]}</div>', unsafe_allow_html=True)

    state = get_state()

    # Find this player's team
    teams = get_teams()
    my_team = None
    for team in teams:
        p1 = team.get("users!teams_player1_id_fkey") or {}
        p2 = team.get("users!teams_player2_id_fkey") or {}
        p1_id = p1.get("id") if isinstance(p1, dict) else None
        p2_id = p2.get("id") if isinstance(p2, dict) else None
        if user["id"] in (p1_id, p2_id):
            my_team = team
            break

    tabs = st.tabs(["🔴 Live Matches", "📅 My Schedule", "🏆 Leaderboard", "👥 All Teams"])

    # ─── LIVE MATCHES ─────────────────────────────────────────────────────────
    with tabs[0]:
        st.markdown("### 🔴 Live Matches — Both Courts")
        
        live = get_live_matches()
        if not live:
            st.info("⏳ No matches currently live. Check back soon!")
        else:
            cols = st.columns(len(live)) if len(live) > 1 else [st.container()]
            for i, m in enumerate(live[:2]):
                t1 = m.get("team1", {}) or {}
                t2 = m.get("team2", {}) or {}
                court = m.get("court", {}) or {}
                s1 = m.get("score_team1", 0)
                s2 = m.get("score_team2", 0)
                
                with (cols[i] if len(live) > 1 else cols[0]):
                    st.markdown(f"""
                    <div style='background:#0d0d1a;border:1px solid rgba(255,60,60,0.4);
                                border-top:3px solid #ff3c3c;padding:20px;text-align:center;'>
                        <div style='color:#00e5ff;font-family:Space Mono,monospace;font-size:11px;
                                    letter-spacing:3px;margin-bottom:12px;'>
                            🏟️ {court.get('name','?')} • MATCH #{m['match_number']}
                        </div>
                        <div style='display:flex;justify-content:space-between;align-items:center;'>
                            <div>
                                <div style='font-family:Bebas Neue,cursive;font-size:20px;
                                            letter-spacing:3px;color:#ff3c3c;'>{t1.get('name','?')}</div>
                                <div style='font-family:Bebas Neue,cursive;font-size:64px;
                                            color:#ff3c3c;line-height:1;'>{s1}</div>
                            </div>
                            <div style='font-family:Bebas Neue,cursive;font-size:24px;
                                        color:#8888aa;letter-spacing:4px;'>VS</div>
                            <div>
                                <div style='font-family:Bebas Neue,cursive;font-size:20px;
                                            letter-spacing:3px;color:#00e5ff;'>{t2.get('name','?')}</div>
                                <div style='font-family:Bebas Neue,cursive;font-size:64px;
                                            color:#00e5ff;line-height:1;'>{s2}</div>
                            </div>
                        </div>
                        <div style='margin-top:12px;'>
                            <span style='color:#ff3c3c;font-family:Space Mono,monospace;
                                         font-size:10px;letter-spacing:3px;'>● LIVE</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.caption("🔄 Auto-refreshes every 3 seconds")
        time.sleep(3)
        st.rerun()

    # ─── MY SCHEDULE ──────────────────────────────────────────────────────────
    with tabs[1]:
        if not my_team:
            st.info("⏳ Teams have not been assigned yet. Check back after the Admin spins the wheel!")
        else:
            st.markdown(f"### Your Team: **{my_team['name']}**")
            
            all_matches = get_matches()
            my_matches = [
                m for m in all_matches
                if (m.get("team1", {}) or {}).get("id") == my_team["id"] or
                   (m.get("team2", {}) or {}).get("id") == my_team["id"]
            ]
            my_matches = sorted(my_matches, key=lambda x: x["match_order"])

            if not my_matches:
                st.info("Schedule not generated yet.")
            else:
                for m in my_matches:
                    t1 = m.get("team1", {}) or {}
                    t2 = m.get("team2", {}) or {}
                    court = m.get("court", {}) or {}
                    w = m.get("winner", {}) or {}
                    status = m.get("status", "pending")
                    
                    is_my_t1 = t1.get("id") == my_team["id"]
                    my_score = m["score_team1"] if is_my_t1 else m["score_team2"]
                    opp_score = m["score_team2"] if is_my_t1 else m["score_team1"]
                    opp = t2 if is_my_t1 else t1
                    
                    result = ""
                    result_color = "#8888aa"
                    if status == "completed":
                        if w.get("id") == my_team["id"]:
                            result = "WIN 🏆"
                            result_color = "#22c55e"
                        else:
                            result = "LOSS"
                            result_color = "#ef4444"
                    
                    stage_label = {"group":"Group","semifinal":"SF","third_place":"3rd Place","final":"Final"}.get(m.get("stage",""),"")
                    
                    st.markdown(f"""
                    <div class='match-row {"match-live" if status=="live" else "match-done" if status=="completed" else ""}'>
                        <div>
                            <span style='color:#8888aa;font-family:Space Mono,monospace;font-size:10px;'>
                                #{m['match_number']} • {stage_label} • {court.get('name','?')}
                            </span><br>
                            <span style='font-weight:700;font-size:16px;'>
                                <span style='color:#ffb800;'>{my_team['name']}</span>
                                <span style='color:#8888aa;margin:0 8px;'>vs</span>
                                {opp.get('name','?')}
                            </span>
                        </div>
                        <div style='text-align:right;'>
                            {"<span style='font-family:Space Mono,monospace;font-size:18px;font-weight:700;'>" + str(my_score) + " — " + str(opp_score) + "</span>" if status != "pending" else "<span style='color:#8888aa;font-size:13px;'>UPCOMING</span>"}
                            {"<br><span style='font-family:Space Mono,monospace;font-size:11px;color:" + result_color + ";letter-spacing:2px;'>" + result + "</span>" if result else ""}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                # Stats
                if my_matches:
                    won = sum(1 for m in my_matches if (m.get("winner") or {}).get("id") == my_team["id"] and m["status"] == "completed")
                    played = sum(1 for m in my_matches if m["status"] == "completed")
                    st.markdown(f"**Record:** {won}W / {played - won}L from {played} matches played")

    # ─── LEADERBOARD ──────────────────────────────────────────────────────────
    with tabs[2]:
        st.markdown("### 🏆 Group Stage Leaderboard")
        rows = get_leaderboard()
        if not rows:
            st.info("No match data yet.")
        else:
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
                is_mine = my_team and row["team_name"] == my_team["name"]
                diff = row["score_diff"]
                diff_str = f"+{diff}" if diff > 0 else str(diff)
                diff_color = "#22c55e" if diff > 0 else "#ef4444" if diff < 0 else "#8888aa"
                highlight = "background:#1a1a00;border:1px solid #ffb800;" if is_mine else ""
                
                st.markdown(f"""
                <div class='lb-row {qualified}' style='{highlight}'>
                    <div style='font-size:18px'>{icon}</div>
                    <div style='font-weight:700;{"color:#ffb800;" if is_mine else ""}'>{row['team_name']} {"⭐" if is_mine else ""}</div>
                    <div style='color:#8888aa'>{row['matches_played']}</div>
                    <div style='color:#22c55e;font-weight:700'>{row['won']}</div>
                    <div style='color:#ef4444'>{row['lost']}</div>
                    <div style='color:#00e5ff'>{row['score_for']}</div>
                    <div style='color:#ff8888'>{row['score_against']}</div>
                    <div style='color:{diff_color};font-weight:700'>{diff_str}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.caption("⭐ = Your team | 🏅 Top 4 qualify for Semifinals | SF = Score For | SA = Score Against")

    # ─── ALL TEAMS ────────────────────────────────────────────────────────────
    with tabs[3]:
        st.markdown("### 👥 All Teams")
        if not teams:
            st.info("Teams not assigned yet.")
        else:
            cols = st.columns(4)
            colors = ["#ff3c3c","#ffb800","#00e5ff","#a855f7","#22c55e","#f97316","#ec4899"]
            for i, team in enumerate(teams):
                p1 = team.get("users!teams_player1_id_fkey") or {}
                p2 = team.get("users!teams_player2_id_fkey") or {}
                p1_name = p1.get("name","?") if isinstance(p1,dict) else "?"
                p2_name = p2.get("name","?") if isinstance(p2,dict) else "?"
                color = colors[i % len(colors)]
                is_mine = my_team and team["name"] == my_team["name"]
                with cols[i % 4]:
                    st.markdown(f"""
                    <div style='background:#1a1a25;border:1px solid rgba(255,255,255,0.08);
                                border-left:3px solid {color};padding:14px;margin-bottom:12px;
                                {"outline:2px solid #ffb800;" if is_mine else ""}'>
                        <div style='font-family:Bebas Neue,cursive;font-size:22px;letter-spacing:3px;color:{color};'>
                            {team['name']} {"⭐" if is_mine else ""}
                        </div>
                        <div style='color:#e0e0f0;margin-top:6px;font-size:14px;'>🏸 {p1_name}</div>
                        <div style='color:#e0e0f0;font-size:14px;'>🏸 {p2_name}</div>
                    </div>
                    """, unsafe_allow_html=True)
