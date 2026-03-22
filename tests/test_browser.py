from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from colabsh.core.browser import get_user_data_dir, is_playwright_available


class TestIsPlaywrightAvailable:
    def test_available(self) -> None:
        mock_module = MagicMock()
        with patch.dict(
            "sys.modules", {"playwright": mock_module, "playwright.async_api": mock_module}
        ):
            assert is_playwright_available() is True

    def test_not_available(self) -> None:
        with patch.dict("sys.modules", {"playwright": None, "playwright.async_api": None}):
            assert is_playwright_available() is False


class TestGetUserDataDir:
    def test_returns_path(self) -> None:
        p = get_user_data_dir()
        assert isinstance(p, Path)
        assert p.name == "browser-profile"
        assert "colabsh" in str(p)


class TestAutoConnect:
    @pytest.mark.asyncio
    async def test_raises_when_playwright_missing(self) -> None:
        from colabsh.core.browser import auto_connect

        with (
            patch.dict("sys.modules", {"playwright.async_api": None}),
            pytest.raises(RuntimeError, match="Playwright is not installed"),
        ):
            await auto_connect("https://example.com")

    @pytest.mark.asyncio
    async def test_raises_when_not_logged_in(self) -> None:
        from colabsh.core.browser import auto_connect

        mock_new_page = AsyncMock()
        mock_new_page.url = "https://accounts.google.com/signin"
        mock_new_page.goto = AsyncMock()

        mock_context = AsyncMock()
        mock_context.pages = []
        mock_context.new_page = AsyncMock(return_value=mock_new_page)

        mock_pw = AsyncMock()
        mock_pw.chromium.launch_persistent_context = AsyncMock(return_value=mock_context)

        mock_async_pw = MagicMock()
        mock_async_pw.return_value.start = AsyncMock(return_value=mock_pw)

        mock_module = MagicMock()
        mock_module.async_playwright = mock_async_pw

        with (
            patch.dict("sys.modules", {"playwright.async_api": mock_module}),
            pytest.raises(RuntimeError, match="Not logged in"),
        ):
            await auto_connect("https://colab.research.google.com/test")


class TestLogin:
    @pytest.mark.asyncio
    async def test_raises_when_playwright_missing(self) -> None:
        from colabsh.core.browser import login

        with (
            patch.dict("sys.modules", {"playwright.async_api": None}),
            pytest.raises(RuntimeError, match="Playwright is not installed"),
        ):
            await login()


class TestClosePage:
    @pytest.mark.asyncio
    async def test_closes_context(self) -> None:
        from colabsh.core.browser import close_page

        mock_pw = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_page.context = mock_context
        mock_page._pw_instance = mock_pw

        await close_page(mock_page)

        mock_context.close.assert_awaited_once()
        mock_pw.stop.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handles_error_gracefully(self) -> None:
        from colabsh.core.browser import close_page

        mock_page = AsyncMock()
        mock_page.context = AsyncMock()
        mock_page.context.close = AsyncMock(side_effect=RuntimeError("test"))

        # Should not raise
        await close_page(mock_page)
