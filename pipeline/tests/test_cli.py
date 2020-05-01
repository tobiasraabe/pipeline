import os
import textwrap
from pathlib import Path

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
