"""Punto de entrada de la interfaz: autenticación y menú según el rol (HU 1–3)."""
from __future__ import annotations

import streamlit as st

from geih_bi.context import AppContext, build_context
from geih_bi.core.permissions import Page, pages_for
from geih_bi.models.user import User
from geih_bi.views import admin, dashboard, login, session, ui

PAGE_TITLES = {
    Page.TABLERO: "Tablero",
    Page.USUARIOS: "Usuarios",
    Page.CALIDAD: "Calidad de datos",
}
PAGE_ICONS = {
    Page.TABLERO: ":material/monitoring:",
    Page.USUARIOS: ":material/group:",
    Page.CALIDAD: ":material/fact_check:",
}
ROLE_COLORS = {"administrador": "violet", "analista": "blue", "gerente": "green"}


@st.cache_resource
def get_context() -> AppContext:
    return build_context()


def _page(page: Page, ctx: AppContext, user: User) -> st.Page:
    renderers = {
        Page.TABLERO: lambda: dashboard.render(ctx.dashboard, user),
        Page.USUARIOS: lambda: admin.render_users(ctx.admin, user),
        Page.CALIDAD: lambda: admin.render_quality(ctx.admin),
    }
    return st.Page(renderers[page], title=PAGE_TITLES[page], url_path=page.value, icon=PAGE_ICONS[page])


def run() -> None:
    st.set_page_config(page_title="GEIH BI", page_icon=":material/work:", layout="wide")
    ctx = get_context()
    user = session.current_user()
    if user is None:
        login.render(ctx.auth)
        return

    navigation = st.navigation([_page(p, ctx, user) for p in pages_for(user.rol)])
    with st.sidebar:
        st.markdown("### GEIH BI")
        ui.subtitle("Mercado laboral colombiano")
        st.divider()
        st.markdown(f"**{user.nombre}**")
        st.badge(user.rol.label, icon=":material/badge:", color=ROLE_COLORS.get(user.rol.value, "gray"))
        st.button("Cerrar sesión", on_click=session.logout, width="stretch", icon=":material/logout:")
        ui.note("Fuente: DANE, GEIH Marco 2018.")
    navigation.run()
