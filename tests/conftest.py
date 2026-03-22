from collections.abc import Generator
from typing import Any
from unittest.mock import patch

import pytest
from click.testing import CliRunner


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture(autouse=True)
def _disable_history_writes() -> Generator[None, None, None]:
    """Prevent tests from writing to the real history file."""
    with patch("colabsh.core.history.is_history_enabled", return_value=False):
        yield


def make_click_context(**kwargs: Any) -> dict[str, Any]:
    """Create a Click context obj dict for testing."""
    defaults: dict[str, Any] = {
        "human": False,
        "verbose": False,
    }
    defaults.update(kwargs)
    return defaults
