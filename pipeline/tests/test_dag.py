import pytest

from pipeline.dag import _create_dag_dict


@pytest.mark.unit
def test_create_dag_dict():
    tasks = {
        "task-1": {
            "template": "task-1.py",
            "depends_on": "dependency-1",
            "target": "target-1",
        },
        "task-2": {
            "template": "task-2.py",
            "depends_on": "target-1",
            "target": "target-2",
        },
    }

    dag_dict = _create_dag_dict(tasks)

    expected = {
        "task-1": ["dependency-1", "task-1.py"],
        "task-2": ["target-1", "task-2.py"],
    }

    assert dag_dict == expected
