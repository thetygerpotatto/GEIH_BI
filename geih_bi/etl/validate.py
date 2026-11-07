"""Reglas de calidad de datos aplicadas al resultado de cada mes."""
from __future__ import annotations

import pandas as pd

TD_RANGE = (3.0, 30.0)  # rango plausible de la TD nacional mensual


def validate_month(df: pd.DataFrame, td: float | None) -> list[str]:
    """Devuelve la lista de problemas encontrados (vacía si el mes es válido)."""
    issues: list[str] = []
    periods = df["periodo"].dropna().unique()
    if len(periods) != 1:
        issues.append(f"se esperaba un único periodo y hay {sorted(periods)}")
    if (df["ft"] != (df["oci"] + df["dsi"])).any():
        issues.append("FT != OCI + DSI en algunos registros")
    if ((df["oci"] == 1) & (df["pet"] != 1)).any():
        issues.append("hay ocupados fuera de la PET")
    if df["dpto"].isna().any():
        issues.append("registros sin departamento")
    if td is None:
        issues.append("TD no calculable (fuerza de trabajo vacía)")
    elif not TD_RANGE[0] <= td <= TD_RANGE[1]:
        issues.append(f"TD fuera de rango plausible: {td:.2f}%")
    return issues
