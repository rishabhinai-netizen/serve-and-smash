import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from utils.db import get_state, count_by_role, login_user

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

.main { background: #0a0a0f; }
.stApp { background: linear-gradient(135deg, #0a0a0f 0%, #0d0d1a 100%); }

/* Header */
.hero-header {
    text-align: center;
    padding: 2rem 0 1rem;
    background: linear-gradient(180deg, rgba(255,60,60,0.08) 0%, transparent 100%);
    border-bottom: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 2rem;
}
.hero-title {
    font-family: 'Bebas Neue', cursive;
    font-size: clamp(48px, 8vw, 80px);
    letter-spacing: 8px;
    background: linear-gradient(135deg, #ff3c3c, #ffb800);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    line-height: 1;
}
.hero-sub {
    font-family: 'Space Mono', monospace;
    color: #8888aa;
    font-size: 11px;
    letter-spacing: 5px;
    margin-top: 8px;
    text-transform: uppercase;
}

/* Status chips */
.status-row { display: flex; gap: 12px; flex-wrap: wrap; margin: 1rem 0; }
.chip {
    padding: 6px 16px;
    border-radius: 0;
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    letter-spacing: 2px;
    border: 1px solid rgba(255,255,255,0.1);
    clip-path: polygon(8px 0%, 100% 0%, calc(100% - 8px) 100%, 0% 100%);
}
.chip-player { background: rgba(0,229,255,0.15); color: #00e5ff; border-color: rgba(0,229,255,0.3); }
.chip-referee { background: rgba(255,184,0,0.15); color: #ffb800; border-color: rgba(255,184,0,0.3); }
.chip-admin { background: rgba(255,60,60,0.15); color: #ff3c3c; border-color: rgba(255,60,60,0.3); }

/* Cards */
.ss-card {
    background: #111118;
    border: 1px solid rgba(255,255,255,0.07);
    border-top: 3px solid #ff3c3c;
    padding: 24px;
    margin-bottom: 20px;
}
.ss-card-gold { border-top-color: #ffb800; }
.ss-card-cyan { border-top-color: #00e5ff; }

/* Section titles */
.section-title {
    font-family: 'Bebas Neue', cursive;
    font-size: 24px;
    letter-spacing: 4px;
    color: #ffb800;
    margin-bottom: 1rem;
}

/* Team badge */
.team-badge {
    display: inline-block;
    background: rgba(255,184,0,0.15);
    border: 1px solid rgba(255,184,0,0.4);
    color: #ffb800;
    font-family: 'Bebas Neue', cursive;
    font-size: 20px;
    letter-spacing: 3px;
    padding: 4px 16px;
    margin-right: 8px;
}

/* Match row */
.match-row {
    background: #1a1a25;
    border: 1px solid rgba(255,255,255,0.07);
    padding: 12px 20px;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 15px;
}
.match-live { border-left: 3px solid #ff3c3c; animation: livePulse 2s infinite; }
.match-done { border-left: 3px solid #22c55e; opacity: 0.7; }
@keyframes livePulse { 0%,100%{border-left-color:#ff3c3c} 50%{border-left-color:#ff8888} }

/* Score display */
.score-big {
    font-family: 'Bebas Neue', cursive;
    font-size: 64px;
    letter-spacing: 4px;
    line-height: 1;
}
.score-red { color: #ff3c3c; }
.score-cyan { color: #00e5ff; }

/* Leaderboard */
.lb-row {
    display: grid;
    grid-template-columns: 40px 1fr 60px 50px 50px 80px 80px 80px;
    gap: 8px;
    padding: 10px 16px;
    background: #1a1a25;
    border: 1px solid rgba(255,255,255,0.07);
    margin-bottom: 4px;
    align-items: center;
    font-size: 14px;
}
.lb-header {
    background: #22223a;
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    letter-spacing: 2px;
    color: #8888aa;
    text-transform: uppercase;
}
.lb-qualified { border-left: 3px solid #ffb800; }
.pos-1 { color: #ffd700; font-family: 'Bebas Neue', cursive; font-size: 20px; }
.pos-2 { color: #c0c0c0; font-family: 'Bebas Neue', cursive; font-size: 18px; }
.pos-3 { color: #cd7f32; font-family: 'Bebas Neue', cursive; font-size: 18px; }
.pos-4 { color: #ffb800; font-family: 'Bebas Neue', cursive; font-size: 16px; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0d0d1a;
    border-right: 1px solid rgba(255,255,255,0.07);
}
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ───────────────────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None

# ─── Header ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-header">
  <div class="hero-title">🏸 SERVE &amp; SMASH</div>
  <div class="hero-sub">Badminton Tournament Management System</div>
</div>
""", unsafe_allow_html=True)

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏸 Navigation")
    
    state = get_state()
    counts = count_by_role()

    st.markdown(f"""
    <div style='margin:12px 0;'>
        <div class='chip chip-player' style='margin-bottom:6px;'>👤 PLAYERS: {counts['player']}/14</div><br>
        <div class='chip chip-referee' style='margin-bottom:6px;'>🎯 REFEREES: {counts['referee']}/2</div><br>
        <div class='chip chip-admin'>⚙️ ADMIN: {counts['admin']}/1</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"**Phase:** `{state['phase'].upper()}`")
    st.markdown("---")

    if st.session_state.user:
        u = st.session_state.user
        st.success(f"✅ Logged in as **{u['name']}**\n\n`{u['role'].upper()}`")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.rerun()
    else:
        st.info("Please sign up or log in below.")

# ─── Main Router ─────────────────────────────────────────────────────────────
user = st.session_state.user

if user is None:
    # Show signup / login
    tab1, tab2 = st.tabs(["📝 SIGN UP", "🔐 LOGIN"])
    with tab1:
        from pages.signup import show_signup
        show_signup()
    with tab2:
        from pages.login import show_login
        show_login()
else:
    role = user["role"]
    if role == "admin":
        from pages.admin import show_admin
        show_admin()
    elif role == "referee":
        from pages.referee import show_referee
        show_referee()
    elif role == "player":
        from pages.player import show_player
        show_player()
