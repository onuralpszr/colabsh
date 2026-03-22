from unittest.mock import MagicMock, patch

from colabsh.constants import QR_BLOCK_CHAR, QR_SPACE_CHAR
from colabsh.core.qr import render_qr


class TestRenderQr:
    def test_returns_none_when_qrcode_not_installed(self) -> None:
        with patch.dict("sys.modules", {"qrcode": None}):
            result = render_qr("https://example.com")
        assert result is None

    def test_renders_qr_code(self) -> None:
        mock_qr_instance = MagicMock()
        mock_qr_instance.get_matrix.return_value = [
            [True, False, True],
            [False, True, False],
        ]

        mock_qrcode = MagicMock()
        mock_qrcode.QRCode.return_value = mock_qr_instance
        mock_qrcode.constants.ERROR_CORRECT_L = 0

        with patch.dict("sys.modules", {"qrcode": mock_qrcode}):
            result = render_qr("https://example.com")

        assert result is not None
        lines = result.split("\n")
        assert len(lines) == 2
        assert lines[0] == QR_BLOCK_CHAR + QR_SPACE_CHAR + QR_BLOCK_CHAR
        assert lines[1] == QR_SPACE_CHAR + QR_BLOCK_CHAR + QR_SPACE_CHAR

    def test_calls_qrcode_with_correct_params(self) -> None:
        mock_qr_instance = MagicMock()
        mock_qr_instance.get_matrix.return_value = [[True]]

        mock_qrcode = MagicMock()
        mock_qrcode.QRCode.return_value = mock_qr_instance
        mock_qrcode.constants.ERROR_CORRECT_L = 0

        with patch.dict("sys.modules", {"qrcode": mock_qrcode}):
            render_qr("https://test.com")

        mock_qr_instance.add_data.assert_called_once_with("https://test.com")
        mock_qr_instance.make.assert_called_once_with(fit=True)

    def test_empty_matrix(self) -> None:
        mock_qr_instance = MagicMock()
        mock_qr_instance.get_matrix.return_value = []

        mock_qrcode = MagicMock()
        mock_qrcode.QRCode.return_value = mock_qr_instance
        mock_qrcode.constants.ERROR_CORRECT_L = 0

        with patch.dict("sys.modules", {"qrcode": mock_qrcode}):
            result = render_qr("https://test.com")

        assert result == ""
