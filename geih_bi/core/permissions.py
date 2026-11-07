"""Control de acceso por rol: qué páginas y qué componentes ve cada usuario."""
from __future__ import annotations

from enum import Enum

from geih_bi.models.user import Role


class Page(str, Enum):
    TABLERO = "tablero"
    USUARIOS = "usuarios"
    CALIDAD = "calidad"


class Feature(str, Enum):
    GRAFICA_SEXO_EDAD = "grafica_sexo_edad"


ROLE_PAGES: dict[Role, list[Page]] = {
    Role.ADMINISTRADOR: [Page.USUARIOS, Page.CALIDAD],
    Role.ANALISTA: [Page.TABLERO],
    Role.GERENTE: [Page.TABLERO],
}

FEATURE_ROLES: dict[Feature, set[Role]] = {
    Feature.GRAFICA_SEXO_EDAD: {Role.ANALISTA},
}


def pages_for(role: Role) -> list[Page]:
    return list(ROLE_PAGES[role])


def can_access(role: Role, page: Page) -> bool:
    return page in ROLE_PAGES[role]


def has_feature(role: Role, feature: Feature) -> bool:
    return role in FEATURE_ROLES[feature]
