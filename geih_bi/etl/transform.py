"""Transformación: tipado, integración de módulos, depuración y variables derivadas."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from geih_bi.etl.catalogs import DIVISION_A_SECCION, NIVEL_EDUCATIVO, RANGOS_EDAD
from geih_bi.etl.schema import (
    FACT_FIELDS,
    FLAG_FIELDS,
    FLOAT_FIELDS,
    INT_FIELDS,
    KEYS,
    MODULE_COLUMNS,
    STR_FIELDS,
    Module,
)

HORAS_MAX = 130
EDAD_MAX = 110


@dataclass
class TransformReport:
    """Trazabilidad de lo que hizo la transformación en un mes (va al informe ETL)."""

    rows_in: dict[str, int] = field(default_factory=dict)
    duplicates_removed: dict[str, int] = field(default_factory=dict)
    orphans: dict[str, int] = field(default_factory=dict)
    invalid_weight_removed: int = 0
    values_nullified: dict[str, int] = field(default_factory=dict)
    rows_out: int = 0


def _to_number(series: pd.Series) -> pd.Series:
    text = series.astype("string").str.strip().str.replace(",", ".", regex=False)
    return pd.to_numeric(text, errors="coerce")


def normalize_module(frame: pd.DataFrame, module: Module) -> pd.DataFrame:
    """Renombra columnas al esquema destino y convierte llaves a enteros."""
    df = frame.rename(columns=MODULE_COLUMNS[module]).copy()
    for key in KEYS:
        df[key] = _to_number(df[key]).astype("Int64")
    return df.rename(columns={k: k.lower() for k in KEYS})


def merge_modules(
    modules: dict[Module, pd.DataFrame], report: TransformReport
) -> pd.DataFrame:
    """Une los módulos a la base de personas (Características) por la llave de persona."""
    keys = [k.lower() for k in KEYS]
    merged: pd.DataFrame | None = None
    for module in Module:
        df = modules[module]
        report.rows_in[module.value] = len(df)
        before = len(df)
        df = df.dropna(subset=keys).drop_duplicates(subset=keys, keep="first")
        report.duplicates_removed[module.value] = before - len(df)
        if merged is None:
            merged = df
            continue
        indicator = merged.merge(df[keys], on=keys, how="right", indicator=True)["_merge"]
        report.orphans[module.value] = int((indicator == "right_only").sum())
        merged = merged.merge(df, on=keys, how="left", validate="one_to_one")
    assert merged is not None
    return merged


def cast_types(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in INT_FIELDS:
        df[col] = _to_number(df[col]).round().astype("Int64")
    for col in FLOAT_FIELDS:
        df[col] = _to_number(df[col]).astype("Float64")
    for col in STR_FIELDS:
        df[col] = df[col].astype("string").str.strip()
    df["dpto"] = df["dpto"].str.zfill(2)
    df["area"] = df["area"].where(df["area"].isna(), df["area"].str.zfill(2))
    for col in FLAG_FIELDS:
        df[col] = (df[col] == 1).astype("Int8")
    return df


def _nullify(df: pd.DataFrame, col: str, mask: pd.Series, report: TransformReport) -> None:
    mask = mask.fillna(False)
    count = int(mask.sum())
    if count:
        df.loc[mask, col] = pd.NA
        report.values_nullified[col] = report.values_nullified.get(col, 0) + count


def clean(df: pd.DataFrame, report: TransformReport) -> pd.DataFrame:
    """Elimina registros sin factor de expansión y anula valores fuera de rango."""
    valid_weight = df["fex"].notna() & (df["fex"] > 0)
    report.invalid_weight_removed = int((~valid_weight).sum())
    df = df.loc[valid_weight].copy()

    _nullify(df, "edad", (df["edad"] < 0) | (df["edad"] > EDAD_MAX), report)
    _nullify(df, "sexo", df["sexo"].notna() & ~df["sexo"].isin([1, 2]), report)
    _nullify(df, "ingreso_laboral", df["ingreso_laboral"] < 0, report)
    _nullify(df, "horas_semanales", (df["horas_semanales"] < 0) | (df["horas_semanales"] > HORAS_MAX), report)
    _nullify(df, "semanas_buscando", df["semanas_buscando"] < 0, report)
    _nullify(
        df,
        "nivel_educativo",
        df["nivel_educativo"].notna() & ~df["nivel_educativo"].isin(list(NIVEL_EDUCATIVO)),
        report,
    )
    return df


def condicion_laboral(df: pd.DataFrame) -> pd.Series:
    """Clasifica a cada persona según los indicadores oficiales OCI/DSI/FFT/PET."""
    conditions = [
        (df[col] == 1).to_numpy(dtype=bool, na_value=False) for col in ("oci", "dsi", "fft", "pet")
    ]
    choices = np.select(
        conditions,
        ["ocupado", "desocupado", "inactivo", "inactivo"],
        default="fuera_pet",
    )
    return pd.Series(choices, index=df.index, dtype="string")


def rango_edad(edad: pd.Series) -> pd.Series:
    bins = [r[0] for r in RANGOS_EDAD] + [RANGOS_EDAD[-1][1] + 1]
    labels = [r[2] for r in RANGOS_EDAD]
    return pd.cut(edad.astype("Float64"), bins=bins, labels=labels, right=False).astype("string")


def informalidad(df: pd.DataFrame) -> pd.Series:
    """Proxy de informalidad: ocupado que no cotiza a pensión (P6920 = 2).

    1 = informal, 0 = cotiza o ya es pensionado, <NA> = no aplica / sin dato.
    """
    result = pd.Series(pd.NA, index=df.index, dtype="Int8")
    ocupado = df["oci"] == 1
    result[ocupado & (df["cotiza_pension"] == 2)] = 1
    result[ocupado & df["cotiza_pension"].isin([1, 3])] = 0
    return result


def derive(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["periodo"] = (df["anio"] * 100 + df["mes"]).astype("Int64")
    df["condicion"] = condicion_laboral(df)
    df["rango_edad"] = rango_edad(df["edad"])
    df["grupo_educativo"] = df["nivel_educativo"].map(
        {code: group for code, (_, group) in NIVEL_EDUCATIVO.items()}
    ).astype("string")
    df["rama_seccion"] = df["rama2d"].map(DIVISION_A_SECCION).astype("string")
    df["informal"] = informalidad(df)
    return df


def transform_month(
    raw_modules: dict[Module, pd.DataFrame],
) -> tuple[pd.DataFrame, TransformReport]:
    """Pipeline completo de transformación para un mes."""
    report = TransformReport()
    normalized = {m: normalize_module(df, m) for m, df in raw_modules.items()}
    df = merge_modules(normalized, report)
    df = cast_types(df)
    df = clean(df, report)
    df = derive(df)
    report.rows_out = len(df)
    return df[FACT_FIELDS].reset_index(drop=True), report
