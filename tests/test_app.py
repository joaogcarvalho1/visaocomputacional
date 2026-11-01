from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_interface_steps_and_empty_enrollment(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    app = AppTest.from_file(str(APP)).run()
    assert not app.exception
    assert app.title[0].value == "Seu rosto acende a luz."
    assert app.metric[0].value == "0"
    assert app.button[0].disabled
    app.sidebar.radio[0].set_value("2 · Testar reconhecimento").run()
    assert not app.exception
    assert any("pelo menos 5" in item.value for item in app.info)
    app.sidebar.radio[0].set_value("3 · Acionar lâmpada").run()
    app.sidebar.slider[0].set_value(50).run()
    assert not app.exception
    assert any("--port COM3 --threshold 50" in item.value for item in app.code)
