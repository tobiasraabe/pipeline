from pathlib import Path

from pipeline._yaml import read_yaml
from pipeline.shared import ensure_list


def load_config():
    path = Path.cwd() / ".pipeline.yaml"

    if path.exists():
        config = read_yaml(path.read_text())
        config = {} if not config else config
        config["user_config_file"] = path.as_posix()
    else:
        raise ValueError("Cannot find '.pipeline.yaml' in current directory.")

    project_directory = config.get(
        "project_directory", Path(config["user_config_file"]).parent
    )
    config["project_directory"] = Path(project_directory).resolve().as_posix()

    source_dir = config.get("source_directory", "src")
    config["source_directory"] = (
        Path(config["project_directory"], source_dir).resolve().as_posix()
    )

    build_dir = config.get("build_directory", "bld")
    config["build_directory"] = (
        Path(config["project_directory"], build_dir).resolve().as_posix()
    )
    config["hidden_build_directory"] = config["build_directory"] + "/.pipeline"
    config["hidden_task_directory"] = config["build_directory"] + "/.tasks"

    custom_templates_dir = ensure_list(config.get("custom_templates", []))
    config["custom_templates"] = [
        Path(config["project_directory"], path).resolve().as_posix()
        for path in custom_templates_dir
    ]

    return config
