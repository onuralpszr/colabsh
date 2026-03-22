import json
from unittest.mock import patch

from click.testing import CliRunner

from colabsh.main import cli


class TestHistoryList:
    def test_list_empty(self, cli_runner: CliRunner) -> None:
        with patch("colabsh.history.get_history", return_value={"notebooks": {}}):
            result = cli_runner.invoke(cli, ["--json", "history", "list"])

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["notebooks"] == []

    def test_list_with_entries(self, cli_runner: CliRunner) -> None:
        mock_data = {
            "notebooks": {
                "nb-1": {
                    "access_count": 5,
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "last_accessed_at": "2026-03-01T00:00:00+00:00",
                },
                "nb-2": {
                    "access_count": 2,
                    "created_at": "2026-02-01T00:00:00+00:00",
                    "last_accessed_at": "2026-03-15T00:00:00+00:00",
                },
            }
        }
        with patch("colabsh.history.get_history", return_value=mock_data):
            result = cli_runner.invoke(cli, ["--json", "history", "list"])

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert len(output) == 2
        assert output[0]["notebook_id"] == "nb-2"
        assert output[1]["notebook_id"] == "nb-1"

    def test_list_human_output(self, cli_runner: CliRunner) -> None:
        with patch("colabsh.history.get_history", return_value={"notebooks": {}}):
            result = cli_runner.invoke(cli, ["history", "list"])

        assert result.exit_code == 0
        assert "No history recorded" in result.output


class TestHistoryShow:
    def test_show_existing(self, cli_runner: CliRunner) -> None:
        mock_entry = {
            "access_count": 3,
            "created_at": "2026-01-01T00:00:00+00:00",
            "last_accessed_at": "2026-03-01T00:00:00+00:00",
            "events": [{"event": "exec", "timestamp": "2026-03-01T00:00:00+00:00"}],
        }
        with patch("colabsh.history.get_notebook_history", return_value=mock_entry):
            result = cli_runner.invoke(cli, ["--json", "history", "show", "nb-1"])

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["notebook_id"] == "nb-1"
        assert output["access_count"] == 3

    def test_show_nonexistent(self, cli_runner: CliRunner) -> None:
        with patch("colabsh.history.get_notebook_history", return_value=None):
            result = cli_runner.invoke(cli, ["history", "show", "nb-999"])

        assert result.exit_code == 1


class TestHistoryClear:
    def test_clear_with_confirmation(self, cli_runner: CliRunner) -> None:
        with patch("colabsh.history.clear_history", return_value=True):
            result = cli_runner.invoke(cli, ["history", "clear", "--yes"])

        assert result.exit_code == 0
        assert "cleared" in result.output.lower() or "deleted" in result.output.lower()

    def test_clear_empty(self, cli_runner: CliRunner) -> None:
        with patch("colabsh.history.clear_history", return_value=False):
            result = cli_runner.invoke(cli, ["history", "clear", "--yes"])

        assert result.exit_code == 0
        assert "empty" in result.output.lower() or "no history" in result.output.lower()

    def test_clear_aborted(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["history", "clear"], input="n\n")
        assert result.exit_code == 1


class TestHistoryPath:
    def test_path(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["history", "path"])

        assert result.exit_code == 0
        assert "history.json" in result.output


class TestHistoryToggle:
    def test_disable(self, cli_runner: CliRunner) -> None:
        with patch("colabsh.history.set_setting") as mock_set:
            result = cli_runner.invoke(cli, ["history", "toggle", "off"])

        assert result.exit_code == 0
        assert "disabled" in result.output.lower()
        mock_set.assert_called_once_with("history_enabled", False)

    def test_enable(self, cli_runner: CliRunner) -> None:
        with patch("colabsh.history.set_setting") as mock_set:
            result = cli_runner.invoke(cli, ["history", "toggle", "on"])

        assert result.exit_code == 0
        assert "enabled" in result.output.lower()
        mock_set.assert_called_once_with("history_enabled", True)
