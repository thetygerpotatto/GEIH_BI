# GEIH_BI

Sistema de Business Intelligence para el análisis y predicción del mercado laboral en Colombia,
a partir de la Gran Encuesta Integrada de Hogares (GEIH, DANE) 2022–2025.

## Requisitos

- Python 3.11+
- Docker (para MongoDB)
- Los zips originales del DANE en `../GEIH_DATA/<año>/zipfiles/*.zip`
  (ruta configurable con `GEIH_DATA_DIR`)

## Instalación

```bash
python -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
docker compose up -d          # MongoDB en localhost:27017
```

## ETL

```bash
.venv/bin/python -m geih_bi.etl process   # zips -> data/processed/*.parquet + etl_report.json
.venv/bin/python -m geih_bi.etl load      # parquet -> MongoDB
.venv/bin/python -m geih_bi.etl run       # ambas etapas
```

| Etapa | Qué hace |
|---|---|
| Extracción (`etl/extract.py`) | Abre los zips mensuales (incluidos los zips anidados de 2023), identifica los 4 módulos usados aunque sus nombres tengan tildes mal codificadas o espacios no separables, detecta el separador (`,` en enero 2022, `;` en el resto) y lee solo las columnas necesarias por nombre. |
| Transformación (`etl/transform.py`) | Une Características + Fuerza de trabajo + Ocupados + No ocupados por `DIRECTORIO, SECUENCIA_P, ORDEN`; tipa los campos; elimina duplicados y registros sin factor de expansión; anula valores fuera de rango; deriva `condicion`, `rango_edad`, `grupo_educativo`, `rama_seccion` (CIIU) e `informal`. |
| Validación (`etl/validate.py`) | FT = OCI + DSI, ocupados dentro de la PET, un único periodo por archivo, TD en rango plausible. |
| Carga (`etl/load.py`) | Carga idempotente por periodo en MongoDB: hecho `personas_mes`, cubo `cubo_mensual`, dimensiones `dim_*` y bitácora `etl_ejecuciones`. |

Variables de entorno: `GEIH_DATA_DIR`, `GEIH_PROCESSED_DIR`, `MONGO_URI`, `MONGO_DB`, `GEIH_YEARS`.

## Modelo de datos (estrella)

- **Hecho `personas_mes`**: una persona encuestada en un mes (~3,4 M documentos).
- **Dimensiones**: `dim_tiempo`, `dim_departamento`, `dim_sexo`, `dim_clase`, `dim_rango_edad`,
  `dim_nivel_educativo`, `dim_grupo_educativo`, `dim_posicion_ocupacional`, `dim_rama`, `dim_condicion`.
- **Agregado `cubo_mensual`**: sumas ponderadas por periodo × departamento × zona × sexo × edad × educación.

Los indicadores (TD, TO, TGP) siempre se ponderan por `fex` (FEX_C18). Ver `geih_bi/analytics/indicators.py`.

## Pruebas

```bash
.venv/bin/python -m pytest --cov=geih_bi
```
