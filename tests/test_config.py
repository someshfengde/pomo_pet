"""Tests for persistent config."""

import json
import pytest
from unittest.mock import patch
from pomo_pet.core.config import Config


class TestConfigDefaults:
    def test_default_values(self):
        c = Config()
        assert c.default_pet == "avocado"
        assert c.work_minutes == 25
        assert c.break_minutes == 5
        assert c.volume == 80
        assert c.sound_enabled is True
        assert c.messages_file is None


class TestConfigLoad:
    def test_load_missing_file(self, tmp_path):
        with patch("pomo_pet.core.config.CONFIG_FILE", tmp_path / "nope.json"):
            c = Config.load()
            assert c.default_pet == "avocado"

    def test_load_valid_file(self, tmp_path):
        cfg = tmp_path / "config.json"
        cfg.write_text(json.dumps({"default_pet": "cat", "work_minutes": 30}))
        with patch("pomo_pet.core.config.CONFIG_FILE", cfg):
            c = Config.load()
            assert c.default_pet == "cat"
            assert c.work_minutes == 30
            assert c.break_minutes == 5  # default

    def test_load_ignores_unknown_fields(self, tmp_path):
        cfg = tmp_path / "config.json"
        cfg.write_text(json.dumps({"default_pet": "dog", "bogus": 42}))
        with patch("pomo_pet.core.config.CONFIG_FILE", cfg):
            c = Config.load()
            assert c.default_pet == "dog"
            assert not hasattr(c, "bogus")

    def test_load_corrupted_file(self, tmp_path):
        cfg = tmp_path / "config.json"
        cfg.write_text("NOT JSON")
        with patch("pomo_pet.core.config.CONFIG_FILE", cfg):
            c = Config.load()
            assert c.default_pet == "avocado"  # fallback


class TestConfigSave:
    def test_save_creates_file(self, tmp_path):
        cfg = tmp_path / "config.json"
        with patch("pomo_pet.core.config.CONFIG_FILE", cfg), \
             patch("pomo_pet.core.config.CONFIG_DIR", tmp_path):
            c = Config(default_pet="bunny", work_minutes=45)
            c.save()
            assert cfg.exists()
            data = json.loads(cfg.read_text())
            assert data["default_pet"] == "bunny"
            assert data["work_minutes"] == 45

    def test_update_and_save(self, tmp_path):
        cfg = tmp_path / "config.json"
        with patch("pomo_pet.core.config.CONFIG_FILE", cfg), \
             patch("pomo_pet.core.config.CONFIG_DIR", tmp_path):
            c = Config()
            c.update(work_minutes=30, volume=50)
            assert c.work_minutes == 30
            assert c.volume == 50
            data = json.loads(cfg.read_text())
            assert data["work_minutes"] == 30

@pytest.mark.parametrize("data", [[], None, 42, {"work_minutes": "30", "volume": -1}, {"sound_enabled": "false"}])
def test_invalid_config_recovers_defaults(tmp_path, data):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps(data))
    with patch("pomo_pet.core.config.CONFIG_FILE", cfg):
        config = Config.load()
        assert config.work_minutes == 25
        assert config.volume == 80
        assert config.sound_enabled is True


def test_invalid_update_leaves_memory_and_disk_unchanged(tmp_path):
    cfg = Config()
    cfg.save()
    with pytest.raises(ValueError):
        cfg.update(work_minutes=-1)
    assert cfg.work_minutes == 25
    assert Config.load().work_minutes == 25


def test_atomic_save_preserves_existing_file_when_replace_fails(tmp_path):
    cfg = Config()
    cfg.save()
    before = (tmp_path / 'config.json').read_text()
    with patch('pomo_pet.core.persistence.os.replace', side_effect=OSError('disk error')):
        with pytest.raises(OSError):
            cfg.update(work_minutes=40)
    assert (tmp_path / 'config.json').read_text() == before
    assert cfg.work_minutes == 25
    assert not list(tmp_path.glob('.config.json.*'))
