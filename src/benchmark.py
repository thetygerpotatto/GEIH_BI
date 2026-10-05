#!/usr/bin/env python3
"""
Taller de pruebas de rendimiento - GEIH (DANE) - Prototipo del dashboard.

Operaciones medidas (cada una con DOS soluciones):
  CARGA  : A) csv.reader + dict (Python puro -> list[Registro])
           B) pandas.read_csv + merge (DataFrame)
  EST. 1 : jovenes 15-28 anios, regimen Subsidiado, buscando trabajo
  EST. 2 : ingreso laboral promedio de ocupados con educacion universitaria o
           mas, por departamento y sexo
  EST. 3 : ocupados por regimen de salud x sexo x area (urbano/rural)
           A) bucles en Python + dict   B) pandas (mascaras / groupby)

Uso:
  python benchmark.py --datos dataset/CSV [otra/carpeta ...] --out resultados.json
"""
import argparse
import csv
import glob
import json
import os
import statistics
import time
from collections import defaultdict
from typing import NamedTuple, Optional

import pandas as pd

ENC = "latin-1"
SEP = ";"
KEY = ["PER", "MES", "DIRECTORIO", "SECUENCIA_P", "ORDEN"]

# nombre logico del archivo -> patron (los nombres reales tienen espacios no separables)
ARCHIVOS = {
    "carac": "Caracter*.CSV",
    "ft": "Fuerza*.CSV",
    "ocu": "Ocupados.CSV",
}
COLS = {
    "carac": KEY + ["DPTO", "CLASE", "P3271", "P6040", "P6100", "P3042", "FEX_C18"],
    "ft": KEY + ["P6240"],
    "ocu": KEY + ["P6430", "P6800", "INGLABO"],
}


class Registro(NamedTuple):
    """Registro depurado (12 variables)."""
    dpto: str
    clase: int            # 1 urbano (cabecera), 2 rural
    sexo: int             # 1 hombre, 2 mujer
    edad: int
    regimen: int          # 1 contributivo, 2 especial, 3 subsidiado
    educ: Optional[int]   # P3042 (10 universitaria, 11-13 posgrado)
    actividad: Optional[int]  # P6240 (1 trabajando, 2 buscando trabajo ...)
    posicion: Optional[int]   # P6430 (solo ocupados)
    horas: Optional[int]      # P6800 (solo ocupados)
    ingreso: Optional[float]  # INGLABO (solo ocupados)
    fex: float            # factor de expansion
    mes: int


def ruta(carpeta, clave):
    r = glob.glob(os.path.join(carpeta, ARCHIVOS[clave]))
    if not r:
        raise FileNotFoundError(f"No se encontro {ARCHIVOS[clave]} en {carpeta}")
    return r[0]


# ------------------------------------------------------------------ utilidades
def _int(s):
    try:
        return int(s) if s else None
    except ValueError:
        return None


def _float(s):
    try:
        return float(s) if s else None
    except ValueError:
        return None


# ------------------------------------------------------------------ CARGA A
def cargar_python(carpetas):
    """Solucion A: csv.reader + diccionarios (hash join) -> list[Registro]."""
    registros = []
    for carpeta in carpetas:
        # 1) indices de los modulos laborales (clave -> datos)
        def leer(clave):
            with open(ruta(carpeta, clave), encoding=ENC, newline="") as f:
                rd = csv.reader(f, delimiter=SEP)
                h = {c: i for i, c in enumerate(next(rd))}
                idx = [h[c] for c in COLS[clave]]
                for fila in rd:
                    yield [fila[i] for i in idx]

        ft = {}
        for r in leer("ft"):
            ft[tuple(r[:5])] = _int(r[5])
        ocu = {}
        for r in leer("ocu"):
            ocu[tuple(r[:5])] = (_int(r[5]), _int(r[6]), _float(r[7]))

        # 2) modulo base (personas) + depuracion + union
        for r in leer("carac"):
            k = tuple(r[:5])
            dpto, clase, sexo, edad, reg, educ, fex = r[5:12]
            edad, sexo, clase, reg = _int(edad), _int(sexo), _int(clase), _int(reg)
            # ---- depuracion basica
            if edad is None or not (0 <= edad <= 110):
                continue
            if sexo not in (1, 2) or clase not in (1, 2) or not dpto:
                continue
            if reg not in (1, 2, 3):          # vacio o 9 = "no sabe"
                continue
            fexf = _float(fex)
            if fexf is None or fexf <= 0:
                continue
            o = ocu.get(k)
            if o is not None:
                pos, horas, ing = o
                if ing is not None and ing <= 0:
                    ing = None
            else:
                pos = horas = ing = None
            registros.append(Registro(dpto, clase, sexo, edad, reg, _int(educ),
                                      ft.get(k), pos, horas, ing, fexf, _int(k[1])))
    return registros


