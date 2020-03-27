import subprocess
from pathlib import Path

import click
import networkx as nx
from tqdm import tqdm

from pipeline.dag import create_dag
from pipeline.dag import draw_dag
from pipeline.exceptions import TaskError
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

    tasks = _mark_which_tasks_need_to_be_executed(tasks, dag, env, config)

    _execute_dag_serially(dag, tasks, env, config)

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


def _execute_dag_serially(dag, tasks, env, config):
    """Naive serial scheduler for our tasks."""
    tasks_needing_execution = [
        id_ for id_ in tasks if tasks[id_]["_needs_to_be_executed"]
    ]
    len_task_names = list(map(len, tasks_needing_execution))
    prevent_task_description_from_moving = max(len_task_names) if len_task_names else 0

    with TqdmTotalTime(
        total=len(tasks_needing_execution),
        bar_format="{l_bar}{bar}|{n_fmt}/{total_fmt} tasks in {total_time}",
    ) as t:
        for id_ in nx.topological_sort(dag):
            if id_ in tasks_needing_execution:
                t.set_description(id_.ljust(prevent_task_description_from_moving))

                _execute_task(id_, tasks, env, config)

                _process_task_target(id_, tasks, config)

                t.update()


def _execute_task(id_, tasks, env, config):
    file = _render_task_template(tasks[id_], env)
    if "produces" in tasks[id_]:
        Path(tasks[id_]["produces"]).parent.mkdir(parents=True, exist_ok=True)

    if tasks[id_]["template"].endswith(".py"):
        try:
            path = Path(config["hidden_task_directory"], id_ + ".py")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(file)

            subprocess.run(["python", str(path)], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            message = (
                f"\n\nTask '{id_}' in file '{path}' failed."
                f"\n\n{e.stderr.decode('utf-8')}"
            )
            if config["is_debug"]:
                click.echo(message)
                subprocess.run(
                    ["python", "-m", "pdb", "-c", "continue", str(path)], check=True,
                )
                import sys

                sys.exit("### Abort build.")
            else:
                raise TaskError(message, e)

    elif tasks[id_]["template"].endswith(".r"):
        if not IS_R_INSTALLED:
            raise RuntimeError(
                "R is not installed. Choose only Python templates or install 'rpy2' via"
                " conda with `conda install -c conda-forge rpy2`."
            )
        path = Path(config["hidden_task_directory"], id_ + ".r")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(file)
        robjects.r.source(str(path))

    else:
        raise NotImplementedError("Only Python and R tasks are allowed.")


def _process_task_target(id_, tasks, config):
    path = Path(tasks[id_]["produces"])
    if not path.exists():
        raise FileNotFoundError(
            f"Target '{path.as_posix()}' was not produced by task '{id_}'."
        )
    save_hash_of_task_target(id_, tasks, config)


def _render_task_template(task_info, env):
    """Compile the file of the task."""
    template = env.get_template(task_info["template"])
    return template.render(**task_info)


class TqdmTotalTime(tqdm):
    """Provides a `total_time` format parameter"""

    @property
    def format_dict(self):
        d = super().format_dict
        total_time = d["elapsed"] * (d["total"] or 0) / max(d["n"], 1)
        d.update(total_time=f"{self.format_interval(total_time)}")

        return d
