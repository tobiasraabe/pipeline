import os
import textwrap
from pathlib import Path

import pytest
from click.testing import CliRunner

from pipeline.cli import cli
from pipeline.config import load_config
from pipeline.exceptions import DuplicatedTaskError
from pipeline.tasks import process_tasks


def test_duplicated_task_ids_in_the_same_file(test_project_config):
    """Test whether a duplicated task in the same file raises an error."""
    config = test_project_config
    config = load_config(config=config)

    source_directory = Path(config["source_directory"])
    source_directory.mkdir()

    task = """
    task-1:
      template: task.py

    task-1:
      template: task.py
    """
    source_directory.joinpath("task.yaml").write_text(textwrap.dedent(task))

    os.chdir(config["project_directory"])
    with pytest.raises(DuplicatedTaskError):
        process_tasks(config)

    runner = CliRunner()
    result = runner.invoke(cli, ["collect", "--tasks"])
    assert result.exit_code == 1
    assert isinstance(result.exception, DuplicatedTaskError)


def test_duplicated_task_ids_in_different_files(test_project_config):
    """Test whether a duplicated task in separate files raises an error."""
    config = test_project_config
    config = load_config(config=config)

    source_directory = Path(config["source_directory"])
    source_directory.mkdir()

    task = """
    task:
      template: task.py
    """
    source_directory.joinpath("task-1.yaml").write_text(textwrap.dedent(task))
    source_directory.joinpath("task-2.yaml").write_text(textwrap.dedent(task))

    os.chdir(config["project_directory"])
    with pytest.raises(DuplicatedTaskError):
        process_tasks(config)

    runner = CliRunner()
    result = runner.invoke(cli, ["collect", "--tasks"])
    assert result.exit_code == 1
    assert isinstance(result.exception, DuplicatedTaskError)
