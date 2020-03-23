import pdb
import sys
from pathlib import Path

import networkx as nx
from tqdm import tqdm

from pipeline.dag import create_dag
from pipeline.dag import draw_dag
from pipeline.hashing import compare_hashes_of_task
from pipeline.hashing import save_hash_of_task_target
from pipeline.shared import ensure_list
from pipeline.tasks import process_tasks
from pipeline.tasks import replace_missing_templates_with_correct_paths
from pipeline.templates import collect_templates

try:
    from rpy2 import robjects
except ImportError:
    IS_R_INSTALLED = False
    robjects = None
else:
    IS_R_INSTALLED = True


def build_project(config):
    tasks = process_tasks(config)
    env, missing_templates = collect_templates(config["custom_templates"], tasks)
    tasks = replace_missing_templates_with_correct_paths(tasks, missing_templates)

    dag_dict = create_dag_dict(tasks)
    dag = create_dag(dag_dict)

    draw_dag(dag, config)
    execute_dag(dag, tasks, env, config)

    return tasks, dag


def create_dag_dict(tasks):
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


def execute_dag(dag, tasks, env, config):
    """Naive serial scheduler for our tasks."""
    len_task_names = list(map(len, tasks.keys()))
    prevent_task_description_from_moving = max(len_task_names) if len_task_names else 0

    with tqdm(total=0) as t:
        for id_ in nx.topological_sort(dag):
            if id_ in tasks:
                check_for_missing_dependencies(id_, env, dag)
                have_same_hashes = compare_hashes_of_task(id_, env, dag, config)
                if not have_same_hashes:
                    t.total += 1
                    t.update(0)
                    t.set_description(id_.ljust(prevent_task_description_from_moving))
                    _execute_task(id_, tasks, env, config)
                    save_hash_of_task_target(id_, tasks, config)
                    t.update()


def check_for_missing_dependencies(id_, env, dag):
    for dependency in dag.predecessors(id_):
        if dependency in env.list_templates():
            pass
        else:
            path = Path(dependency)
            if not path.exists():
                raise FileNotFoundError(
                    f"Dependency '{path.resolve().as_posix()}' of task '{id_}' cannot "
                    "be found."
                )


def _execute_task(id_, tasks, env, config):
    file = _render_task_template(tasks[id_], env)
    if "produces" in tasks[id_]:
        Path(tasks[id_]["produces"]).parent.mkdir(parents=True, exist_ok=True)

    if tasks[id_]["template"].endswith(".py"):
        try:
            exec(file, {"__name__": "__main__"})
        except Exception as e:
            if config["is_debug"]:
                type_, value, traceback = sys.exc_info()
                pdb.post_mortem(traceback)
            else:
                raise e
    elif tasks[id_]["template"].endswith(".r"):
        if not IS_R_INSTALLED:
            raise RuntimeError(
                "R is not installed. Choose only Python templates or install 'rpy2' via"
                " conda with `conda install -c conda-forge rpy2`."
            )
        robjects.r(file)


def _render_task_template(task_info, env):
    """Compile the file of the task."""
    template = env.get_template(task_info["template"])
    return template.render(**task_info)
