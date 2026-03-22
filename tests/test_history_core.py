from pathlib import Path
from typing import Any
from unittest.mock import patch

from colabsh.core import history as history_mod
from colabsh.core.history import (
    clear_history,
    get_history,
    get_history_path,
    get_notebook_history,
    is_history_enabled,
    record_notebook_event,
)


def _use_tmp_history(tmp_path: Path) -> Any:
    """Context manager to redirect history to a temp dir."""
    return patch.object(history_mod, "HISTORY_PATH", tmp_path / "history.json")


class TestIsHistoryEnabled:
    def test_default_enabled(self) -> None:
        with patch("colabsh.core.history.get_setting", return_value=True):
            assert is_history_enabled() is True

    def test_disabled(self) -> None:
        with patch("colabsh.core.history.get_setting", return_value=False):
            assert is_history_enabled() is False

    def test_missing_setting_defaults_true(self) -> None:
        with patch("colabsh.core.history.get_setting", return_value=True):
            assert is_history_enabled() is True


class TestRecordNotebookEvent:
    def test_record_new_notebook(self, tmp_path: Path) -> None:
        with (
            _use_tmp_history(tmp_path),
            patch("colabsh.core.history.is_history_enabled", return_value=True),
            patch("colabsh.core.history.ensure_config_dir"),
        ):
            record_notebook_event("nb-1", "vm_assign", variant="GPU", accelerator="T4")

            data = get_history()
            assert "nb-1" in data["notebooks"]
            entry = data["notebooks"]["nb-1"]
            assert entry["access_count"] == 1
            assert entry["events"][0]["event"] == "vm_assign"
            assert entry["events"][0]["variant"] == "GPU"
            assert entry["events"][0]["accelerator"] == "T4"
            assert "created_at" in entry
            assert "last_accessed_at" in entry

    def test_record_increments_access_count(self, tmp_path: Path) -> None:
        with (
            _use_tmp_history(tmp_path),
            patch("colabsh.core.history.is_history_enabled", return_value=True),
            patch("colabsh.core.history.ensure_config_dir"),
        ):
            record_notebook_event("nb-1", "exec")
            record_notebook_event("nb-1", "exec")
            record_notebook_event("nb-1", "repl_start")

            entry = get_notebook_history("nb-1")
            assert entry is not None
            assert entry["access_count"] == 3
            assert len(entry["events"]) == 3

    def test_record_with_endpoint(self, tmp_path: Path) -> None:
        with (
            _use_tmp_history(tmp_path),
            patch("colabsh.core.history.is_history_enabled", return_value=True),
            patch("colabsh.core.history.ensure_config_dir"),
        ):
            record_notebook_event("nb-1", "vm_assign", endpoint="ep-123")

            entry = get_notebook_history("nb-1")
            assert entry is not None
            assert entry["events"][0]["endpoint"] == "ep-123"

    def test_record_disabled(self, tmp_path: Path) -> None:
        with (
            _use_tmp_history(tmp_path),
            patch("colabsh.core.history.is_history_enabled", return_value=False),
        ):
            record_notebook_event("nb-1", "exec")

            data = get_history()
            assert data == {"notebooks": {}}

    def test_record_multiple_notebooks(self, tmp_path: Path) -> None:
        with (
            _use_tmp_history(tmp_path),
            patch("colabsh.core.history.is_history_enabled", return_value=True),
            patch("colabsh.core.history.ensure_config_dir"),
        ):
            record_notebook_event("nb-1", "exec")
            record_notebook_event("nb-2", "vm_assign")

            data = get_history()
            assert len(data["notebooks"]) == 2


class TestGetHistory:
    def test_empty_history(self, tmp_path: Path) -> None:
        with _use_tmp_history(tmp_path):
            data = get_history()
            assert data == {"notebooks": {}}

    def test_get_notebook_history_missing(self, tmp_path: Path) -> None:
        with _use_tmp_history(tmp_path):
            assert get_notebook_history("nonexistent") is None


class TestClearHistory:
    def test_clear_existing(self, tmp_path: Path) -> None:
        history_file = tmp_path / "history.json"
        history_file.write_text('{"notebooks": {}}')
        with patch.object(history_mod, "HISTORY_PATH", history_file):
            assert clear_history() is True
            assert not history_file.exists()

    def test_clear_nonexistent(self, tmp_path: Path) -> None:
        with _use_tmp_history(tmp_path):
            assert clear_history() is False


class TestGetHistoryPath:
    def test_returns_path(self) -> None:
        p = get_history_path()
        assert isinstance(p, Path)
        assert p.name == "history.json"
