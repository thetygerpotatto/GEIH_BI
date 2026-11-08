"""Vista de inicio de sesión (HU 1)."""
from __future__ import annotations

import streamlit as st

from geih_bi.controllers.auth import LOGIN_ERROR, AuthController
from geih_bi.views import session, ui


def render(auth: AuthController) -> None:
    st.space("large")
    _, center, _ = st.columns([1, 1.1, 1])
    with center:
        st.title("GEIH BI")
        st.markdown("**Mercado laboral colombiano**  \n"
                    ":gray[Gran Encuesta Integrada de Hogares · DANE · 2022–2025]")
        if st.session_state.pop("sesion_expirada", False):
            st.info("Su sesión expiró por inactividad. Ingrese nuevamente.", icon=":material/schedule:")
        with st.form("login"):
            st.markdown("##### Iniciar sesión")
            ui.note("Ingrese con la cuenta que le asignó el administrador.")
            username = st.text_input(
                "Usuario", key="login_usuario", placeholder="Ej.: jnorena", autocomplete="username",
                help="Sin espacios. Las mayúsculas se convierten a minúsculas automáticamente.",
            )
            password = st.text_input(
                "Contraseña", type="password", key="login_clave", placeholder="Su contraseña",
                autocomplete="current-password", help="Distingue mayúsculas y minúsculas.",
            )
            submitted = st.form_submit_button("Ingresar", type="primary", width="stretch",
                                              icon=":material/login:")
        ui.note("¿Olvidó su contraseña o no tiene cuenta? Contacte al administrador del sistema. "
                "La sesión se cierra tras 30 minutos de inactividad.")
        if submitted:
            user = auth.login(username, password)
            if user is None:
                st.error(LOGIN_ERROR)
            else:
                session.login(user)
                st.rerun()
