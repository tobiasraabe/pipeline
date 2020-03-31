from pathlib import Path

from pipeline._yaml import read_yaml
from pipeline.shared import ensure_list


def load_config(debug=False, n_jobs=1, priority=False):
    config = _read_config_file()

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
    config["hidden_task_directory"] = config["build_directory"] + "/.tasks"

    custom_templates_dir = ensure_list(config.get("custom_templates", []))
    config["custom_templates"] = [
        Path(config["project_root"], path).resolve().as_posix()
        for path in custom_templates_dir
    ]

    config["_is_debug"] = debug

    config["priority"] = priority
    config["priority_discount_factor"] = config.get("priority_discount_factor", 1)

    if config["_is_debug"]:
        # Turn off parallelization if debug modus is requested.
        config["n_jobs"] = 1
    else:
        # The command-line input has precedence over the value in the config file.
        config["n_jobs"] = n_jobs if n_jobs is not None else config.get("n_jobs", 1)

    return config


def _read_config_file():
    paths = list(Path.cwd().glob("**/.pipeline.yaml"))

    if len(paths) == 0:
        raise ValueError("Cannot find .pipeline.yaml.")
    elif len(paths) == 1:
        config = read_yaml(paths[0].read_text())
        config = {} if not config else config
        config["user_config_file"] = paths[0].as_posix()
    else:
        raise ValueError("There can only be one configuration file.")

    return config
