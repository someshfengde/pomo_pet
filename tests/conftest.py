"""Never let CLI tests change the developer's real preferences."""

import pytest


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setattr("pomo_pet.core.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("pomo_pet.core.config.CONFIG_FILE", tmp_path / "config.json")