# ------------------------------------------------------------------ CARGA B
def cargar_pandas(carpetas):
    """Solucion B: pandas.read_csv(usecols) + merge(how='left') -> DataFrame."""
    partes = []
    for carpeta in carpetas:
        def leer(clave):
            return pd.read_csv(ruta(carpeta, clave), sep=SEP, encoding=ENC,
                               usecols=COLS[clave], dtype=str)

        c, f, o = leer("carac"), leer("ft"), leer("ocu")
        df = c.merge(f, on=KEY, how="left").merge(o, on=KEY, how="left")
        partes.append(df)
    df = pd.concat(partes, ignore_index=True)

    df = df.rename(columns={"DPTO": "dpto", "CLASE": "clase", "P3271": "sexo",
                            "P6040": "edad", "P6100": "regimen", "P3042": "educ",
                            "P6240": "actividad", "P6430": "posicion",
                            "P6800": "horas", "INGLABO": "ingreso",
                            "FEX_C18": "fex", "MES": "mes"})
    for col in ["clase", "sexo", "edad", "regimen", "educ", "actividad",
                "posicion", "horas", "mes"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["ingreso"] = pd.to_numeric(df["ingreso"], errors="coerce")
    df["fex"] = pd.to_numeric(df["fex"], errors="coerce")
    # ---- depuracion basica (mismas reglas que la solucion A)
    m = (df["edad"].between(0, 110) & df["sexo"].isin([1, 2]) &
         df["clase"].isin([1, 2]) & df["dpto"].notna() &
         df["regimen"].isin([1, 2, 3]) & (df["fex"] > 0))
    df = df[m].copy()
    df.loc[df["ingreso"] <= 0, "ingreso"] = float("nan")
    return df[["dpto", "clase", "sexo", "edad", "regimen", "educ", "actividad",
               "posicion", "horas", "ingreso", "fex", "mes"]].reset_index(drop=True)


# ------------------------------------------------------------------ ESTADISTICA 1
# Jovenes (15-28), regimen subsidiado (3), buscando trabajo (actividad = 2)
def est1_python(regs):
    n = 0
    expandido = 0.0
    for r in regs:
        if 15 <= r.edad <= 28 and r.regimen == 3 and r.actividad == 2:
            n += 1
            expandido += r.fex
    return {"registros": n, "expandido": round(expandido, 2)}


def est1_pandas(df):
    m = df["edad"].between(15, 28) & (df["regimen"] == 3) & (df["actividad"] == 2)
    return {"registros": int(m.sum()), "expandido": round(float(df.loc[m, "fex"].sum()), 2)}


# ------------------------------------------------------------------ ESTADISTICA 2
# Ingreso laboral promedio de ocupados con educ >= universitaria, por dpto y sexo
def est2_python(regs):
    acc = defaultdict(lambda: [0, 0.0])
    for r in regs:
        if r.ingreso is not None and r.educ is not None and r.educ >= 10:
            a = acc[(r.dpto, r.sexo)]
            a[0] += 1
            a[1] += r.ingreso
    return {k: (v[0], v[1] / v[0]) for k, v in acc.items()}


def est2_pandas(df):
    d = df[df["ingreso"].notna() & (df["educ"] >= 10)]
    g = d.groupby(["dpto", "sexo"])["ingreso"].agg(["size", "mean"])
    return {k: (int(n), float(m)) for k, (n, m) in g.iterrows()}


# ------------------------------------------------------------------ ESTADISTICA 3
# Ocupados por regimen de salud x sexo x area
def est3_python(regs):
    acc = defaultdict(lambda: [0, 0.0])
    for r in regs:
        if r.posicion is not None:
            a = acc[(r.regimen, r.sexo, r.clase)]
            a[0] += 1
            a[1] += r.fex
    return {k: (v[0], v[1]) for k, v in acc.items()}


def est3_pandas(df):
    d = df[df["posicion"].notna()]
    g = d.groupby(["regimen", "sexo", "clase"]).agg(n=("fex", "size"), fex=("fex", "sum"))
    return {tuple(int(x) for x in k): (int(n), float(f)) for k, (n, f) in g.iterrows()}


# ------------------------------------------------------------------ medicion
def medir(fn, arg, reps):
    """Ejecuta fn(arg) reps veces; devuelve (ultimo_resultado, lista_ms)."""
    tiempos = []
    res = None
    for _ in range(reps):
        t0 = time.perf_counter_ns()
        res = fn(arg)
        tiempos.append((time.perf_counter_ns() - t0) / 1e6)
    return res, tiempos


def resumen(t):
    return {"media_ms": statistics.mean(t), "mediana_ms": statistics.median(t),
            "min_ms": min(t), "max_ms": max(t),
            "desv_ms": statistics.stdev(t) if len(t) > 1 else 0.0, "n": len(t)}


def casi_igual(a, b, tol=1e-6):
    if isinstance(a, dict):
        if set(a) != set(b):
            return False
        return all(casi_igual(a[k], b[k], tol) for k in a)
    if isinstance(a, (tuple, list)):
        return all(casi_igual(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, (int, float)):
        return abs(a - b) <= tol * max(1.0, abs(a))
    return a == b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datos", nargs="+", required=True, help="carpeta(s) con los CSV")
    ap.add_argument("--reps-carga", type=int, default=5)
    ap.add_argument("--reps-est", type=int, default=30)
    ap.add_argument("--out", default="resultados.json")
    a = ap.parse_args()

    out = {"carpetas": a.datos, "operaciones": {}}

    regs, t = medir(cargar_python, a.datos, a.reps_carga)
    out["operaciones"]["Carga A (csv + dict)"] = resumen(t)
    df, t = medir(cargar_pandas, a.datos, a.reps_carga)
    out["operaciones"]["Carga B (pandas)"] = resumen(t)
    out["registros_A"], out["registros_B"] = len(regs), len(df)
    out["variables"] = list(Registro._fields)
    assert len(regs) == len(df), "Las dos cargas deben producir los mismos registros"

    pares = [("Estadistica 1", est1_python, est1_pandas),
             ("Estadistica 2", est2_python, est2_pandas),
             ("Estadistica 3", est3_python, est3_pandas)]
    out["resultados"] = {}
    for nombre, fa, fb in pares:
        ra, ta = medir(fa, regs, a.reps_est)
        rb, tb = medir(fb, df, a.reps_est)
        assert casi_igual(ra, rb), f"{nombre}: las dos soluciones difieren"
        out["operaciones"][f"{nombre} A (bucle Python)"] = resumen(ta)
        out["operaciones"][f"{nombre} B (pandas)"] = resumen(tb)
        out["resultados"][nombre] = {str(k): v for k, v in
                                     (ra.items() if isinstance(ra, dict) and nombre != "Estadistica 1"
                                      else [("resultado", ra)])}

    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Registros depurados: {len(regs):,}  |  variables: {len(Registro._fields)}")
    print(f"{'Operacion':38s}{'media ms':>11s}{'min ms':>11s}{'desv':>9s}")
    for k, v in out["operaciones"].items():
        print(f"{k:38s}{v['media_ms']:11.2f}{v['min_ms']:11.2f}{v['desv_ms']:9.2f}")


if __name__ == "__main__":
    main()
