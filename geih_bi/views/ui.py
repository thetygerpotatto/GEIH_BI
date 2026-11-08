"""Componentes de texto con contraste verificado.

``st.caption`` pinta el texto al 60 % de opacidad (≈ 4,1:1 sobre blanco, por debajo de WCAG AA);
estos helpers usan ``grayTextColor`` del tema (≥ 7:1 en claro y oscuro).
"""
from __future__ import annotations

import streamlit as st


def subtitle(text: str) -> None:
    """Línea descriptiva bajo el título de una página."""
    st.markdown(f":gray[{text}]")


def note(text: str) -> None:
    """Nota secundaria en tamaño pequeño (fuente, tamaño de muestra, instrucciones)."""
    st.markdown(f":small[:gray[{text}]]")


def is_dark() -> bool:
    """Tema activo del navegador (claro por defecto si aún no se conoce)."""
    theme = getattr(st.context, "theme", None)
    return getattr(theme, "type", None) == "dark"
