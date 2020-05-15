import os
import textwrap
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from pipeline.cli import cli


@pytest.mark.end_to_end
def test_cli_collect(test_project_config):
    for flag in ["--config", "--tasks", "--templates"]:
        os.chdir(test_project_config["project_directory"])
        runner = CliRunner()
        result = runner.invoke(cli, ["collect", flag])
        assert result.exit_code == 0


@pytest.mark.end_to_end
def test_run_always(test_project_config):
    """Test whether tasks are rerun if they should always run."""
    config = test_project_config

    # Create templates files.
    project_path = Path(config["project_directory"])
    project_path.joinpath("src").mkdir()

    task_which_runs_always = textwrap.dedent(
        """
        task:
            template: task.py
            produces: {{ build_directory }}/out.txt
            run_always: true
        """
    )
    project_path.joinpath("src", "task.yaml").write_text(task_which_runs_always)

    task = textwrap.dedent(
        """
        from pathlib import Path


        if __name__ == '__main__':
            path = Path("{{ produces }}")
            if not path.exists():
                path.write_text("0")
            else:
                number = int(path.read_text()) + 1
                path.write_text(f"{number}")
        """
    )
    project_path.joinpath("src", "task.py").write_text(task)

    os.chdir(project_path)

    # Build the project the first time.
    runner = CliRunner()
    result = runner.invoke(cli, ["build"])
    assert result.exit_code == 0

    assert project_path.joinpath("bld", "out.txt").read_text() == "0"

    # Build the project the second time.
    runner = CliRunner()
    result = runner.invoke(cli, ["build"])
    assert result.exit_code == 0

    assert project_path.joinpath("bld", "out.txt").read_text() == "1"


@pytest.mark.end_to_end
def test_missing_pipeline_configuration(test_project_config):
    config = test_project_config

    # Remove configuration.
    Path(config["project_directory"]).joinpath(".pipeline.yaml").unlink()

    os.chdir(config["project_directory"])

    runner = CliRunner()
    result = runner.invoke(cli, ["build"])

    assert result.exit_code == 1
    assert str(result.exception) == "Cannot find '.pipeline.yaml' in current directory."


@pytest.mark.end_to_end
def test_priority_scheduling(test_project_config):
    """Test priority scheduling.

    This tests create four tasks with different priorities where two are independent and
    two are dependent where the preceding task gets its priority via discounting.

    """
    config = test_project_config
    project_directory = Path(config["project_directory"])

    # Set priority discount factor.
    project_directory.joinpath(".pipeline.yaml").write_text(
        "priority_discount_factor: 0.5"
    )

    project_directory.joinpath("src").mkdir()
    task = textwrap.dedent(
        """
        import yaml
        from pathlib import Path


        if __name__ == '__main__':
            Path("{{ produces }}").touch()
            path = Path("{{ build_directory }}/out.yaml")
            if path.exists():
                list_ = yaml.safe_load(path.read_text())
            else:
                list_ = []
            list_.append("{{ letter }}")
            path.write_text(yaml.dump(list_))

        """
    )
    project_directory.joinpath("src", "task.py").write_text(task)

    task_specification = textwrap.dedent(
        """
        task-1:
            template: task.py
            produces: {{ build_directory }}/dummy_out_d
            letter: d
            priority: 0.25

        task-2:
            template: task.py
            produces: {{ build_directory }}/dummy_out_a
            letter: a
            priority: 0.75

        task-3:
            produces: {{ build_directory }}/dummy_out_b
            template: task.py
            letter: b

        task-4:
            template: task.py
            produces: {{ build_directory }}/dummy_out_c
            depends_on: task-3
            letter: c
            priority: 1

        """
    )
    project_directory.joinpath("src", "tasks.yaml").write_text(task_specification)

    os.chdir(config["project_directory"])

    runner = CliRunner()
    result = runner.invoke(cli, ["build"])

    assert result.exit_code == 0

    list_ = yaml.safe_load(project_directory.joinpath("bld", "out.yaml").read_text())

    result = runner.invoke(cli, ["clean"])
    result = runner.invoke(cli, ["build", "--priority"])

    assert result.exit_code == 0

    list_ = yaml.safe_load(project_directory.joinpath("bld", "out.yaml").read_text())
    assert list_ == list("abcd")
