import subprocess
import sys
import time
from concurrent.futures.process import ProcessPoolExecutor
from pathlib import Path

import click
import jinja2
import networkx as nx
from tqdm import tqdm

from pipeline.exceptions import TaskError
from pipeline.hashing import save_hash_of_task_target
from pipeline.hashing import save_hashes_of_task_dependencies
from pipeline.shared import ensure_list


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


def execute_dag_serially(dag, tasks, env, config):
    """Naive serial scheduler for our tasks."""
    unfinished_tasks = [id_ for id_ in tasks if tasks[id_]["_needs_to_be_executed"]]
    len_task_names = list(map(len, unfinished_tasks))
    prevent_task_description_from_moving = max(len_task_names) if len_task_names else 0

    with tqdm(total=len(unfinished_tasks), bar_format=TQDM_BAR_FORMAT) as t:
        for id_ in nx.topological_sort(dag):
            if id_ in unfinished_tasks:
                t.set_description(id_.ljust(prevent_task_description_from_moving))

                save_hashes_of_task_dependencies(id_, env, dag, config)

                path = _preprocess_task(id_, tasks, env, config)

                _ = _execute_task(id_, path, config["is_debug"])

                _process_task_target(id_, tasks, config)

                t.update()


def execute_dag_parallelly(dag, tasks, env, config):
    unfinished_tasks = {id_ for id_ in tasks if tasks[id_]["_needs_to_be_executed"]}
    finished_tasks = {id_ for id_ in tasks if id_ not in unfinished_tasks}
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
                    for dependency in ensure_list(tasks[id_].get("depends_on", []))
                    for predecessor in dag.predecessors(dependency)
                ]
                all_dependencies_executed = all(dep in finished_tasks for dep in deps)
                if all_dependencies_executed:
                    save_hashes_of_task_dependencies(id_, env, dag, config)

                    path = _preprocess_task(id_, tasks, env, config)

                    future = executor.submit(
                        _execute_task, id_, path, config["is_debug"]
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
                _process_task_target(id_, tasks, config)

            finished_tasks = finished_tasks.union(newly_finished_tasks)
            unfinished_tasks = unfinished_tasks - finished_tasks - set(submitted_tasks)
            are_tasks_left = len(unfinished_tasks) != 0

            # A little bit of sleep time to wait for tasks to finish.
            time.sleep(0.1)


def _preprocess_task(id_, tasks, env, config):
    file = _render_task_template(id_, tasks[id_], env, config)

    if "produces" in tasks[id_]:
        Path(tasks[id_]["produces"]).parent.mkdir(parents=True, exist_ok=True)

    if tasks[id_]["template"].endswith(".py"):
        path = Path(config["hidden_task_directory"], id_ + ".py")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(file)

    elif tasks[id_]["template"].endswith(".r"):
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
    exc_info = (
        e.__str__()
        if not isinstance(e, subprocess.CalledProcessError)
        else e.stderr.decode("utf-8")
    )
    return f"\n\nTask '{id_}' in file '{path}' failed.\n\n{exc_info}"


def _process_task_target(id_, tasks, config):
    path = Path(tasks[id_]["produces"])
    if not path.exists():
        raise FileNotFoundError(
            f"Target '{path.as_posix()}' was not produced by task '{id_}'."
        )
    save_hash_of_task_target(id_, tasks, config)


def _render_task_template(id_, task_info, env, config):
    """Compile the file of the task."""
    template = env.get_template(task_info["template"])

    try:
        rendered_template = template.render(globals=config["globals"], **task_info)
    except jinja2.exceptions.UndefinedError as e:
        raise jinja2.exceptions.UndefinedError(
            f"Task '{id_}' has an undefined variable."
        ).with_traceback(e.__traceback__)
    else:
        return rendered_template
