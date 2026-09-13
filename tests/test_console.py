import io
import sys

from pitchlens.console import use_utf8_output

PROGRESS_LINE = "━━ época 1/2 ━━"


def test_redirected_cp1252_output_is_switched_to_utf8(monkeypatch):
    stdout_buffer, stderr_buffer = io.BytesIO(), io.BytesIO()
    stdout = io.TextIOWrapper(stdout_buffer, encoding="cp1252", newline="\n")
    stderr = io.TextIOWrapper(stderr_buffer, encoding="cp1252", newline="\n")
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(sys, "stderr", stderr)

    use_utf8_output()
    print(PROGRESS_LINE)
    print(PROGRESS_LINE, file=sys.stderr)
    stdout.flush()
    stderr.flush()

    assert stdout_buffer.getvalue().decode("utf-8") == PROGRESS_LINE + "\n"
    assert stderr_buffer.getvalue().decode("utf-8") == PROGRESS_LINE + "\n"


def test_streams_without_reconfigure_are_left_alone(monkeypatch):
    monkeypatch.setattr(sys, "stdout", None)

    use_utf8_output()

    assert sys.stdout is None
