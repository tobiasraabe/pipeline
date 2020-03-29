from pathlib import Path

import networkx as nx

from pipeline.dag import create_dag
from pipeline.dag import draw_dag
from pipeline.execution import execute_dag_parallelly
from pipeline.execution import execute_dag_serially
from pipeline.hashing import compare_hashes_of_task
from pipeline.shared import ensure_list
from pipeline.tasks import process_tasks
from pipeline.tasks import replace_missing_templates_with_correct_paths
from pipeline.templates import collect_templates


def build_project(config):
    tasks = process_tasks(config)
    env, missing_templates = collect_templates(config["custom_templates"], tasks)
    tasks = replace_missing_templates_with_correct_paths(tasks, missing_templates)

    dag_dict = _create_dag_dict(tasks)
    dag = create_dag(dag_dict)

    draw_dag(dag, config)

    tasks = _mark_which_tasks_need_to_be_executed(tasks, dag, env, config)

    if config["n_jobs"] == 1:
        execute_dag_serially(dag, tasks, env, config)
    else:
        execute_dag_parallelly(dag, tasks, env, config)

    return tasks, dag


def _create_dag_dict(tasks):
    dag_dict = {}
    for id_, task_info in tasks.items():
        # Add the task to the graph as a node.
        depends_on = ensure_list(task_info.get("depends_on", [])).copy()
        depends_on.extend(ensure_list(task_info.get("template", [])))
        depends_on.append(task_info["config"])

        dag_dict[id_] = depends_on

        # If the task produces anything, register the output as a node.
        if "produces" in task_info:
            dag_dict[task_info["produces"]] = [id_]

    return dag_dict


def _mark_which_tasks_need_to_be_executed(tasks, dag, env, config):
    for id_ in nx.topological_sort(dag):
        if id_ in tasks:
            have_same_hashes = compare_hashes_of_task(id_, env, dag, config)
            if not have_same_hashes:
                tasks[id_]["_needs_to_be_executed"] = True

                # `missing_ok` in `Path.unlink()` was recently added in Python 3.8.
                try:
                    Path(tasks[id_]["produces"]).unlink()
                except FileNotFoundError:
                    pass
            else:
                tasks[id_]["_needs_to_be_executed"] = False

    return tasks


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
