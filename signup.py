import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from utils.db import signup_user, count_by_role, get_state, update_state

LIMITS = {"player": 14, "referee": 2, "admin": 1}

def show_signup():
    state = get_state()

    if state["signups_frozen"]:
        st.error("🔒 Signups are **frozen** — all slots are filled! Please login.")
        return

    counts = count_by_role()
    
    # Determine available roles
    available_roles = []
    if counts["admin"] < LIMITS["admin"]:
        available_roles.append("admin")
    if counts["referee"] < LIMITS["referee"]:
        available_roles.append("referee")
    if counts["player"] < LIMITS["player"]:
        available_roles.append("player")

    if not available_roles:
        st.error("🔒 All slots are full! Signups are now closed.")
        update_state(signups_frozen=True)
        return

    st.markdown('<div class="ss-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📝 PLAYER / REFEREE / ADMIN SIGNUP</div>', unsafe_allow_html=True)

    # Signup progress
    col1, col2, col3 = st.columns(3)
    col1.metric("Players", f"{counts['player']}/14")
    col2.metric("Referees", f"{counts['referee']}/2")
    col3.metric("Admin", f"{counts['admin']}/1")

    st.markdown("---")

    with st.form("signup_form", clear_on_submit=True):
        name = st.text_input("Full Name", placeholder="e.g. Rahul Sharma")
        mobile = st.text_input("Mobile Number (Username)", placeholder="e.g. 9876543210", max_chars=10)
        password = st.text_input("Password", type="password", placeholder="Min 6 characters")
        confirm = st.text_input("Confirm Password", type="password")
        role = st.selectbox("Category", available_roles, 
                           format_func=lambda x: {"player": "🏸 Player", "referee": "🎯 Referee", "admin": "⚙️ Admin"}[x])
        submit = st.form_submit_button("🚀 REGISTER", use_container_width=True)

    if submit:
        errors = []
        if not name.strip():
            errors.append("Name is required.")
        if not mobile.strip() or not mobile.isdigit() or len(mobile) != 10:
            errors.append("Valid 10-digit mobile number required.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            user, err = signup_user(name.strip(), mobile.strip(), password, role)
            if err:
                if "unique" in err.lower() or "duplicate" in err.lower():
                    st.error("❌ This mobile number is already registered!")
                else:
                    st.error(f"❌ Registration failed: {err}")
            else:
                st.success(f"✅ Welcome, **{name}**! You're registered as a **{role}**. Please login now.")
                
                # Recheck if all slots are now filled
                new_counts = count_by_role()
                if (new_counts["player"] >= 14 and 
                    new_counts["referee"] >= 2 and 
                    new_counts["admin"] >= 1):
                    update_state(signups_frozen=True)
                    st.info("🔒 All signup slots are now filled! Tournament signups are closed.")
                
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
