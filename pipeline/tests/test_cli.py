import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from pipeline.cli import cli


@pytest.fixture
def test_project(tmpdir_factory):
    project_path = Path(tmpdir_factory.mktemp("project"))
    project_path.joinpath(".pipeline.yaml").touch()

    return project_path


def test_cli_collect(test_project):
    for flag in ["--config", "--tasks", "--templates"]:
        os.chdir(test_project)
        runner = CliRunner()
        result = runner.invoke(cli, ["collect", flag])
        assert result.exit_code == 0
