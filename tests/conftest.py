import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def settings_de_prueba(monkeypatch, tmp_path):
    from agente import config
    from agente.tienda import crear_base

    monkeypatch.setenv("GEMINI_API_KEY", "test")
    config.get_settings.cache_clear()
    settings = config.get_settings()
    settings.tienda_db = tmp_path / "tienda.db"
    crear_base(settings.tienda_db)
    yield
    config.get_settings.cache_clear()
