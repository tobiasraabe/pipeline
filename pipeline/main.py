from pathlib import Path

from pipeline.dag import create_dag
from pipeline.execution import execute_dag_parallelly
from pipeline.execution import execute_dag_serially
from pipeline.tasks import process_tasks
from pipeline.tasks import replace_missing_templates_with_correct_paths
from pipeline.templates import collect_templates


def build_project(config):
    tasks = process_tasks(config)
    env, missing_templates = collect_templates(config["custom_templates"], tasks)
    tasks = replace_missing_templates_with_correct_paths(tasks, missing_templates)

    dag = create_dag(tasks, config)

    if config["n_jobs"] == 1:
        execute_dag_serially(dag, env, config)
    else:
        execute_dag_parallelly(dag, env, config)

    return dag


def _check_for_missing_dependencies(id_, env, dag):
    for dependency in dag.predecessors(id_):
        if dependency in env.list_templates():
            pass
        else:
            path = Path(dependency)
            if not path.exists():
                raise FileNotFoundError(
                    f"Dependency '{path.as_posix()}' of task '{id_}' cannot be found."
                )
