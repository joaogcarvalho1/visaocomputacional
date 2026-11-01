from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_guide_builds_automatic_command_and_validates_port(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    app = AppTest.from_file(str(APP)).run()
    assert not app.exception
    assert any("--port COM3 --on-delay 5 --off-delay 5" in item.value for item in app.code)
    app.text_input[0].set_value("COM4").run()
    assert any("--port COM4" in item.value for item in app.code)
    app.text_input[0].set_value("COM3; bad-command").run()
    assert not app.exception
    assert any("porta Windows válida" in item.value for item in app.warning)
    assert not any("--port" in item.value for item in app.code)
