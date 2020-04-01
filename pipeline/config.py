from pathlib import Path

from pipeline._yaml import read_yaml
from pipeline.shared import ensure_list


def load_config(config=None):
    if config is None:
        path = Path.cwd() / ".pipeline.yaml"

        if path.exists():
            config = read_yaml(path.read_text())
            config = {} if not config else config
            config["user_config_file"] = path.as_posix()
            config["user_config_directory"] = path.parent.as_posix()
        else:
            raise ValueError("Cannot find '.pipeline.yaml' in current directory.")

    for key, default, default_parent in [
        ("project_directory", ".", "user_config_directory"),
        ("source_directory", "src", "project_directory"),
        ("build_directory", "bld", "project_directory"),
        ("hidden_build_directory", ".pipeline", "build_directory"),
        ("hidden_task_directory", ".tasks", "build_directory"),
    ]:
        config[key] = _generate_path(key, default, default_parent, config)

    custom_templates_dirs = ensure_list(config.get("custom_templates", []))
    config["custom_templates"] = [
        _generate_path(path, default_parent="project_directory", config=config)
        for path in custom_templates_dirs
    ]

    return config


def _generate_path(key_or_path, default=None, default_parent=None, config=None):
    if default is None:
        path = Path(key_or_path)
    else:
        path = Path(config.get(key_or_path, default))

    if path.is_absolute():
        pass
    else:
        path = Path(config[default_parent], path).resolve().as_posix()

    return path
