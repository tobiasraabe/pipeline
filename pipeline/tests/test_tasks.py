import os
import textwrap
from pathlib import Path

import pytest
from click.testing import CliRunner

from pipeline.cli import cli
from pipeline.config import load_config
from pipeline.exceptions import DuplicatedTaskError
from pipeline.tasks import _collect_user_defined_tasks
from pipeline.tasks import process_tasks


@pytest.mark.end_to_end
def test_duplicated_task_ids_in_the_same_file(test_project_config):
    """Test whether a duplicated task in the same file raises an error."""
    config = load_config(config=test_project_config)

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


@pytest.mark.end_to_end
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


@pytest.mark.unit
def test_discard_non_task_yamls(test_project_config):
    config = test_project_config
    config = load_config(config=config)

    source_directory = Path(config["source_directory"])
    source_directory.mkdir()

    task_specification = textwrap.dedent(
        """
        task-1:
          template: task.py


        task-2:
          a: 1
        """
    )
    source_directory.joinpath("task.yaml").write_text(task_specification)

    random_yaml = textwrap.dedent(
        """
        - a
        - b
        """
    )
    source_directory.joinpath("random_yaml.yaml").write_text(random_yaml)

    task_yml = textwrap.dedent(
        """
        task-3:
          template: task.py
        """
    )
    source_directory.joinpath("task.yml").write_text(task_yml)

    result = _collect_user_defined_tasks(config)

    result["task-1"].pop("config")
    assert result == {"task-1": {"template": "task.py"}}


@pytest.mark.unit
def test_python_comments_within_jinja2_templates(test_project_config):
    config = load_config(config=test_project_config)

    source_directory = Path(config["source_directory"])
    source_directory.mkdir()

    task_specification = textwrap.dedent(
        """
        task-1:
          template: t.py

        # task-2:
        #   template: t.py

        task-3:
          template: t.py
        """
    )
    source_directory.joinpath("tasks.yaml").write_text(task_specification)

    result = _collect_user_defined_tasks(config)
    result["task-1"].pop("config")
    result["task-3"].pop("config")

    assert result == {"task-1": {"template": "t.py"}, "task-3": {"template": "t.py"}}
