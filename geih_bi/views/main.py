"""Punto de entrada de la interfaz: autenticación y menú según el rol (HU 1–3)."""
from __future__ import annotations

import streamlit as st

from geih_bi.context import AppContext, build_context
from geih_bi.core.permissions import Page, pages_for
from geih_bi.models.user import User
from geih_bi.views import admin, dashboard, login, session

PAGE_TITLES = {
    Page.TABLERO: "Tablero",
    Page.USUARIOS: "Usuarios",
    Page.CALIDAD: "Calidad de datos",
}


@st.cache_resource
def get_context() -> AppContext:
    return build_context()


def _page(page: Page, ctx: AppContext, user: User) -> st.Page:
    renderers = {
        Page.TABLERO: lambda: dashboard.render(ctx.dashboard, user),
        Page.USUARIOS: lambda: admin.render_users(ctx.admin, user),
        Page.CALIDAD: lambda: admin.render_quality(ctx.admin),
    }
    return st.Page(renderers[page], title=PAGE_TITLES[page], url_path=page.value)


def run() -> None:
    st.set_page_config(page_title="GEIH BI", layout="wide")
    ctx = get_context()
    user = session.current_user()
    if user is None:
        login.render(ctx.auth)
        return

    navigation = st.navigation([_page(p, ctx, user) for p in pages_for(user.rol)])
    with st.sidebar:
        st.markdown(f"**{user.nombre}**  \n{user.rol.label}")
        st.button("Cerrar sesión", on_click=session.logout, width="stretch")
    navigation.run()
