# SPDX-FileCopyrightText: 2026-present Onuralp SEZER <thunderbirdtr@gmail.com>
#
# SPDX-License-Identifier: Apache-2.0

"""Playwright-based browser automation for auto-connecting to Google Colab.

!!! note "Optional dependency"
    Requires `playwright`. Install with `pip install colabsh[auto]`
    and run `playwright install chromium` once.
"""

import logging
from pathlib import Path
from typing import Any

from colabsh.constants import (
    BROWSER_PROFILE_DIR,
    CHROME_ARGS,
    COLAB_URL,
    GPU_TYPES,
    MCP_ACCEPT_BUTTON_TEXT,
    PLAYWRIGHT_ACCEPT_TIMEOUT,
    PLAYWRIGHT_NAV_TIMEOUT,
    RUNTIME_DIALOG_TIMEOUT,
)
from colabsh.core.config import CONFIG_DIR


def is_playwright_available() -> bool:
    """Check if playwright is importable.

    Returns:
        `True` if the `playwright` package is installed.
    """
    try:
        import playwright.async_api  # noqa: F401

        return True
    except ImportError:
        return False


def get_user_data_dir() -> Path:
    """Return path to persistent browser profile directory.

    Returns:
        The path to `~/.config/colabsh/browser-profile/` (platform-specific).
    """
    return CONFIG_DIR / BROWSER_PROFILE_DIR


async def auto_connect(url: str, *, headless: bool = True, user_data_dir: str | None = None) -> Any:
    """Launch browser, navigate to Colab URL, and accept the MCP proxy dialog.

    Uses a persistent browser context so that Google login sessions
    are preserved across runs. Pass an existing browser profile via
    `user_data_dir` to reuse your Google login session.

    Args:
        url: The full Colab URL with MCP proxy token and port in the hash.
        headless: If `True`, run the browser without a visible window.
        user_data_dir: Path to a browser profile directory. If `None`,
            uses the default colabsh profile.

    Returns:
        The Playwright `Page` object. Must be kept alive for the
        WebSocket connection to persist.

    Raises:
        RuntimeError: If Playwright is not installed or the accept button
            is not found within the timeout.

    !!! example "Usage"
        === "Default profile"
            ```python
            page = await auto_connect("https://colab.research.google.com/...", headless=True)
            ```

        === "Existing Chrome profile"
            ```python
            page = await auto_connect(
                "https://colab.research.google.com/...",
                user_data_dir="~/.config/google-chrome",
            )
            ```
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError as e:
        raise RuntimeError(
            "Playwright is not installed. Run: pip install colabsh[auto] "
            "&& playwright install chromium"
        ) from e

    profile_path = Path(user_data_dir) if user_data_dir else get_user_data_dir()
    profile_path.mkdir(parents=True, exist_ok=True)
    logging.info("Using browser profile: %s", profile_path)

    pw = await async_playwright().start()
    try:
        context = await pw.chromium.launch_persistent_context(
            str(profile_path),
            headless=headless,
            channel="chrome",
            args=CHROME_ARGS,
        )
    except Exception as e:
        await pw.stop()
        error_msg = str(e)
        logging.error("Browser launch failed: %s", error_msg)
        raise RuntimeError(
            f"Failed to launch browser with profile {profile_path}: {error_msg}"
        ) from e

    page = await context.new_page()

    # Close any extra tabs
    for p in context.pages:
        if p != page:
            await p.close()

    logging.info("Navigating to Colab: %s", url[:80])
    try:
        await page.goto(url, timeout=PLAYWRIGHT_NAV_TIMEOUT, wait_until="domcontentloaded")
    except Exception as nav_err:
        logging.error("Navigation failed: %s", nav_err)
        raise RuntimeError(f"Failed to navigate to Colab: {nav_err}") from nav_err
    logging.info("Navigation complete. Page URL: %s", page.url)

    # Check if redirected to Google login
    if "accounts.google.com" in page.url:
        raise RuntimeError("Not logged in to Google. Run 'colabsh login' first to authenticate.")

    # Wait for and click the MCP accept button
    # Use get_by_role for reliable matching of Material Design buttons
    try:
        accept_btn = page.get_by_role("button", name=MCP_ACCEPT_BUTTON_TEXT, exact=True)
        await accept_btn.wait_for(timeout=PLAYWRIGHT_ACCEPT_TIMEOUT, state="visible")
        await accept_btn.click()
        logging.info("MCP proxy accept button clicked")
    except Exception:
        # Save screenshot for debugging
        screenshot_path = CONFIG_DIR / "debug-screenshot.png"
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=str(screenshot_path))
            logging.warning(
                "Accept button not found. Screenshot saved to %s. Page title: %s, URL: %s",
                screenshot_path,
                await page.title(),
                page.url,
            )
        except Exception as screenshot_err:
            logging.warning("Accept button not found and screenshot failed: %s", screenshot_err)

    # Store references to prevent garbage collection
    page._pw_instance = pw  # type: ignore[attr-defined]

    return page


async def login(*, headless: bool = False) -> None:
    """Open a visible browser for the user to log in to Google.

    The login session is persisted to the browser profile directory
    so that subsequent `--auto` runs can use it.

    Args:
        headless: Should be `False` (default) for interactive login.

    !!! example "Usage"
        ```bash
        colabsh login
        ```
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError as e:
        raise RuntimeError(
            "Playwright is not installed. Run: pip install colabsh[auto] "
            "&& playwright install chromium"
        ) from e

    user_data_dir = get_user_data_dir()
    user_data_dir.mkdir(parents=True, exist_ok=True)

    pw = await async_playwright().start()
    context = await pw.chromium.launch_persistent_context(
        str(user_data_dir),
        headless=headless,
        channel="chrome",
        args=CHROME_ARGS,
    )

    page = context.pages[0] if context.pages else await context.new_page()

    # Navigate to Colab which will redirect to Google login if needed
    await page.goto(COLAB_URL, wait_until="domcontentloaded")
    logging.info("Browser opened at %s", page.url)

    # If already logged in, let the user know
    if "accounts.google.com" not in page.url:
        logging.info("Already logged in to Google!")
        input("Already logged in. Press Enter to save session and close...")
    else:
        input("Please log in to Google in the browser, then press Enter here...")

    # context.close() flushes cookies to disk
    await context.close()
    await pw.stop()
    logging.info("Login session saved to %s", user_data_dir)


