"""Pruebas funcionales de la interfaz con streamlit.testing (sin navegador)."""
from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from geih_bi.context import build_context
from geih_bi.models.user import Role

APP = str(Path(__file__).resolve().parents[2] / "app.py")


@pytest.fixture
def app(seeded_db, fast_hasher, monkeypatch):
    ctx = build_context(db=seeded_db, hasher=fast_hasher)
    for username, rol in (("admin", Role.ADMINISTRADOR), ("ana", Role.ANALISTA), ("gina", Role.GERENTE)):
        ctx.admin.create_user(username, username.capitalize(), "secreta123", rol)
    monkeypatch.setattr("geih_bi.views.main.build_context", lambda: ctx)
    st.cache_resource.clear()
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    yield at
    st.cache_resource.clear()


def _login(at, username, password="secreta123"):
    at.text_input(key="login_usuario").input(username)
    at.text_input(key="login_clave").input(password)
    at.button[0].click()
    at.run()
    return at


def test_login_page_is_shown_first(app):
    assert app.title[0].value == "GEIH BI"
    assert not app.exception


def test_wrong_password_shows_generic_error(app):
    _login(app, "ana", "incorrecta")
    assert app.error[0].value == "Usuario o contraseña incorrectos"


def test_gerente_sees_dashboard_without_sex_age_chart(app):
    _login(app, "gina")
    assert not app.exception
    assert app.title[0].value == "Tablero del mercado laboral"
    labels = [m.label for m in app.metric]
    assert "Tasa de desempleo (TD)" in labels and len(labels) == 6
    assert "Ver datos por sexo y edad" not in [e.label for e in app.expander]


def test_analista_sees_sex_age_chart(app):
    _login(app, "ana")
    assert not app.exception
    assert "Ver datos por sexo y edad" in [e.label for e in app.expander]


def test_dashboard_metrics_follow_filters(app):
    _login(app, "ana")
    td = next(m for m in app.metric if m.label == "Tasa de desempleo (TD)")
    assert td.value == "8,3 %"  # (48+72+30) / (600*3) en 2025, todos los departamentos
    app.multiselect(key="f_dptos").set_value(["76"]).run()
    td = next(m for m in app.metric if m.label == "Tasa de desempleo (TD)")
    assert td.value == "10,0 %"


def test_admin_sees_user_management(app):
    _login(app, "admin")
    assert not app.exception
    assert app.title[0].value == "Gestión de usuarios"


def test_logout_returns_to_login(app):
    _login(app, "gina")
    next(b for b in app.button if b.label == "Cerrar sesión").click().run()
    assert app.title[0].value == "GEIH BI"
