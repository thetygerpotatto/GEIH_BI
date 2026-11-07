"""Catálogos (dimensiones) de la GEIH Marco 2018, según el diccionario del DANE."""
from __future__ import annotations

DEPARTAMENTOS: dict[str, str] = {
    "05": "Antioquia", "08": "Atlántico", "11": "Bogotá D.C.", "13": "Bolívar",
    "15": "Boyacá", "17": "Caldas", "18": "Caquetá", "19": "Cauca", "20": "Cesar",
    "23": "Córdoba", "25": "Cundinamarca", "27": "Chocó", "41": "Huila",
    "44": "La Guajira", "47": "Magdalena", "50": "Meta", "52": "Nariño",
    "54": "Norte de Santander", "63": "Quindío", "66": "Risaralda", "68": "Santander",
    "70": "Sucre", "73": "Tolima", "76": "Valle del Cauca", "81": "Arauca",
    "85": "Casanare", "86": "Putumayo", "88": "San Andrés", "91": "Amazonas",
    "94": "Guainía", "95": "Guaviare", "97": "Vaupés", "99": "Vichada",
}

SEXO: dict[int, str] = {1: "Hombre", 2: "Mujer"}

CLASE: dict[int, str] = {1: "Cabecera (urbano)", 2: "Centros poblados y rural disperso"}

CONDICION: dict[str, str] = {
    "ocupado": "Ocupado",
    "desocupado": "Desocupado",
    "inactivo": "Fuera de la fuerza de trabajo",
    "fuera_pet": "Fuera de la población en edad de trabajar",
}

# P3042 - nivel educativo más alto alcanzado -> grupo analítico
NIVEL_EDUCATIVO: dict[int, tuple[str, str]] = {
    1: ("Ninguno", "ninguno"),
    2: ("Preescolar", "ninguno"),
    3: ("Básica primaria", "primaria"),
    4: ("Básica secundaria", "secundaria"),
    5: ("Media académica", "media"),
    6: ("Media técnica", "media"),
    7: ("Normalista", "media"),
    8: ("Técnica profesional", "tecnica_tecnologica"),
    9: ("Tecnológica", "tecnica_tecnologica"),
    10: ("Universitaria", "universitaria"),
    11: ("Especialización", "posgrado"),
    12: ("Maestría", "posgrado"),
    13: ("Doctorado", "posgrado"),
    99: ("No sabe, no informa", "sin_informacion"),
}

GRUPO_EDUCATIVO: dict[str, str] = {
    "ninguno": "Ninguno / preescolar",
    "primaria": "Básica primaria",
    "secundaria": "Básica secundaria",
    "media": "Media",
    "tecnica_tecnologica": "Técnica / tecnológica",
    "universitaria": "Universitaria",
    "posgrado": "Posgrado",
    "sin_informacion": "Sin información",
}

# P6430 - posición ocupacional en el empleo principal
POSICION_OCUPACIONAL: dict[int, str] = {
    1: "Obrero o empleado de empresa particular",
    2: "Obrero o empleado del gobierno",
    3: "Empleado doméstico",
    4: "Trabajador por cuenta propia",
    5: "Patrón o empleador",
    6: "Trabajador familiar sin remuneración",
    7: "Trabajador sin remuneración en empresas de otros hogares",
    8: "Jornalero o peón",
    9: "Otro",
}

# Rangos de edad (límite inferior inclusivo); 15-28 es la definición DANE de "jóvenes"
RANGOS_EDAD: list[tuple[int, int, str]] = [
    (0, 14, "0-14"),
    (15, 28, "15-28"),
    (29, 44, "29-44"),
    (45, 59, "45-59"),
    (60, 200, "60+"),
]

# CIIU Rev. 4 A.C.: división (2 dígitos) -> sección
_SECCIONES_CIIU: list[tuple[int, int, str, str]] = [
    (1, 3, "A", "Agricultura, ganadería, silvicultura y pesca"),
    (5, 9, "B", "Explotación de minas y canteras"),
    (10, 33, "C", "Industrias manufactureras"),
    (35, 35, "D", "Electricidad, gas y aire acondicionado"),
    (36, 39, "E", "Agua, alcantarillado y gestión de desechos"),
    (41, 43, "F", "Construcción"),
    (45, 47, "G", "Comercio y reparación de vehículos"),
    (49, 53, "H", "Transporte y almacenamiento"),
    (55, 56, "I", "Alojamiento y servicios de comida"),
    (58, 63, "J", "Información y comunicaciones"),
    (64, 66, "K", "Actividades financieras y de seguros"),
    (68, 68, "L", "Actividades inmobiliarias"),
    (69, 75, "M", "Actividades profesionales, científicas y técnicas"),
    (77, 82, "N", "Actividades de servicios administrativos y de apoyo"),
    (84, 84, "O", "Administración pública y defensa"),
    (85, 85, "P", "Educación"),
    (86, 88, "Q", "Salud humana y asistencia social"),
    (90, 93, "R", "Actividades artísticas y de entretenimiento"),
    (94, 96, "S", "Otras actividades de servicios"),
    (97, 98, "T", "Actividades de los hogares como empleadores"),
    (99, 99, "U", "Organizaciones extraterritoriales"),
]

RAMA_SECCION: dict[str, str] = {letra: nombre for _, _, letra, nombre in _SECCIONES_CIIU}


DIVISION_A_SECCION: dict[int, str] = {
    d: letra for desde, hasta, letra, _ in _SECCIONES_CIIU for d in range(desde, hasta + 1)
}

MESES: dict[int, str] = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}
