from pathlib import Path

from pipeline._yaml import read_yaml
from pipeline.shared import ensure_list


def load_config():
    paths = list(Path.cwd().glob("**/.pipeline.yaml"))

    if len(paths) == 0:
        raise ValueError("Cannot find .pipeline.yaml.")
    elif len(paths) == 1:
        config = read_yaml(paths[0].read_text())
        config = {} if not config else config
        config["user_config_file"] = paths[0].as_posix()
    else:
        raise ValueError("There can only be one configuration file.")

    project_root = config.get("project_root", Path(config["user_config_file"]).parent)
    config["project_root"] = Path(project_root).resolve().as_posix()

    source_dir = config.get("source_directory", "src")
    config["source_directory"] = (
        Path(config["project_root"], source_dir).resolve().as_posix()
    )

    build_dir = config.get("build_directory", "bld")
    config["build_directory"] = (
        Path(config["project_root"], build_dir).resolve().as_posix()
    )
    config["hidden_build_directory"] = config["build_directory"] + "/.pipeline"

    custom_templates_dir = ensure_list(config.get("custom_templates", []))
    config["custom_templates"] = [
        Path(config["project_root"], path).resolve().as_posix()
        for path in custom_templates_dir
    ]

    return config
