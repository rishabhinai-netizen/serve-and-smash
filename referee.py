import streamlit as st
import time
from utils.db import (
    get_referee_match, start_match, add_score,
    get_matches, update_state, check_group_stage_complete, get_state
)


def show_referee():
    user = st.session_state.user
    st.markdown(f'<div class="section-title">🎯 REFEREE PANEL — {user["name"]}</div>', unsafe_allow_html=True)

    state = get_state()

    # Find this referee's court and match
    match, court = get_referee_match(user["id"])

    if court is None:
        st.warning("⚠️ You have not been assigned to a court yet. Please wait for the Admin to assign you.")
        return

    st.markdown(f"""
    <div style='background:#1a1500;border:1px solid rgba(255,184,0,0.3);border-left:3px solid #ffb800;
                padding:12px 20px;margin-bottom:20px;'>
        <span style='color:#8888aa;font-family:Space Mono,monospace;font-size:11px;'>ASSIGNED COURT</span><br>
        <span style='font-family:Bebas Neue,cursive;font-size:28px;letter-spacing:4px;color:#ffb800;'>
            🏟️ {court['name']}
        </span>
    </div>
    """, unsafe_allow_html=True)

    if match is None:
        # Check if there are any completed matches for this court
        all_matches = get_matches()
        court_matches = [m for m in all_matches if m.get("court", {}) and m["court"].get("name") == court["name"]]
        done = [m for m in court_matches if m["status"] == "completed"]
        pending = [m for m in court_matches if m["status"] == "pending"]
        
        if not pending:
            st.success(f"✅ All matches on {court['name']} are completed! Great work.")
            if done:
                st.markdown("### 📋 Completed Matches")
                for m in done:
                    t1 = m.get("team1", {}) or {}
                    t2 = m.get("team2", {}) or {}
                    w = m.get("winner", {}) or {}
                    st.markdown(f"""
                    <div class='match-row match-done'>
                        #{m['match_number']} &nbsp;
                        <strong>{t1.get('name','?')}</strong> {m['score_team1']} — {m['score_team2']} 
                        <strong>{t2.get('name','?')}</strong>
                        &nbsp; 🏆 {w.get('name','?')}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info(f"⏳ Waiting for match to be assigned. Next up: **Match #{pending[0]['match_number']}**")
        return

    t1 = match.get("team1", {}) or {}
    t2 = match.get("team2", {}) or {}
    status = match.get("status", "pending")

    st.markdown(f"""
    <div style='text-align:center;padding:10px 0 20px;'>
        <div style='font-family:Space Mono,monospace;font-size:11px;color:#8888aa;letter-spacing:3px;'>
            MATCH #{match['match_number']} • {match.get('stage','').upper().replace('_',' ')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Score display
    col1, col_vs, col2 = st.columns([2, 1, 2])
    
    s1 = match.get("score_team1", 0)
    s2 = match.get("score_team2", 0)
    
    with col1:
        st.markdown(f"""
        <div style='text-align:center;background:#1a0a0a;border:1px solid rgba(255,60,60,0.3);padding:20px;'>
            <div style='font-family:Bebas Neue,cursive;font-size:20px;letter-spacing:3px;color:#ff3c3c;'>
                {t1.get('name','Team 1')}
            </div>
            <div style='font-family:Bebas Neue,cursive;font-size:72px;color:#ff3c3c;line-height:1;'>
                {s1}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_vs:
        st.markdown(f"""
        <div style='text-align:center;padding:20px 0;'>
            <div style='font-family:Bebas Neue,cursive;font-size:28px;color:#8888aa;letter-spacing:4px;'>VS</div>
            <div style='font-family:Space Mono,monospace;font-size:11px;color:#8888aa;margin-top:8px;'>
                FIRST TO 15
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style='text-align:center;background:#0a0a1a;border:1px solid rgba(0,229,255,0.3);padding:20px;'>
            <div style='font-family:Bebas Neue,cursive;font-size:20px;letter-spacing:3px;color:#00e5ff;'>
                {t2.get('name','Team 2')}
            </div>
            <div style='font-family:Bebas Neue,cursive;font-size:72px;color:#00e5ff;line-height:1;'>
                {s2}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    if status == "completed":
        w = match.get("winner", {}) or {}
        st.success(f"🏆 Match Complete! Winner: **{w.get('name', '?')}**")
        
        # Check if all group stage done
        if match.get("stage") == "group" and check_group_stage_complete():
            update_state(group_stage_complete=True)
        
        if st.button("➡️ Next Match", use_container_width=True):
            st.rerun()
        return

    if status == "pending":
        st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
        if st.button("🚀 START MATCH", type="primary", use_container_width=True):
            start_match(match["id"])
            st.success("Match started!")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # LIVE scoring
    if status == "live":
        st.markdown("""
        <div style='text-align:center;padding:8px;background:rgba(255,60,60,0.1);
                    border:1px solid rgba(255,60,60,0.3);margin-bottom:16px;'>
            <span style='color:#ff3c3c;font-family:Space Mono,monospace;font-size:12px;
                         letter-spacing:3px;animation:pulse 1s infinite;'>● LIVE MATCH</span>
        </div>
        """, unsafe_allow_html=True)

        col_b1, col_space, col_b2 = st.columns([2, 1, 2])
        
        with col_b1:
            if st.button(f"➕ +1 Point for {t1.get('name','Team 1')}", 
                        type="primary", use_container_width=True, key="score_t1"):
                won, winner_id = add_score(
                    match["id"], "score_team1", s1,
                    t1.get("id"), t2.get("id")
                )
                if won:
                    st.balloons()
                    st.success(f"🏆 {t1.get('name')} wins the match!")
                st.rerun()
        
        with col_b2:
            if st.button(f"➕ +1 Point for {t2.get('name','Team 2')}", 
                        type="primary", use_container_width=True, key="score_t2"):
                won, winner_id = add_score(
                    match["id"], "score_team2", s2,
                    t1.get("id"), t2.get("id")
                )
                if won:
                    st.balloons()
                    st.success(f"🏆 {t2.get('name')} wins the match!")
                st.rerun()

        # Progress bars
        st.markdown("#### Score Progress (first to 15 wins)")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown(f"**{t1.get('name')}** — {s1}/15")
            st.progress(min(s1 / 15, 1.0))
        with col_p2:
            st.markdown(f"**{t2.get('name')}** — {s2}/15")
            st.progress(min(s2 / 15, 1.0))

        # Auto-refresh
        st.markdown("---")
        st.caption("🔄 Page auto-refreshes to keep scores current.")
        time.sleep(2)
        st.rerun()