async def change_runtime_type(page: Any, gpu_type: str) -> None:
    """Change the Colab runtime hardware accelerator via the UI.

    Clicks through: Runtime menu > Change runtime type > select GPU > Save.
    After saving, Colab restarts the runtime which causes a WebSocket
    disconnect. The caller should handle reconnection.

    Args:
        page: The Playwright `Page` object from `auto_connect`.
        gpu_type: GPU shorthand (e.g. `"t4"`, `"a100"`, `"cpu"`).

    Raises:
        ValueError: If `gpu_type` is not a valid option.
        RuntimeError: If any UI interaction fails.

    !!! example "Usage"
        ```python
        await change_runtime_type(page, "t4")
        ```
    """
    display_name = GPU_TYPES.get(gpu_type.lower())
    if not display_name:
        valid = ", ".join(GPU_TYPES.keys())
        raise ValueError(f"Unknown GPU type: {gpu_type}. Valid options: {valid}")

    timeout = RUNTIME_DIALOG_TIMEOUT
    logging.info("Changing runtime to: %s (%s)", gpu_type, display_name)

    try:
        # Step 1: Click Runtime menu
        runtime_menu = page.get_by_text("Runtime", exact=True).first
        await runtime_menu.click()
        logging.info("Opened Runtime menu")

        # Step 2: Click "Change runtime type"
        change_item = page.get_by_text("Change runtime type")
        await change_item.wait_for(timeout=timeout, state="visible")
        await change_item.click()
        logging.info("Opened runtime type dialog")

        # Step 3: Click the radio button for the hardware accelerator
        # Colab uses radio buttons, not a dropdown
        radio = page.get_by_role("radio", name=display_name)
        await radio.wait_for(timeout=timeout, state="visible")
        await radio.click()
        logging.info("Selected: %s", display_name)

        # Step 4: Click Save
        save_btn = page.get_by_role("button", name="Save")
        await save_btn.click()
        logging.info("Runtime type saved. Colab will restart the runtime.")
    except Exception as e:
        # Save screenshot for debugging
        screenshot_path = CONFIG_DIR / "debug-gpu-screenshot.png"
        try:
            await page.screenshot(path=str(screenshot_path))
            logging.error(
                "GPU selection failed. Screenshot saved to %s: %s",
                screenshot_path,
                e,
            )
        except Exception:
            logging.error("GPU selection failed: %s", e)
        raise RuntimeError(f"Failed to change runtime type to {gpu_type}: {e}") from e


async def close_page(page: Any) -> None:
    """Clean up a Playwright page and its browser context.

    Args:
        page: The Playwright `Page` object returned by `auto_connect`.
    """
    try:
        context = page.context
        pw = getattr(page, "_pw_instance", None)
        await context.close()
        if pw:
            await pw.stop()
    except Exception as e:
        logging.warning("Error closing browser: %s", e)
