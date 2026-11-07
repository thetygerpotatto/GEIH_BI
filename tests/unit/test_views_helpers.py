import pytest

from geih_bi.core.permissions import Feature, Page, can_access, has_feature, pages_for
from geih_bi.models.user import Role
from geih_bi.views.formatting import fmt_int, fmt_pct, fmt_pp, fmt_thousands
from geih_bi.views.session import SESSION_TIMEOUT_SECONDS, is_expired


@pytest.mark.parametrize(
    "role, pages",
    [(Role.ADMINISTRADOR, [Page.USUARIOS, Page.CALIDAD]), (Role.ANALISTA, [Page.TABLERO]), (Role.GERENTE, [Page.TABLERO])],
)
def test_pages_for_role(role, pages):
    assert pages_for(role) == pages


def test_admin_cannot_access_dashboard_and_gerente_cannot_admin():
    assert not can_access(Role.ADMINISTRADOR, Page.TABLERO)
    assert not can_access(Role.GERENTE, Page.USUARIOS)


def test_sex_age_chart_only_for_analista():
    assert has_feature(Role.ANALISTA, Feature.GRAFICA_SEXO_EDAD)
    assert not has_feature(Role.GERENTE, Feature.GRAFICA_SEXO_EDAD)


def test_spanish_number_formats():
    assert fmt_pct(10.26) == "10,3 %"
    assert fmt_pct(None) == "—"
    assert fmt_pp(-1.04) == "−1,0 p.p."
    assert fmt_pp(0.5) == "+0,5 p.p."
    assert fmt_pp(None) is None
    assert fmt_thousands(23_456_789) == "23.456,8 mil"
    assert fmt_int(3427494) == "3.427.494"


@pytest.mark.parametrize("last, now, expired", [(None, 100, True), (0, SESSION_TIMEOUT_SECONDS, False),
                                               (0, SESSION_TIMEOUT_SECONDS + 1, True)])
def test_session_expiry(last, now, expired):
    assert is_expired(last, now) is expired
