"""Tests for persistent config."""

import json
import pytest
from unittest.mock import patch
from src.core.config import Config


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
        with patch("src.core.config.CONFIG_FILE", tmp_path / "nope.json"):
            c = Config.load()
            assert c.default_pet == "avocado"

    def test_load_valid_file(self, tmp_path):
        cfg = tmp_path / "config.json"
        cfg.write_text(json.dumps({"default_pet": "cat", "work_minutes": 30}))
        with patch("src.core.config.CONFIG_FILE", cfg):
            c = Config.load()
            assert c.default_pet == "cat"
            assert c.work_minutes == 30
            assert c.break_minutes == 5  # default

    def test_load_ignores_unknown_fields(self, tmp_path):
        cfg = tmp_path / "config.json"
        cfg.write_text(json.dumps({"default_pet": "dog", "bogus": 42}))
        with patch("src.core.config.CONFIG_FILE", cfg):
            c = Config.load()
            assert c.default_pet == "dog"
            assert not hasattr(c, "bogus")

    def test_load_corrupted_file(self, tmp_path):
        cfg = tmp_path / "config.json"
        cfg.write_text("NOT JSON")
        with patch("src.core.config.CONFIG_FILE", cfg):
            c = Config.load()
            assert c.default_pet == "avocado"  # fallback


class TestConfigSave:
    def test_save_creates_file(self, tmp_path):
        cfg = tmp_path / "config.json"
        with patch("src.core.config.CONFIG_FILE", cfg), \
             patch("src.core.config.CONFIG_DIR", tmp_path):
            c = Config(default_pet="bunny", work_minutes=45)
            c.save()
            assert cfg.exists()
            data = json.loads(cfg.read_text())
            assert data["default_pet"] == "bunny"
            assert data["work_minutes"] == 45

    def test_update_and_save(self, tmp_path):
        cfg = tmp_path / "config.json"
        with patch("src.core.config.CONFIG_FILE", cfg), \
             patch("src.core.config.CONFIG_DIR", tmp_path):
            c = Config()
            c.update(work_minutes=30, volume=50)
            assert c.work_minutes == 30
            assert c.volume == 50
            data = json.loads(cfg.read_text())
            assert data["work_minutes"] == 30
