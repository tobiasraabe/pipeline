from pathlib import Path

import pytest
import yaml


@pytest.fixture(scope="function")
def test_project_config(tmp_path_factory):
    project_path = Path(tmp_path_factory.mktemp("project"))

    config = {
        "project_directory": project_path.as_posix(),
        "user_config_file": project_path.joinpath(".pipeline.yaml").as_posix(),
        "user_config_directory": project_path.as_posix(),
    }

    project_path.joinpath(".pipeline.yaml").write_text(yaml.dump(config))

    return config
