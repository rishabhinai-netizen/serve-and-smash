import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from utils.db import login_user, get_state

def show_login():
    state = get_state()

    st.markdown('<div class="ss-card ss-card-cyan">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🔐 LOGIN</div>', unsafe_allow_html=True)

    with st.form("login_form"):
        mobile = st.text_input("Mobile Number", placeholder="Your registered 10-digit number")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("🔑 LOGIN", use_container_width=True)

    if submit:
        if not mobile or not password:
            st.error("Please enter both mobile number and password.")
        else:
            user, err = login_user(mobile.strip(), password)
            if err:
                st.error(f"❌ {err}")
            else:
                st.session_state.user = user
                st.success(f"✅ Welcome back, **{user['name']}**!")
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
