import json

from colabsh.core.cells import extract_cell_id, extract_cells, join_source


class TestExtractCellId:
    def test_none_result(self) -> None:
        assert extract_cell_id(None) is None

    def test_non_dict_result(self) -> None:
        assert extract_cell_id("string") is None
        assert extract_cell_id(42) is None

    def test_empty_content(self) -> None:
        assert extract_cell_id({"content": []}) is None

    def test_structured_new_cell_id(self) -> None:
        result = {"content": [{"text": json.dumps({"newCellId": "cell-123"})}]}
        assert extract_cell_id(result) == "cell-123"

    def test_raw_text_fallback(self) -> None:
        result = {"content": [{"text": "raw-id-456"}]}
        assert extract_cell_id(result) == "raw-id-456"

    def test_strips_whitespace(self) -> None:
        result = {"content": [{"text": "  cell-789  "}]}
        assert extract_cell_id(result) == "cell-789"

    def test_skips_empty_text(self) -> None:
        result = {"content": [{"text": ""}]}
        assert extract_cell_id(result) is None

    def test_skips_non_dict_items(self) -> None:
        result = {"content": ["not-a-dict", {"text": json.dumps({"newCellId": "abc"})}]}
        assert extract_cell_id(result) == "abc"

    def test_non_list_content(self) -> None:
        result = {"content": "not-a-list"}
        assert extract_cell_id(result) is None


class TestExtractCells:
    def test_none_result(self) -> None:
        assert extract_cells(None) == []

    def test_non_dict_result(self) -> None:
        assert extract_cells("string") == []

    def test_structured_content_cells(self) -> None:
        result = {"structuredContent": {"cells": [{"source": "print(1)", "cellType": "code"}]}}
        cells = extract_cells(result)
        assert len(cells) == 1
        assert cells[0]["source"] == "print(1)"

    def test_content_json_with_cells_key(self) -> None:
        """Falls back to content when structuredContent has non-list cells."""
        cells_data = [{"source": "x = 1"}, {"source": "x = 2"}]
        result = {
            "structuredContent": {"cells": "not-a-list"},
            "content": [{"text": json.dumps({"cells": cells_data})}],
        }
        cells = extract_cells(result)
        assert len(cells) == 2

    def test_content_json_list(self) -> None:
        """Falls back to content list when structuredContent is non-dict."""
        cells_data = [{"source": "a"}, {"source": "b"}]
        result = {
            "structuredContent": 42,
            "content": [{"text": json.dumps(cells_data)}],
        }
        cells = extract_cells(result)
        assert len(cells) == 2

    def test_invalid_json_in_content(self) -> None:
        result = {
            "structuredContent": {"cells": "not-a-list"},
            "content": [{"text": "not-json{"}],
        }
        assert extract_cells(result) == []

    def test_empty_structured_content_returns_empty(self) -> None:
        """structuredContent with no cells key returns [] from get()."""
        result = {"structuredContent": {}}
        assert extract_cells(result) == []

    def test_non_list_structured_cells_falls_through(self) -> None:
        """Non-list cells falls through to content check."""
        cells_data = [{"source": "fallback"}]
        result = {
            "structuredContent": {"cells": "not-a-list"},
            "content": [{"text": json.dumps({"cells": cells_data})}],
        }
        cells = extract_cells(result)
        assert len(cells) == 1
        assert cells[0]["source"] == "fallback"

    def test_non_dict_structured_content_falls_through(self) -> None:
        """Non-dict structuredContent falls through to content check."""
        cells_data = [{"source": "a"}]
        result = {
            "structuredContent": "not-a-dict",
            "content": [{"text": json.dumps(cells_data)}],
        }
        cells = extract_cells(result)
        assert len(cells) == 1

    def test_content_with_non_dict_items(self) -> None:
        result = {"structuredContent": {"cells": "skip"}, "content": ["not-a-dict"]}
        assert extract_cells(result) == []

    def test_content_with_empty_text(self) -> None:
        result = {"structuredContent": {"cells": "skip"}, "content": [{"text": ""}]}
        assert extract_cells(result) == []

    def test_non_list_content(self) -> None:
        result = {"structuredContent": {"cells": "skip"}, "content": "not-a-list"}
        assert extract_cells(result) == []


class TestJoinSource:
    def test_string_passthrough(self) -> None:
        assert join_source("hello") == "hello"

    def test_list_join(self) -> None:
        assert join_source(["line1\n", "line2\n"]) == "line1\nline2\n"

    def test_empty_list(self) -> None:
        assert join_source([]) == ""

    def test_non_string_non_list(self) -> None:
        assert join_source(42) == "42"
        assert join_source(None) == "None"
