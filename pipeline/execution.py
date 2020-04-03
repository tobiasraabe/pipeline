import subprocess
import sys
import time
from concurrent.futures.process import ProcessPoolExecutor
from pathlib import Path

import click
import networkx as nx
from tqdm import tqdm

from pipeline.exceptions import TaskError
from pipeline.hashing import compare_hashes_of_task
from pipeline.hashing import save_hash_of_task_target
from pipeline.hashing import save_hashes_of_task_dependencies
from pipeline.shared import ensure_list
from pipeline.shared import render_task_template

try:
    import rpy2
    from rpy2 import robjects

    if rpy2.__version__ < "3":
        from rpy2.rinterface import RRuntimeError
    else:
        from rpy2.rinterface_lib.embedded import RRuntimeError
except ImportError:
    IS_R_INSTALLED = False
    robjects = None
    RRuntimeError = None
else:
    IS_R_INSTALLED = True


TQDM_BAR_FORMAT = "{l_bar}{bar}|{n_fmt}/{total_fmt} tasks in {elapsed}"


def execute_dag_serially(dag, env, config):
    """Execute the DAG serially.

    This function executes the tasks ordered topological which means it is an ordering
    which ensures that a node is only visited if all of its preceding nodes are visited
    before.

    Parameters
    ----------
    dag : nx.DiGraph
        The DAG containing the complete workflow.
    env : jinja2.Environment
        An environment which manages the templates.
    config : dict
        The workflow configuration.

    """
    unfinished_tasks = _collect_unfinished_tasks(dag, env, config)
    len_task_names = list(map(len, unfinished_tasks))
    prevent_task_description_from_moving = max(len_task_names) if len_task_names else 0

    with tqdm(total=len(unfinished_tasks), bar_format=TQDM_BAR_FORMAT) as t:
        for id_ in nx.topological_sort(dag):
            if id_ in unfinished_tasks:
                t.set_description(id_.ljust(prevent_task_description_from_moving))

                save_hashes_of_task_dependencies(id_, env, dag, config)

                path = _preprocess_task(id_, dag, env, config)

                _ = _execute_task(id_, path, config["_is_debug"])

                _process_task_target(id_, dag, config)

                t.update()


def execute_dag_parallelly(dag, env, config):
    unfinished_tasks = _collect_unfinished_tasks(dag, env, config)
    finished_tasks = {id_ for id_ in dag.nodes if id_ not in unfinished_tasks}
    len_task_names = list(map(len, unfinished_tasks))
    prevent_task_description_from_moving = max(len_task_names) if len_task_names else 0

    with tqdm(
        total=len(unfinished_tasks), bar_format=TQDM_BAR_FORMAT,
    ) as t, ProcessPoolExecutor(config["n_jobs"]) as executor:

        are_tasks_left = len(unfinished_tasks) != 0
        submitted_tasks = {}

        while are_tasks_left:
            # Submit new tasks.
            for id_ in unfinished_tasks:
                deps = [
                    predecessor
                    for dependency in ensure_list(dag.nodes[id_].get("depends_on", []))
                    for predecessor in dag.predecessors(dependency)
                ]
                all_dependencies_executed = all(dep in finished_tasks for dep in deps)
                if all_dependencies_executed:
                    save_hashes_of_task_dependencies(id_, env, dag, config)

                    path = _preprocess_task(id_, dag, env, config)

                    future = executor.submit(
                        _execute_task, id_, path, config["_is_debug"]
                    )
                    future.add_done_callback(lambda x: t.update())
                    submitted_tasks[id_] = future

                    t.set_description(id_.ljust(prevent_task_description_from_moving))
                else:
                    pass

            # Evaluate finished tasks.
            newly_finished_tasks = {
                id_
                for id_, task in submitted_tasks.items()
                if task.done() and id_ not in finished_tasks
            }

            # Check for exceptions.
            exceptions = [
                future.exception().message
                for future in submitted_tasks.values()
                if future.exception()
            ]
            if exceptions:
                raise TaskError("\n\n".join(exceptions))

            for id_ in newly_finished_tasks:
                _process_task_target(id_, dag, config)

            finished_tasks = finished_tasks.union(newly_finished_tasks)
            unfinished_tasks = unfinished_tasks - finished_tasks - set(submitted_tasks)
            are_tasks_left = len(unfinished_tasks) != 0

            # A little bit of sleep time to wait for tasks to finish.
            time.sleep(0.1)


