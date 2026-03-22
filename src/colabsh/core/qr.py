# SPDX-FileCopyrightText: 2026-present Onuralp SEZER <thunderbirdtr@gmail.com>
#
# SPDX-License-Identifier: Apache-2.0

"""QR code generation for terminal display."""

from colabsh.constants import QR_BLOCK_CHAR, QR_BORDER, QR_BOX_SIZE, QR_SPACE_CHAR, QR_VERSION


def render_qr(url: str) -> str | None:
    """Render a QR code as ASCII art. Returns None if qrcode is not installed."""
    try:
        import qrcode  # type: ignore[import-untyped]
    except ImportError:
        return None

    qr = qrcode.QRCode(
        version=QR_VERSION,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=QR_BOX_SIZE,
        border=QR_BORDER,
    )
    qr.add_data(url)
    qr.make(fit=True)

    matrix = qr.get_matrix()
    lines: list[str] = []
    for row in matrix:
        line = ""
        for cell in row:
            line += QR_BLOCK_CHAR if cell else QR_SPACE_CHAR
        lines.append(line)
    return "\n".join(lines)
