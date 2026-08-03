import ast
import configparser
from pathlib import Path
from types import FunctionType


def load_env_helper(name: str) -> FunctionType:
    env_path = Path(__file__).resolve().parents[1] / "alembic" / "env.py"
    module = ast.parse(env_path.read_text())
    helper = next(
        node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == name
    )
    compiled = compile(
        ast.Module(body=[helper], type_ignores=[]), filename=str(env_path), mode="exec"
    )
    namespace: dict[str, object] = {}
    exec(compiled, namespace)
    return namespace[name]  # type: ignore[return-value]


def test_alembic_database_url_escapes_percent_signs_for_configparser() -> None:
    escape_url = load_env_helper("escape_database_url_for_alembic")
    database_url = (
        "postgresql+psycopg://happy_post_admin:example%2Bpassword%25"
        "@localhost:5432/happy_post"
    )

    escaped_url = escape_url(database_url)
    parser = configparser.ConfigParser()
    parser.add_section("alembic")
    parser.set("alembic", "sqlalchemy.url", escaped_url)

    assert escaped_url == database_url.replace("%", "%%")
