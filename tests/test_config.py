from pathlib import Path
from unittest.mock import patch

from colabsh.core.config import (
    CONFIG_DIR,
    SERVER_STATE_PATH,
    ensure_config_dir,
    get_setting,
    load_settings,
    save_settings,
    set_setting,
)


class TestConfigPaths:
    def test_config_dir_is_path(self) -> None:
        assert isinstance(CONFIG_DIR, Path)
        assert "colabsh" in str(CONFIG_DIR)

    def test_server_state_path(self) -> None:
        assert SERVER_STATE_PATH.parent == CONFIG_DIR
        assert SERVER_STATE_PATH.name == "server.json"


class TestEnsureConfigDir:
    def test_creates_dir(self, tmp_path: Path) -> None:
        test_dir = tmp_path / "test-config"
        from colabsh.core import config

        original = config.CONFIG_DIR
        config.CONFIG_DIR = test_dir
        try:
            result = ensure_config_dir()
            assert test_dir.exists()
            assert result == test_dir
        finally:
            config.CONFIG_DIR = original

    def test_idempotent(self, tmp_path: Path) -> None:
        test_dir = tmp_path / "test-config"
        test_dir.mkdir()
        from colabsh.core import config

        original = config.CONFIG_DIR
        config.CONFIG_DIR = test_dir
        try:
            ensure_config_dir()
            assert test_dir.exists()
        finally:
            config.CONFIG_DIR = original


class TestSettings:
    def test_load_settings_no_file(self, tmp_path: Path) -> None:
        with patch("colabsh.core.config.SETTINGS_PATH", tmp_path / "nonexistent.json"):
            result = load_settings()
        assert result == {}

    def test_save_and_load_settings(self, tmp_path: Path) -> None:
        settings_path = tmp_path / "settings.json"
        from colabsh.core import config

        original_settings = config.SETTINGS_PATH
        original_dir = config.CONFIG_DIR
        config.SETTINGS_PATH = settings_path
        config.CONFIG_DIR = tmp_path
        try:
            save_settings({"key": "value", "number": 42})
            result = load_settings()
            assert result == {"key": "value", "number": 42}
        finally:
            config.SETTINGS_PATH = original_settings
            config.CONFIG_DIR = original_dir

    def test_get_setting_default(self, tmp_path: Path) -> None:
        with patch("colabsh.core.config.SETTINGS_PATH", tmp_path / "nonexistent.json"):
            assert get_setting("missing") is None
            assert get_setting("missing", "default") == "default"

    def test_set_and_get_setting(self, tmp_path: Path) -> None:
        settings_path = tmp_path / "settings.json"
        from colabsh.core import config

        original_settings = config.SETTINGS_PATH
        original_dir = config.CONFIG_DIR
        config.SETTINGS_PATH = settings_path
        config.CONFIG_DIR = tmp_path
        try:
            set_setting("theme", "dark")
            assert get_setting("theme") == "dark"

            set_setting("theme", "light")
            assert get_setting("theme") == "light"
        finally:
            config.SETTINGS_PATH = original_settings
            config.CONFIG_DIR = original_dir
