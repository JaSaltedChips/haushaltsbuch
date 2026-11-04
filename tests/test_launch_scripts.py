"""POSIX launcher checks using a disposable project and fake Python executable."""

import os
from pathlib import Path
import shutil
import subprocess

import pytest


PROJECT_DIR = Path(__file__).resolve().parent.parent
SHELL = shutil.which("sh")
pytestmark = pytest.mark.skipif(SHELL is None, reason="POSIX shell not installed")


@pytest.fixture
def project(tmp_path):
    directory = tmp_path / "expense monitor"
    directory.mkdir()
    for name in ("setup.sh", "run.sh", "run_demo.sh"):
        shutil.copyfile(PROJECT_DIR / name, directory / name)
    return directory


def launch(project, script="run.sh", *arguments):
    environment = os.environ.copy()
    environment.pop("EM_DB", None)
    return subprocess.run(
        [SHELL, str(project / script), *arguments],
        cwd=project.parent,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def install_fake_python(project):
    executable = project / "venv" / "bin" / "python"
    executable.parent.mkdir(parents=True)
    executable.write_text(
        '#!/bin/sh\nprintf "DB=%s\\n" "${EM_DB:-default}"\n'
        'printf "ARG=%s\\n" "$@"\n'
        'test -f ./run.sh || exit 12\n',
        encoding="utf-8",
    )
    executable.chmod(0o755)


def test_missing_venv_reports_setup_command(project):
    result = launch(project)
    assert result.returncode == 1
    assert "sh setup.sh" in result.stderr


def test_invalid_argument_reports_usage(project):
    result = launch(project, "run.sh", "--unknown")
    assert result.returncode == 1
    assert "Usage:" in result.stderr


def test_native_launcher_uses_project_directory_and_localhost(project):
    install_fake_python(project)
    result = launch(project)
    assert result.returncode == 0, result.stderr
    assert "DB=default" in result.stdout
    assert "ARG=uvicorn\nARG=main:app" in result.stdout
    assert "ARG=--host\nARG=127.0.0.1" in result.stdout
    assert "ARG=--workers\nARG=1" in result.stdout


@pytest.mark.parametrize("existing", [False, True])
def test_demo_launcher_creates_only_missing_demo_database(project, existing):
    install_fake_python(project)
    if existing:
        (project / "data").mkdir()
        (project / "data" / "demo.db").touch()
    result = launch(project, "run_demo.sh")
    assert result.returncode == 0, result.stderr
    assert "DB=data/demo.db" in result.stdout
    assert ("ARG=create_demo_db.py" in result.stdout) is not existing
    assert "ARG=uvicorn" in result.stdout