def _collect_unfinished_tasks(dag, env, config):
    """Collect unfinished tasks.

    Iterate over topological sorted nodes in the DAG. If the node is a task, compare the
    hashes of all dependencies and targets. If the hashes do not match, add the task to
    the set of unfinished tasks. After that, go through the whole list of descendants of
    the task and mark all tasks among them as unfinished, too.

    Parameters
    ----------
    dag : nx.DiGraph
        The DAG containing the complete workflow.
    env : jinja2.Environment
        An environment which manages the templates.
    config : dict
        The workflow configuration.

    """
    unfinished_tasks = set()
    for id_ in nx.topological_sort(dag):
        if dag.nodes[id_]["_is_task"] and id_ not in unfinished_tasks:
            have_same_hashes = compare_hashes_of_task(id_, env, dag, config)
            if not have_same_hashes:
                unfinished_tasks.add(id_)
                for descendant in nx.descendants(dag, id_):
                    if dag.nodes[descendant]["_is_task"]:
                        unfinished_tasks.add(descendant)

    return unfinished_tasks


def _preprocess_task(id_, dag, env, config):
    file = render_task_template(id_, dag.nodes[id_], env, config)

    if "produces" in dag.nodes[id_]:
        Path(dag.nodes[id_]["produces"]).parent.mkdir(parents=True, exist_ok=True)

    if dag.nodes[id_]["template"].endswith(".py"):
        path = Path(config["hidden_task_directory"], id_ + ".py")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(file)

    elif dag.nodes[id_]["template"].endswith(".r"):
        path = Path(config["hidden_task_directory"], id_ + ".r")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(file)

    else:
        raise NotImplementedError("Only Python and R tasks are allowed.")

    return path


def _execute_task(id_, path, is_debug):
    if path.suffix == ".py":
        try:
            subprocess.run(["python", str(path)], check=True)

        except subprocess.CalledProcessError as e:
            message = _format_exception_message(id_, path, e)
            if is_debug:
                click.echo(message)
                click.echo("Rerun the task to enter the debugger.")
                subprocess.run(
                    ["python", "-m", "pdb", "-c", "continue", str(path)], check=True,
                )
                sys.exit("### Abort build.")
            else:
                raise TaskError(message, e)

    elif path.suffix == ".r":
        if not IS_R_INSTALLED:
            raise RuntimeError(
                "R is not installed. Choose only Python templates or install 'rpy2' via"
                " conda with `conda install -c conda-forge rpy2`."
            )
        try:
            robjects.r.source(str(path))
        except RRuntimeError as e:
            message = _format_exception_message(id_, path, e)
            raise TaskError(message, e)

    else:
        raise NotImplementedError("Only Python and R tasks are allowed.")


def _format_exception_message(id_, path, e):
    exc_info = e.__str__()
    return f"\n\nTask '{id_}' in file '{path}' failed.\n\n{exc_info}"


def _process_task_target(id_, dag, config):
    """Process the target of the task."""
    targets = ensure_list(dag.nodes[id_]["produces"])
    missing_targets = [
        Path(target).as_posix() for target in targets if not Path(target).exists()
    ]
    if missing_targets:
        raise FileNotFoundError(
            f"Target(s) '{missing_targets}' was(were) not produced by task '{id_}'."
        )
    save_hash_of_task_target(id_, dag, config)
