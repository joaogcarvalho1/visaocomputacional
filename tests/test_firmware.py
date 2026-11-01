import shutil
import subprocess
from pathlib import Path

import pytest


def test_firmware_commands_and_watchdog(tmp_path):
    compiler = shutil.which("g++")
    if not compiler:
        pytest.skip("g++ necessário para simular o firmware; CI Linux executa este teste.")
    source = Path(__file__).with_name("firmware_harness.cpp")
    executable = tmp_path / "firmware-test"
    subprocess.run(
        [compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror", str(source), "-o", str(executable)],
        check=True,
    )
    subprocess.run([str(executable)], check=True)
