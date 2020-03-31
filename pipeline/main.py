from pathlib import Path

import networkx as nx

from pipeline.dag import create_dag
from pipeline.execution import execute_dag_parallelly
from pipeline.execution import execute_dag_serially
from pipeline.hashing import compare_hashes_of_task
from pipeline.tasks import process_tasks
from pipeline.tasks import replace_missing_templates_with_correct_paths
from pipeline.templates import collect_templates


def build_project(config):
    tasks = process_tasks(config)
    env, missing_templates = collect_templates(config["custom_templates"], tasks)
    tasks = replace_missing_templates_with_correct_paths(tasks, missing_templates)

    dag = create_dag(tasks, config)

    dag = _mark_unfinished_tasks(dag, env, config)

    if config["n_jobs"] == 1:
        execute_dag_serially(dag, env, config)
    else:
        execute_dag_parallelly(dag, env, config)

    return dag


def _mark_unfinished_tasks(dag, env, config):
    for id_ in nx.topological_sort(dag):
        if dag.nodes[id_]["_is_task"]:
            have_same_hashes = compare_hashes_of_task(id_, env, dag, config)
            if not have_same_hashes:
                dag.nodes[id_]["_is_unfinished"] = True

                # `missing_ok` in `Path.unlink()` was only recently added in Python 3.8.
                try:
                    Path(dag.nodes[id_]["produces"]).unlink()
                except FileNotFoundError:
                    pass
            else:
                dag.nodes[id_]["_is_unfinished"] = False
        else:
            dag.nodes[id_]["_is_unfinished"] = False

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
