"""Figuras Plotly del tablero. Paleta categórica de referencia: azul, naranja.

Los títulos de cada gráfica los pinta la vista (``st.subheader``) para que nunca choquen con la
leyenda; la leyenda va siempre debajo del área de trazado.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


@dataclass(frozen=True)
class Palette:
    series_1: str
    series_2: str
    reference: str


# Deben coincidir con chartCategoricalColors de .streamlit/config.toml. Marcas ≥ 5,6:1 sobre el fondo oscuro.
LIGHT = Palette(series_1="#2a78d6", series_2="#eb6834", reference="#8a8984")
DARK = Palette(series_1="#5b9cec", series_2="#f08a5d", reference="#a3a29d")


def palette(dark: bool = False) -> Palette:
    return DARK if dark else LIGHT


FONT = dict(family="Inter, system-ui, sans-serif", size=13)

_BASE_LAYOUT = dict(
    font=FONT,
    margin=dict(l=8, r=8, t=16, b=8),
    hoverlabel=dict(font=FONT),
    legend=dict(orientation="h", yanchor="top", y=-0.14, xanchor="left", x=0, title=None),
)


def _percent_axis(fig: go.Figure, **kwargs) -> None:
    fig.update_yaxes(ticksuffix=" %", showgrid=True, gridwidth=1, zeroline=False, **kwargs)


def monthly_rates(series: pd.DataFrame, dark: bool = False) -> go.Figure:
    """Dos paneles con eje de tiempo compartido: TD sola, y TO junto a TGP."""
    fig = make_subplots(
        rows=1, cols=2, shared_xaxes=True, horizontal_spacing=0.08,
        subplot_titles=("Tasa de desempleo (TD)", "Ocupación (TO) y participación (TGP)"),
    )
    pal = palette(dark)
    hover = "%{x|%b %Y}<br>%{fullData.name}: %{y:.1f} %<extra></extra>"
    line = dict(width=2)
    fig.add_trace(go.Scatter(x=series["fecha"], y=series["td"], name="TD", mode="lines",
                             line={**line, "color": pal.series_1}, hovertemplate=hover, showlegend=False), 1, 1)
    fig.add_trace(go.Scatter(x=series["fecha"], y=series["to"], name="TO", mode="lines",
                             line={**line, "color": pal.series_1}, hovertemplate=hover), 1, 2)
    fig.add_trace(go.Scatter(x=series["fecha"], y=series["tgp"], name="TGP", mode="lines",
                             line={**line, "color": pal.series_2}, hovertemplate=hover), 1, 2)
    if not series.empty:
        last = series.iloc[-1]
        for col, name in (("to", "TO"), ("tgp", "TGP")):
            fig.add_annotation(x=last["fecha"], y=last[col], text=name, xanchor="left", xshift=6,
                               showarrow=False, row=1, col=2)
    fig.update_layout(**{**_BASE_LAYOUT, "margin": dict(l=8, r=32, t=40, b=8),
                         "legend": {**_BASE_LAYOUT["legend"], "y": -0.2}},
                      height=380, hovermode="x unified")
    fig.update_annotations(font=FONT)
    _percent_axis(fig)
    fig.update_xaxes(showgrid=False, dtick="M6", tickformat="%b\n%Y")
    return fig


def department_unemployment(df: pd.DataFrame, national_td: float | None, dark: bool = False) -> go.Figure:
    """Barras horizontales ordenadas de mayor a menor TD, con línea de referencia nacional."""
    pal = palette(dark)
    data = df.sort_values("td")
    fig = go.Figure(
        go.Bar(
            x=data["td"], y=data["departamento"], orientation="h", marker_color=pal.series_1,
            marker_line_width=0, customdata=data["dpto"],
            hovertemplate="%{y}<br>TD: %{x:.1f} %<extra></extra>",
        )
    )
    if national_td is not None:
        fig.add_vline(x=national_td, line_dash="dash", line_color=pal.reference, line_width=1.5,
                      annotation_text=f"Selección: {national_td:.1f} %".replace(".", ","),
                      annotation_position="top", annotation_font=FONT)
    fig.update_layout(**{**_BASE_LAYOUT, "margin": dict(l=8, r=8, t=32, b=8)},
                      height=max(320, 24 * len(data) + 60), bargap=0.25, showlegend=False)
    fig.update_xaxes(ticksuffix=" %", showgrid=True)
    fig.update_yaxes(showgrid=False)
    return fig


def unemployment_by_sex_age(df: pd.DataFrame, dark: bool = False) -> go.Figure:
    fig = go.Figure()
    pal = palette(dark)
    for sexo, color in ((1, pal.series_1), (2, pal.series_2)):
        part = df[df["sexo"] == sexo]
        if part.empty:
            continue
        fig.add_trace(go.Bar(
            x=part["rango_edad"], y=part["td"], name=part["sexo_nombre"].iloc[0], marker_color=color,
            marker_line_width=0, hovertemplate="%{x} años · %{fullData.name}<br>TD: %{y:.1f} %<extra></extra>",
        ))
    fig.update_layout(**_BASE_LAYOUT, height=380, barmode="group", bargap=0.3, bargroupgap=0.08)
    fig.update_xaxes(title=None, ticksuffix=" años", showgrid=False)
    _percent_axis(fig)
    return fig
