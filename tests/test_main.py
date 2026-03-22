from click.testing import CliRunner

from colabsh.main import cli


class TestCli:
    def test_help(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "colabsh" in result.output.lower()

    def test_json_flag(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["--json", "--help"])
        assert result.exit_code == 0

    def test_start_help(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["start", "--help"])
        assert result.exit_code == 0

    def test_stop_help(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["stop", "--help"])
        assert result.exit_code == 0

    def test_status_help(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["status", "--help"])
        assert result.exit_code == 0

    def test_exec_help(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["exec", "--help"])
        assert result.exit_code == 0

    def test_repl_help(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["repl", "--help"])
        assert result.exit_code == 0

    def test_download_help(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["download", "--help"])
        assert result.exit_code == 0

    def test_tools_help(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["tools", "--help"])
        assert result.exit_code == 0

    def test_history_help(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["history", "--help"])
        assert result.exit_code == 0
