"""Vista de inicio de sesión (HU 1)."""
from __future__ import annotations

import streamlit as st

from geih_bi.controllers.auth import LOGIN_ERROR, AuthController
from geih_bi.views import session


def render(auth: AuthController) -> None:
    _, center, _ = st.columns([1, 1.2, 1])
    with center:
        st.title("GEIH BI")
        st.caption("Mercado laboral colombiano · Gran Encuesta Integrada de Hogares 2022–2025")
        if st.session_state.pop("sesion_expirada", False):
            st.info("Su sesión expiró por inactividad. Ingrese nuevamente.")
        with st.form("login"):
            username = st.text_input("Usuario", key="login_usuario")
            password = st.text_input("Contraseña", type="password", key="login_clave")
            submitted = st.form_submit_button("Ingresar", type="primary", width="stretch")
        if submitted:
            user = auth.login(username, password)
            if user is None:
                st.error(LOGIN_ERROR)
            else:
                session.login(user)
                st.rerun()
