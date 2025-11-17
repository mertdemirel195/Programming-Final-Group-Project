"""Streamlit authentication views (login/sign-up/google)."""
from __future__ import annotations

import os
from typing import Optional

import streamlit as st
from streamlit_oauth import OAuth2Component  # type: ignore

import db


def ensure_session_state() -> None:
    if "user" not in st.session_state:
        st.session_state.user = None
    if "login_mode" not in st.session_state:
        st.session_state.login_mode = "login"


def login_form() -> None:
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    submit = st.button("Login", use_container_width=True)
    if submit:
        if db.authenticate(email, password):
            st.session_state.user = email.lower()
            st.success(f"Welcome back, {email}")
            st.rerun()
        else:
            st.error("Invalid email/password")


def signup_form() -> None:
    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Password", type="password", key="signup_password")
    confirm = st.text_input("Confirm password", type="password", key="signup_confirm")
    submit = st.button("Sign up", use_container_width=True)
    if submit:
        if not email or not password:
            st.error("Email and password required")
        elif password != confirm:
            st.error("Passwords do not match")
        elif db.create_user(email, password):
            st.success("Account created! Please log in.")
            st.session_state.login_mode = "login"
            st.rerun()
        else:
            st.error("That email is already registered")


def google_login_button() -> None:
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret:
        st.info("Set GOOGLE_CLIENT_ID/SECRET env vars to enable Google login.")
        return
    oauth = OAuth2Component(
        client_id=client_id,
        client_secret=client_secret,
        authorize_endpoint="https://accounts.google.com/o/oauth2/auth",
        token_endpoint="https://oauth2.googleapis.com/token",
        refresh_token_endpoint="https://oauth2.googleapis.com/token",
        revoke_token_endpoint="https://oauth2.googleapis.com/revoke",
    )
    result = oauth.authorize_button(
        name="Continue with Google",
        icon="https://developers.google.com/identity/images/g-logo.png",
        redirect_uri=os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8501"),
        scope="openid email profile",
        key="google_oauth",
    )
    if result and "email" in result:
        st.session_state.user = result["email"].lower()
        st.success(f"Signed in as {st.session_state.user}")


def auth_section() -> Optional[str]:
    ensure_session_state()
    if st.session_state.user:
        return st.session_state.user
    st.markdown(
        """
        <div class="auth-hero">
            <div>
                <p class="eyebrow">Welcome to</p>
                <h1>FinNews Portal</h1>
                <p>Secure access to your command center. Sign in to view live intelligence.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    tab_login, tab_signup, tab_google = st.tabs(["Login", "Sign Up", "Google"])
    with tab_login:
        st.markdown("<div class='glass-panel auth-panel'><h3>Log in</h3>", unsafe_allow_html=True)
        login_form()
        st.markdown("</div>", unsafe_allow_html=True)
    with tab_signup:
        st.markdown("<div class='glass-panel auth-panel'><h3>Create account</h3>", unsafe_allow_html=True)
        signup_form()
        st.markdown("</div>", unsafe_allow_html=True)
    with tab_google:
        st.markdown("<div class='glass-panel auth-panel'><h3>Continue with Google</h3>", unsafe_allow_html=True)
        google_login_button()
        st.markdown("</div>", unsafe_allow_html=True)
    return None
