import io
import json

from pydantic import BaseModel, Field

from colabsh.core.output import format_output, print_error, print_output


class SampleModel(BaseModel):
    name: str
    value_count: int = Field(..., alias="valueCount")


class TestFormatOutput:
    def test_dict_json(self) -> None:
        result = format_output({"key": "value"})
        parsed = json.loads(result)
        assert parsed == {"key": "value"}

    def test_dict_human(self) -> None:
        result = format_output({"key": "value"}, human=True)
        assert "key: value" in result

    def test_list_json(self) -> None:
        result = format_output([1, 2, 3])
        parsed = json.loads(result)
        assert parsed == [1, 2, 3]

    def test_list_human(self) -> None:
        result = format_output([{"a": 1}, {"a": 2}], human=True)
        assert "[0]" in result
        assert "[1]" in result
        assert "a: 1" in result

    def test_empty_list_human(self) -> None:
        result = format_output([], human=True)
        assert result == "(empty)"

    def test_nested_dict_human(self) -> None:
        result = format_output({"outer": {"inner": "val"}}, human=True)
        assert "outer:" in result
        assert "  inner: val" in result

    def test_nested_list_in_dict_human(self) -> None:
        result = format_output({"items": [1, 2]}, human=True)
        assert "items:" in result

    def test_pydantic_model(self) -> None:
        model = SampleModel(name="test", valueCount=42)
        result = format_output(model)
        parsed = json.loads(result)
        assert parsed["name"] == "test"
        assert parsed["valueCount"] == 42

    def test_pydantic_model_human(self) -> None:
        model = SampleModel(name="test", valueCount=42)
        result = format_output(model, human=True)
        assert "name: test" in result

    def test_scalar_human(self) -> None:
        result = format_output("hello", human=True)
        assert result == "hello"

    def test_scalar_json(self) -> None:
        result = format_output("hello")
        assert json.loads(result) == "hello"


class TestPrintOutput:
    def test_print_json(self) -> None:
        buf = io.StringIO()
        print_output({"status": "ok"}, human=False, file=buf)
        parsed = json.loads(buf.getvalue())
        assert parsed["status"] == "ok"

    def test_print_human(self) -> None:
        buf = io.StringIO()
        print_output({"status": "ok"}, human=True, file=buf)
        assert "status: ok" in buf.getvalue()


class TestPrintError:
    def test_error_json(self, capsys: object) -> None:
        import sys

        # Capture stderr
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()
        try:
            print_error("test error", human=False)
            output = sys.stderr.getvalue()
        finally:
            sys.stderr = old_stderr
        parsed = json.loads(output)
        assert parsed["error"] == "test error"

    def test_error_human(self) -> None:
        import sys

        old_stderr = sys.stderr
        sys.stderr = io.StringIO()
        try:
            print_error("test error", human=True)
            output = sys.stderr.getvalue()
        finally:
            sys.stderr = old_stderr
        assert "Error: test error" in output
