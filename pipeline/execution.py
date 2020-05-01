import os
import subprocess
import sys
import time
from concurrent.futures.process import ProcessPoolExecutor
from pathlib import Path

import click
import networkx as nx
from tqdm import tqdm

from pipeline.dag import Scheduler
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

    padding = _compute_padding_to_prevent_task_description_from_moving(unfinished_tasks)

    scheduler = Scheduler(dag, unfinished_tasks, config["priority"])

    with tqdm(total=len(unfinished_tasks), bar_format=TQDM_BAR_FORMAT) as t:
        while scheduler.are_tasks_left:
            id_ = scheduler.propose().pop()

            t.set_description(id_.ljust(padding))

            save_hashes_of_task_dependencies(id_, env, dag, config)

            path = _preprocess_task(id_, dag, env, config)

            _ = _execute_task(id_, path, config)

            _process_task_target(id_, dag, config)

            scheduler.process_finished(id_)

            t.update()


def execute_dag_parallelly(dag, env, config):
    n_jobs = config["n_jobs"]

    unfinished_tasks = _collect_unfinished_tasks(dag, env, config)

    padding = _compute_padding_to_prevent_task_description_from_moving(unfinished_tasks)

    scheduler = Scheduler(dag, unfinished_tasks, config["priority"])
    submitted_tasks = {}

    with tqdm(
        total=len(unfinished_tasks), bar_format=TQDM_BAR_FORMAT,
    ) as t, ProcessPoolExecutor(n_jobs) as executor:
        while scheduler.are_tasks_left:
            # Add new tasks to the queue.
            n_proposals = (
                n_jobs - sum(not task.done() for task in submitted_tasks.values())
                if config["priority"]
                else -1
            )
            proposals = scheduler.propose(n_proposals)

            for id_ in ensure_list(proposals):
                save_hashes_of_task_dependencies(id_, env, dag, config)

                path = _preprocess_task(id_, dag, env, config)

                future = executor.submit(_execute_task, id_, path, config)
                future.add_done_callback(lambda x: t.update())
                submitted_tasks[id_] = future

                t.set_description(id_.ljust(padding))

            # Evaluate finished tasks.
            newly_finished_tasks = {
                id_ for id_, task in submitted_tasks.items() if task.done()
            }

            # Check for exceptions.
            exceptions = [
                str(future.exception())
                for future in submitted_tasks.values()
                if future.exception()
            ]
            if exceptions:
                raise TaskError("\n\n".join(exceptions))

            for id_ in newly_finished_tasks:
                _process_task_target(id_, dag, config)
                del submitted_tasks[id_]

            scheduler.process_finished(newly_finished_tasks)

            # A little bit of sleep time to wait for tasks to finish.
            time.sleep(0.1)


def _collect_unfinished_tasks(dag, env, config):
    """Collect unfinished tasks.

    Iterate over topological sorted nodes in the DAG. If the node is a task, do the
    following.

    1. If the task is marked to be always executed, add it to the set.
    2. Otherwise, compare the hashes of all dependencies and targets. If the hashes do
       not match, add the task to the set of unfinished tasks. After that, go through
       the whole list of descendants of the task and mark all tasks among them as
       unfinished, too.

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
        if dag.nodes[id_]["_is_task"]:
            if dag.nodes[id_].get("run_always", False):
                unfinished_tasks.add(id_)
            else:
                have_same_hashes = compare_hashes_of_task(id_, env, dag, config)
                if not have_same_hashes:
                    unfinished_tasks.add(id_)
                    for descendant in nx.descendants(dag, id_):
                        if dag.nodes[descendant]["_is_task"]:
                            unfinished_tasks.add(descendant)

    return unfinished_tasks


def _compute_padding_to_prevent_task_description_from_moving(unfinished_tasks):
    """Compute the padding to have task descriptions with the same length.

    Some task names are longer than others. The tqdm progress bar would be constantly
    adjusting if more space is available. Instead, we compute the length of the longest
    task name and add whitespace to the right.

    Example
    -------
    >>> unfinished_tasks = ["short_name", "long_task_name"]
    >>> _compute_padding_to_prevent_task_description_from_moving(unfinished_tasks)
    14

    """
    len_task_names = list(map(len, unfinished_tasks))
    padding = max(len_task_names) if len_task_names else 0

    return padding


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


def _execute_task(id_, path, config):
    if path.suffix == ".py":
        environment = _patch_subprocess_environment(config)

        try:
            subprocess.run(["python", str(path)], check=True, env=environment)

        except subprocess.CalledProcessError as e:
            message = _format_exception_message(id_, path, e)
            if config["_is_debug"]:
                click.echo(message)
                click.echo("Rerun the task to enter the debugger.")

                subprocess.run(
                    ["python", "-m", "pdb", "-c", "continue", str(path)],
                    check=True,
                    env=environment,
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


def _patch_subprocess_environment(config):
    """Patch the environment of the subprocess.

    The problem is that task files are rendered and, then, stored in the hidden build
    directory. This would prohibit imports if we did not add the project root to the
    `PYTHONPATH`.

    """
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(Path(config["project_directory"])) + ";" + env.get("PYTHONPATH", "")
    )

    return env
