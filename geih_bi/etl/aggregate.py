"""Agregados precalculados que alimentan el dashboard y el modelo predictivo."""
from __future__ import annotations

import pandas as pd

GROUP_DIMS = ["anio", "mes", "periodo", "dpto", "clase", "sexo", "rango_edad", "grupo_educativo"]


def build_monthly_cube(df: pd.DataFrame) -> pd.DataFrame:
    """Cubo mensual: sumas ponderadas por departamento, zona, sexo, edad y educación.

    Con estas sumas se reconstruyen TD/TO/TGP para cualquier combinación de esos filtros
    sin recorrer la tabla de hechos completa.
    """
    fex = df["fex"].astype(float)
    ocupado = df["oci"] == 1
    con_ingreso = ocupado & (df["ingreso_laboral"].fillna(0) > 0)
    con_horas = ocupado & df["horas_semanales"].notna()
    con_informal = df["informal"].notna()
    con_semanas = (df["dsi"] == 1) & df["semanas_buscando"].notna()

    measures = pd.DataFrame(
        {
            "n": 1,
            "w_pob": fex,
            "w_pet": fex * df["pet"].astype(float),
            "w_ft": fex * df["ft"].astype(float),
            "w_oci": fex * df["oci"].astype(float),
            "w_dsi": fex * df["dsi"].astype(float),
            "w_fft": fex * df["fft"].astype(float),
            "w_ingreso": (fex * df["ingreso_laboral"].astype(float)).where(con_ingreso, 0.0),
            "w_ingreso_n": fex.where(con_ingreso, 0.0),
            "w_horas": (fex * df["horas_semanales"].astype(float)).where(con_horas, 0.0),
            "w_horas_n": fex.where(con_horas, 0.0),
            "w_informal": (fex * df["informal"].astype(float)).where(con_informal, 0.0),
            "w_informal_n": fex.where(con_informal, 0.0),
            "w_semanas": (fex * df["semanas_buscando"].astype(float)).where(con_semanas, 0.0),
            "w_semanas_n": fex.where(con_semanas, 0.0),
        }
    )
    keys = df[GROUP_DIMS].astype(object).where(df[GROUP_DIMS].notna(), None)
    cube = pd.concat([keys, measures], axis=1).groupby(GROUP_DIMS, dropna=False, as_index=False).sum()
    return cube
