import pytest

from geih_bi.controllers.admin import AdminController, ValidationError
from geih_bi.controllers.auth import AuthController
from geih_bi.models.repositories import AccessLogRepository, QualityRepository, UserRepository
from geih_bi.models.user import Role


@pytest.fixture
def admin(mongo_db, fast_hasher):
    return AdminController(UserRepository(mongo_db), QualityRepository(mongo_db), fast_hasher)


@pytest.fixture
def auth(mongo_db, fast_hasher):
    return AuthController(UserRepository(mongo_db), AccessLogRepository(mongo_db), fast_hasher)


@pytest.fixture
def ana(admin):
    return admin.create_user("ana", "Ana Gómez", "secreta123", Role.ANALISTA)


# ------------------------------------------------------------------ login
def test_login_success(auth, ana):
    user = auth.login("ana", "secreta123")
    assert user is not None and user.rol is Role.ANALISTA


def test_login_username_is_case_insensitive_and_trimmed(auth, ana):
    assert auth.login("  ANA ", "secreta123") is not None


@pytest.mark.parametrize("username, password", [("ana", "incorrecta"), ("nadie", "secreta123"), ("", ""), ("ana", "")])
def test_login_failures(auth, ana, username, password):
    assert auth.login(username, password) is None


def test_inactive_user_cannot_login(auth, admin, ana):
    root = admin.create_user("root", "Admin", "secreta123", Role.ADMINISTRADOR)
    admin.set_active(root, "ana", False)
    assert auth.login("ana", "secreta123") is None


def test_password_is_not_stored_in_plain_text(mongo_db, ana):
    doc = mongo_db["usuarios"].find_one({"_id": "ana"})
    assert "secreta123" not in str(doc)
    assert doc["password_hash"].startswith("$2")


def test_login_attempts_are_logged(auth, ana, mongo_db):
    auth.login("ana", "secreta123")
    auth.login("ana", "mala")
    assert [d["exitoso"] for d in mongo_db["bitacora_accesos"].find().sort("fecha", 1)] == [True, False]


# ------------------------------------------------------------- usuarios
@pytest.mark.parametrize(
    "username, nombre, password, message",
    [
        ("ab", "Nombre", "secreta123", "3 a 30"),
        ("con espacio", "Nombre", "secreta123", "3 a 30"),
        ("valido", "  ", "secreta123", "nombre"),
        ("valido", "Nombre", "corta", "8 caracteres"),
    ],
)
def test_create_user_validation(admin, username, nombre, password, message):
    with pytest.raises(ValidationError, match=message):
        admin.create_user(username, nombre, password, Role.GERENTE)


def test_duplicate_user_is_rejected(admin, ana):
    with pytest.raises(ValidationError, match="Ya existe"):
        admin.create_user("ANA", "Otra Ana", "secreta123", Role.GERENTE)


def test_admin_cannot_deactivate_self(admin):
    root = admin.create_user("root", "Admin", "secreta123", Role.ADMINISTRADOR)
    with pytest.raises(ValidationError, match="propia"):
        admin.set_active(root, "root", False)


def test_last_active_admin_cannot_be_deactivated(admin):
    root = admin.create_user("root", "Admin", "secreta123", Role.ADMINISTRADOR)
    other = admin.create_user("otro", "Otro", "secreta123", Role.ANALISTA)
    with pytest.raises(ValidationError, match="al menos un administrador"):
        admin.set_active(other, "root", False)


def test_set_active_unknown_user(admin):
    root = admin.create_user("root", "Admin", "secreta123", Role.ADMINISTRADOR)
    with pytest.raises(ValidationError, match="No existe"):
        admin.set_active(root, "fantasma", False)


# --------------------------------------------------------------- calidad
def test_quality_report(admin, mongo_db):
    QualityRepository(mongo_db).replace_all([
        {"periodo": 202501, "archivo": "2025/Enero.zip", "filas_entrada": {"caracteristicas": 10},
         "duplicados_eliminados": {"a": 1}, "huerfanos": {"a": 0}, "sin_factor_expansion": 0,
         "valores_anulados": {"edad": 2}, "filas_salida": 9, "td": 11.6, "problemas": []},
        {"periodo": 202502, "archivo": "2025/Febrero.zip", "filas_entrada": {"caracteristicas": 10},
         "duplicados_eliminados": {}, "huerfanos": {}, "sin_factor_expansion": 0,
         "valores_anulados": {}, "filas_salida": 10, "td": 45.0, "problemas": ["TD fuera de rango"]},
    ])
    df = admin.quality_report()
    assert df["Estado"].tolist() == ["Válido", "Con problemas"]
    assert df.loc[0, "Duplicados"] == 1 and df.loc[0, "Valores anulados"] == 2


def test_quality_report_empty(admin):
    assert admin.quality_report().empty
