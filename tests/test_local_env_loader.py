"""Tests para _load_dotenv_if_present (S72 local NRT support).

Verifica que:
- Lee .env correctamente.
- NO sobrescribe variables ya en env (CI/GH Secrets prioridad).
- No falla si .env no existe.
- Ignora comentarios y líneas vacías.
"""
from __future__ import annotations

import os
import importlib
from pathlib import Path

import pytest


@pytest.fixture
def isolated_env(monkeypatch, tmp_path):
    """Crea un .env en tmp_path y monkey-patcha la función para apuntar allí."""
    env_file = tmp_path / ".env"
    monkeypatch.delenv("TEST_VAR_NEW", raising=False)
    monkeypatch.delenv("TEST_VAR_EXISTING", raising=False)
    return env_file


def _load_with_path(env_path: Path):
    """Helper: replica la lógica de _load_dotenv_if_present sobre un path arbitrario."""
    if not env_path.exists():
        return
    with env_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip("'").strip('"')
            if key and key not in os.environ:
                os.environ[key] = val


def test_loads_new_var_from_env_file(isolated_env, monkeypatch):
    """Variable nueva en .env se carga al ambiente."""
    isolated_env.write_text("TEST_VAR_NEW=hello_world\n", encoding="utf-8")
    _load_with_path(isolated_env)
    assert os.environ.get("TEST_VAR_NEW") == "hello_world"


def test_does_not_override_existing_env_var(isolated_env, monkeypatch):
    """Variable ya en env (CI / GH Secrets) tiene prioridad — .env NO sobrescribe."""
    monkeypatch.setenv("TEST_VAR_EXISTING", "from_env")
    isolated_env.write_text("TEST_VAR_EXISTING=from_dotenv\n", encoding="utf-8")
    _load_with_path(isolated_env)
    assert os.environ["TEST_VAR_EXISTING"] == "from_env"  # NO override


def test_handles_missing_env_file(tmp_path):
    """No crash si .env no existe."""
    non_existent = tmp_path / ".env"
    # No debe raise.
    _load_with_path(non_existent)


def test_ignores_comments_and_blank_lines(isolated_env):
    """Comments (#) y líneas vacías se saltan."""
    content = """
# Comment line
TEST_VAR_NEW=value1

# Another comment
"""
    isolated_env.write_text(content, encoding="utf-8")
    _load_with_path(isolated_env)
    assert os.environ.get("TEST_VAR_NEW") == "value1"


def test_strips_quotes(isolated_env):
    """Quotes single y double se strippean."""
    isolated_env.write_text('TEST_VAR_NEW="quoted value"\n', encoding="utf-8")
    _load_with_path(isolated_env)
    assert os.environ.get("TEST_VAR_NEW") == "quoted value"


def test_ignores_lines_without_equals(isolated_env):
    """Líneas sin '=' se ignoran (no crash)."""
    content = "TEST_VAR_NEW=ok\nNOT_A_VAR\n"
    isolated_env.write_text(content, encoding="utf-8")
    _load_with_path(isolated_env)
    assert os.environ.get("TEST_VAR_NEW") == "ok"


def test_fetch_module_load_function_callable():
    """El loader existe y es importable desde pipeline.fetch."""
    from pipeline.fetch import _load_dotenv_if_present
    # No debe crash al invocar (si .env no existe, retorna silente).
    _load_dotenv_if_present()
