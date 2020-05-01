import os
from pathlib import Path

import pytest

from pipeline.execution import _patch_subprocess_environment


@pytest.mark.unit
def test_patch_subprocess_environment(monkeypatch):
    monkeypatch.setattr(os, "environ", {})

    path = Path("C:/dummy_project_directory")
    config = {"project_directory": str(path)}
    result = _patch_subprocess_environment(config)

    assert result == {"PYTHONPATH": f"{path};"}
