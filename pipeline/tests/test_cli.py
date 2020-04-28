import os

import pytest
from click.testing import CliRunner

from pipeline.cli import cli


@pytest.mark.end_to_end
def test_cli_collect(test_project_config):
    for flag in ["--config", "--tasks", "--templates"]:
        os.chdir(test_project_config["project_directory"])
        runner = CliRunner()
        result = runner.invoke(cli, ["collect", flag])
        assert result.exit_code == 0
