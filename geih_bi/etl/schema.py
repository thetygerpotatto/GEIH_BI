"""Esquema de destino del ETL: qué columnas se toman de cada módulo y cómo se renombran.

Los nombres de origen son los del diccionario GEIH Marco 2018 (DANE). Las columnas que
falten en algún mes se crean vacías y se reportan, de modo que todos los meses
terminen con la misma estructura.
"""
from __future__ import annotations

from enum import Enum


class Module(str, Enum):
    CARACTERISTICAS = "caracteristicas"
    FUERZA_TRABAJO = "fuerza_trabajo"
    OCUPADOS = "ocupados"
    NO_OCUPADOS = "no_ocupados"


# Llave de persona dentro de un mes (vivienda, hogar, persona)
KEYS: list[str] = ["DIRECTORIO", "SECUENCIA_P", "ORDEN"]

MODULE_COLUMNS: dict[Module, dict[str, str]] = {
    # módulo base: contiene a todas las personas del hogar
    Module.CARACTERISTICAS: {
        "PER": "anio",
        "MES": "mes",
        "HOGAR": "hogar",
        "FEX_C18": "fex",
        "DPTO": "dpto",
        "AREA": "area",
        "CLASE": "clase",
        "P3271": "sexo",
        "P6040": "edad",
        "P3042": "nivel_educativo",
        "P6090": "afiliado_salud",
        "P6100": "regimen_salud",
    },
    Module.FUERZA_TRABAJO: {
        "PET": "pet",
        "FT": "ft",
        "FFT": "fft",
        "P6240": "actividad_principal",
    },
    Module.OCUPADOS: {
        "OCI": "oci",
        "INGLABO": "ingreso_laboral",
        "P6800": "horas_semanales",
        "P6430": "posicion_ocupacional",
        "RAMA2D_R4": "rama2d",
        "P6920": "cotiza_pension",
        "P3069": "tamano_empresa",
        "P6440": "tiene_contrato",
    },
    Module.NO_OCUPADOS: {
        "DSI": "dsi",
        "P7250": "semanas_buscando",
    },
}

INT_FIELDS: list[str] = [
    "anio", "mes", "hogar", "clase", "sexo", "edad", "nivel_educativo", "afiliado_salud",
    "regimen_salud", "pet", "ft", "fft", "actividad_principal", "oci", "horas_semanales",
    "posicion_ocupacional", "rama2d", "cotiza_pension", "tamano_empresa", "tiene_contrato",
    "dsi", "semanas_buscando",
]
FLOAT_FIELDS: list[str] = ["fex", "ingreso_laboral"]
FLAG_FIELDS: list[str] = ["pet", "ft", "fft", "oci", "dsi"]
STR_FIELDS: list[str] = ["dpto", "area"]

# Campos finales del hecho personas_mes (orden de la colección)
FACT_FIELDS: list[str] = [
    "anio", "mes", "periodo", "directorio", "secuencia_p", "orden", "hogar",
    "fex", "dpto", "area", "clase", "sexo", "edad", "rango_edad",
    "nivel_educativo", "grupo_educativo", "afiliado_salud", "regimen_salud",
    "pet", "ft", "fft", "oci", "dsi", "condicion", "actividad_principal",
    "ingreso_laboral", "horas_semanales", "posicion_ocupacional", "rama2d", "rama_seccion",
    "cotiza_pension", "informal", "tamano_empresa", "tiene_contrato", "semanas_buscando",
]
