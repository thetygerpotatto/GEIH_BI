"""Manejo de la sesión del usuario en Streamlit (HU 1, 3)."""
from __future__ import annotations

import time

import streamlit as st

from geih_bi.models.user import User

SESSION_TIMEOUT_SECONDS = 30 * 60
_USER = "usuario"
_LAST_ACTIVITY = "ultima_actividad"


def is_expired(last_activity: float | None, now: float, timeout: float = SESSION_TIMEOUT_SECONDS) -> bool:
    return last_activity is None or now - last_activity > timeout


def current_user() -> User | None:
    """Usuario de la sesión; cierra la sesión si estuvo inactiva más del tiempo límite."""
    user = st.session_state.get(_USER)
    if user is None:
        return None
    now = time.time()
    if is_expired(st.session_state.get(_LAST_ACTIVITY), now):
        logout()
        st.session_state["sesion_expirada"] = True
        return None
    st.session_state[_LAST_ACTIVITY] = now
    return user


def login(user: User) -> None:
    st.session_state[_USER] = user
    st.session_state[_LAST_ACTIVITY] = time.time()


def logout() -> None:
    for key in list(st.session_state.keys()):
        del st.session_state[key]
