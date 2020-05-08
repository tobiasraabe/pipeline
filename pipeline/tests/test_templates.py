from pipeline.templates import collect_templates
import os
import textwrap
from click.testing import CliRunner
import yaml
from pipeline.config import load_config
from pipeline.cli import cli
from pathlib import Path
import pytest
from pipeline.tasks import _collect_user_defined_tasks


@pytest.mark.end_to_end
def test_collection_of_files_and_directories(test_project_config):
    """Test template collection via function and CLI."""
    config = test_project_config

    # Create templates files.
    project_path = Path(config["project_directory"])
    project_path.joinpath("template_1.py").touch()
    project_path.joinpath("template_2.r").touch()
    project_path.joinpath("templates").mkdir()
    project_path.joinpath("templates", "template_3.r").touch()
    project_path.joinpath("templates", "template_4.py").touch()

    # Add files and directories to config.
    config["custom_templates"] = ["template_1.py", "template_2.r", "templates"]

    # Update written config.
    project_path.joinpath(".pipeline.yaml").write_text(
        textwrap.dedent(yaml.dump(config))
    )

    # Collect templates via the function.
    os.chdir(project_path)
    config = load_config(config)
    env, missing_templates = collect_templates(config["custom_templates"])

    for template in ["template_1.py", "template_2.r", "template_3.py", "template_4.r"]:
        template in env.list_templates()
    assert not missing_templates

    # Collect templates via the CLI.
    runner = CliRunner()
    result = runner.invoke(cli, ["collect", "--templates"])
    assert result.exit_code == 0


@pytest.mark.end_to_end
def test_globals_in_templates(test_project_config):
    """Test using globals in templates."""
    config = test_project_config

    # Add globals to configuration and write to disk.
    config["globals"] = {"a": 'Rendered global variable.'}
    Path(config["user_config_file"]).write_text(yaml.dump(config))

    # Load config to get other variables.
    os.chdir(config["project_directory"])
    config = load_config()

    # Create source directory.
    Path(config["source_directory"]).mkdir()

    # Write task.yaml.
    task_template = {"task": {"template": "task.py"}}
    Path(config["source_directory"], "task.yaml").write_text(yaml.dump(task_template))

    # Write task.py.
    task = """
    from pathlib import Path

    Path("{{ produces }}").write_text("{{ globals['a'] }}")
    """
    Path(config["source_directory"], "task.py").write_text(textwrap.dedent(task))

    # Build the project.
    runner = CliRunner()
    result = runner.invoke(cli, ["build"])
    assert result.exit_code == 0

    # Read rendered task.
    assert (
        config["globals"]["a"]
        == Path(config["hidden_build_directory"], "task").read_text()
    )


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
