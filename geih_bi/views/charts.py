"""Figuras Plotly del tablero. Paleta categórica de referencia: azul, naranja."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

SERIES_1 = "#2a78d6"
SERIES_2 = "#eb6834"
REFERENCE = "#8a8984"
FONT = dict(family="Inter, system-ui, sans-serif", size=13)

_BASE_LAYOUT = dict(
    font=FONT,
    margin=dict(l=8, r=8, t=48, b=8),
    hoverlabel=dict(font=FONT),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title=None),
)


def _percent_axis(fig: go.Figure, **kwargs) -> None:
    fig.update_yaxes(ticksuffix=" %", showgrid=True, gridwidth=1, zeroline=False, **kwargs)


def monthly_rates(series: pd.DataFrame) -> go.Figure:
    """Dos paneles con eje de tiempo compartido: TD sola, y TO junto a TGP."""
    fig = make_subplots(
        rows=1, cols=2, shared_xaxes=True, horizontal_spacing=0.08,
        subplot_titles=("Tasa de desempleo (TD)", "Ocupación (TO) y participación (TGP)"),
    )
    hover = "%{x|%b %Y}<br>%{fullData.name}: %{y:.1f} %<extra></extra>"
    line = dict(width=2)
    fig.add_trace(go.Scatter(x=series["fecha"], y=series["td"], name="TD", mode="lines",
                             line={**line, "color": SERIES_1}, hovertemplate=hover, showlegend=False), 1, 1)
    fig.add_trace(go.Scatter(x=series["fecha"], y=series["to"], name="TO", mode="lines",
                             line={**line, "color": SERIES_1}, hovertemplate=hover), 1, 2)
    fig.add_trace(go.Scatter(x=series["fecha"], y=series["tgp"], name="TGP", mode="lines",
                             line={**line, "color": SERIES_2}, hovertemplate=hover), 1, 2)
    if not series.empty:
        last = series.iloc[-1]
        for col, name in (("to", "TO"), ("tgp", "TGP")):
            fig.add_annotation(x=last["fecha"], y=last[col], text=name, xanchor="left", xshift=6,
                               showarrow=False, row=1, col=2)
    fig.update_layout(**_BASE_LAYOUT, height=360, hovermode="x unified")
    fig.update_annotations(font=FONT)
    _percent_axis(fig)
    fig.update_xaxes(showgrid=False, dtick="M6", tickformat="%b\n%Y")
    return fig


def department_unemployment(df: pd.DataFrame, national_td: float | None) -> go.Figure:
    """Barras horizontales ordenadas de mayor a menor TD, con línea de referencia nacional."""
    data = df.sort_values("td")
    fig = go.Figure(
        go.Bar(
            x=data["td"], y=data["departamento"], orientation="h", marker_color=SERIES_1,
            marker_line_width=0, customdata=data["dpto"],
            hovertemplate="%{y}<br>TD: %{x:.1f} %<extra></extra>",
        )
    )
    if national_td is not None:
        fig.add_vline(x=national_td, line_dash="dash", line_color=REFERENCE, line_width=1.5,
                      annotation_text=f"Selección: {national_td:.1f} %".replace(".", ","),
                      annotation_position="top", annotation_font=FONT)
    fig.update_layout(**_BASE_LAYOUT, height=max(320, 24 * len(data) + 80), bargap=0.25,
                      title=dict(text="Tasa de desempleo por departamento", font=FONT))
    fig.update_xaxes(ticksuffix=" %", showgrid=True)
    fig.update_yaxes(showgrid=False)
    return fig


def unemployment_by_sex_age(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for sexo, color in ((1, SERIES_1), (2, SERIES_2)):
        part = df[df["sexo"] == sexo]
        if part.empty:
            continue
        fig.add_trace(go.Bar(
            x=part["rango_edad"], y=part["td"], name=part["sexo_nombre"].iloc[0], marker_color=color,
            marker_line_width=0, hovertemplate="%{x} años · %{fullData.name}<br>TD: %{y:.1f} %<extra></extra>",
        ))
    fig.update_layout(**_BASE_LAYOUT, height=360, barmode="group", bargap=0.3, bargroupgap=0.08,
                      title=dict(text="Tasa de desempleo por sexo y rango de edad", font=FONT))
    fig.update_xaxes(title="Rango de edad (años)", showgrid=False)
    _percent_axis(fig)
    return fig
