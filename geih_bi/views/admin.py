"""Vistas del administrador: usuarios (HU 4) y calidad de datos (HU 8)."""
from __future__ import annotations

import streamlit as st

from geih_bi.controllers.admin import AdminController, ValidationError
from geih_bi.models.user import Role, User
from geih_bi.views import ui


def render_users(controller: AdminController, actor: User) -> None:
    st.title("Gestión de usuarios")
    ui.subtitle("Cree cuentas y asigne el rol que determina el menú de cada usuario.")
    with st.form("nuevo_usuario", clear_on_submit=True):
        st.subheader("Crear usuario")
        cols = st.columns(2)
        username = cols[0].text_input("Usuario", key="nu_usuario")
        nombre = cols[1].text_input("Nombre completo", key="nu_nombre")
        password = cols[0].text_input("Contraseña", type="password", key="nu_clave")
        rol = cols[1].selectbox("Rol", list(Role), format_func=lambda r: r.label, key="nu_rol")
        submitted = st.form_submit_button("Crear usuario", type="primary", icon=":material/person_add:")
    if submitted:
        try:
            user = controller.create_user(username, nombre, password, rol)
            st.success(f"Usuario '{user.username}' creado con rol {user.rol.label}.", icon=":material/check_circle:")
        except ValidationError as exc:
            st.error(str(exc), icon=":material/error:")

    st.subheader("Usuarios registrados")
    users = controller.list_users()
    st.dataframe(
        [{"Usuario": u.username, "Nombre": u.nombre, "Rol": u.rol.label,
          "Estado": "Activo" if u.activo else "Inactivo"} for u in users],
        hide_index=True, width="stretch",
    )


def render_quality(controller: AdminController) -> None:
    st.title("Calidad de los datos (ETL)")
    ui.subtitle("Resultado de las reglas de validación aplicadas a cada mes procesado.")
    df = controller.quality_report()
    if df.empty:
        st.info("Aún no hay informe de calidad. Ejecute `python -m geih_bi.etl run`.")
        return
    problems = int((df["Estado"] != "Válido").sum())
    cols = st.columns(3)
    cols[0].metric("Meses cargados", len(df), border=True)
    cols[1].metric("Registros", f"{int(df['Filas salida'].sum()):,}".replace(",", "."), border=True)
    cols[2].metric("Meses con problemas", problems, border=True)
    if problems:
        st.warning("Hay meses que no superan las reglas de validación; revise la columna Problemas.",
                   icon=":material/warning:")
    else:
        st.success("Todos los meses superan las reglas de validación "
                   "(FT = OCI + DSI, ocupados dentro de la PET, un periodo por archivo, TD plausible).",
                   icon=":material/verified:")
    st.dataframe(df, hide_index=True, width="stretch",
                 column_config={"TD (%)": st.column_config.NumberColumn(format="%.1f")})
