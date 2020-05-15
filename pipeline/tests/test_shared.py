import os
import textwrap
from pathlib import Path

import pytest
from click.testing import CliRunner

from pipeline.cli import cli
from pipeline.config import load_config


@pytest.mark.end_to_end
def test_variables_with_the_same_name_in_config_and_task_dict(test_project_config):
    config = load_config(config=test_project_config)

    source_directory = Path(config["source_directory"])
    source_directory.mkdir()

    task_specification = textwrap.dedent(
        """
        task:
          template: ols.py
          project_directory: dummy_value
        """
    )
    source_directory.joinpath("tasks.yaml").write_text(task_specification)

    os.chdir(config["project_directory"])

    runner = CliRunner()
    result = runner.invoke(cli, ["build"])

    assert result.exit_code == 1
    assert result.exception.__str__().startswith("Task 'task' received arguments")
