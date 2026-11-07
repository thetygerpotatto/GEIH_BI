"""Indicadores oficiales del mercado laboral (metodología DANE), ponderados por FEX_C18.

* TD  (tasa de desempleo)            = desocupados / fuerza de trabajo
* TO  (tasa de ocupación)            = ocupados / población en edad de trabajar
* TGP (tasa global de participación) = fuerza de trabajo / población en edad de trabajar

Los factores de expansión de un mes suman la población de ese mes; al agregar varios
meses las poblaciones se promedian (se divide por el número de meses), las tasas no cambian.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd

WEIGHTED_SUMS = ["w_pet", "w_ft", "w_oci", "w_dsi", "w_fft"]


@dataclass(frozen=True)
class LaborIndicators:
    poblacion_pet: float
    fuerza_trabajo: float
    ocupados: float
    desocupados: float
    inactivos: float
    td: float | None
    to: float | None
    tgp: float | None

    def as_dict(self) -> dict:
        return asdict(self)


def _ratio(num: float, den: float) -> float | None:
    return num / den * 100 if den else None


def weighted_sums(df: pd.DataFrame) -> dict[str, float]:
    """Sumas ponderadas de las banderas PET/FT/OCI/DSI/FFT."""
    fex = df["fex"].astype(float)
    return {
        "w_pet": float((fex * df["pet"].astype(float)).sum()),
        "w_ft": float((fex * df["ft"].astype(float)).sum()),
        "w_oci": float((fex * df["oci"].astype(float)).sum()),
        "w_dsi": float((fex * df["dsi"].astype(float)).sum()),
        "w_fft": float((fex * df["fft"].astype(float)).sum()),
    }


def indicators_from_sums(sums: dict[str, float], n_months: int = 1) -> LaborIndicators:
    """Calcula los indicadores a partir de sumas ponderadas de ``n_months`` meses."""
    if n_months < 1:
        raise ValueError("n_months debe ser >= 1")
    pet, ft, oci, dsi, fft = (sums.get(k, 0.0) for k in WEIGHTED_SUMS)
    return LaborIndicators(
        poblacion_pet=pet / n_months,
        fuerza_trabajo=ft / n_months,
        ocupados=oci / n_months,
        desocupados=dsi / n_months,
        inactivos=fft / n_months,
        td=_ratio(dsi, ft),
        to=_ratio(oci, pet),
        tgp=_ratio(ft, pet),
    )


def compute_indicators(df: pd.DataFrame) -> LaborIndicators:
    n_months = int(df[["anio", "mes"]].drop_duplicates().shape[0]) or 1
    return indicators_from_sums(weighted_sums(df), n_months)


def add_rates(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega columnas td/to/tgp (en %) a un DataFrame de sumas ponderadas agrupadas."""
    out = df.copy()
    ft = out["w_ft"].where(out["w_ft"] > 0)
    pet = out["w_pet"].where(out["w_pet"] > 0)
    out["td"] = out["w_dsi"] / ft * 100
    out["to"] = out["w_oci"] / pet * 100
    out["tgp"] = out["w_ft"] / pet * 100
    return out
