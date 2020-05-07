"""This module contains the code related to the DAG and the scheduler."""
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.axes_grid1 import make_axes_locatable
from networkx.drawing import nx_pydot

from pipeline.shared import ensure_list


BLUE = "#547482"
YELLOW_TO_RED = ["#C8B05C", "#C89D64", "#F1B05D", "#EE8445", "#C87259", "#6C4A4D"]


class Scheduler:
    """This class allows to schedule tasks.

    The functionality is inspired by func:`networkx.topological_sort` which allows to
    loop over a directed acyclic graph such that all preceding nodes are executed before
    a dependent node.

    The scheduler keeps track of all unfinished tasks and their dependencies in the
    `task_dict`. If a task has no dependencies, it is eligible to be executed. All
    submitted tasks are remove from `task_dict`. If a task finishes, it is removed as a
    dependency from all tasks in `task_dict`.

    The scheduler can take task priorities into account and proposes only tasks
    with the highest priorities.

    """

    def __init__(self, dag, unfinished_tasks, priority):
        self.dag = dag
        self.task_dict = self._create_task_dependency_dict(unfinished_tasks)
        self.submitted_tasks = set()
        self.priority = priority

    def _create_task_dependency_dict(self, unfinished_tasks):
        """Create a task-dependency dictionary.

        For each unfinished task, this function collects the tasks which have to be
        executed in advance.

        """
        task_dict = {}
        for id_ in unfinished_tasks:
            task_dict[id_] = {
                preceding_task
                for dependency in ensure_list(self.dag.nodes[id_].get("depends_on", []))
                for preceding_task in self.dag.predecessors(dependency)
                if preceding_task in unfinished_tasks
            }

        return task_dict

    def propose(self, n_proposals=1):
        """Propose a number of tasks.

        This function proposes tasks which can be executed. If a task is proposed,
        remove it from the `task_dict`.

        Parameters
        ----------
        n_proposals : int
            Number of tasks which should be proposed. For any nonnegative number, return
            a set of task ids. For `-1` return all possible tasks.

        Returns
        -------
        proposals : set
            A set of task ids which should be executed.

        """
        # Get task candidates.
        candidates = [id_ for id_ in self.task_dict if len(self.task_dict[id_]) == 0]
        if self.priority:
            candidates = sorted(
                candidates,
                key=lambda id_: self.dag.nodes[id_]["priority"],
                reverse=True,
            )

        if 0 <= n_proposals:
            proposals = set(candidates[:n_proposals])

        elif n_proposals == -1:
            proposals = set(candidates)

        else:
            raise NotImplementedError

        self.submitted_tasks = self.submitted_tasks.union(proposals)

        for id_ in proposals:
            del self.task_dict[id_]

        return proposals

    def process_finished(self, finished_tasks):
        """Process finished tasks.

        The executor passes an id or a list of ids of finished tasks back to the
        scheduler. The scheduler removes the ids from the set of submitted tasks and
        removes the finished tasks from the dependency sets of all unfinished tasks in
        `task_dict`.

        Parameters
        ----------
        finished_tasks : str or list
            An id or a list of ids of finished tasks.

        """
        finished_tasks = ensure_list(finished_tasks)
        for id_ in finished_tasks:
            self.submitted_tasks.remove(id_)
            for id__ in self.task_dict:
                self.task_dict[id__].discard(id_)

    @property
    def are_tasks_left(self):
        return len(self.task_dict) != 0 or len(self.submitted_tasks) != 0


def create_dag(tasks, config):
    """Create a directed acyclic graph (DAG) capturing dependencies between functions.

    Parameters
    ----------
    tasks : dict
        Dictionary containing tasks.

    Returns
    -------
    dag : nx.DiGraph
        The directed acyclic graph.

    """
    dag_dict = _create_dag_dict(tasks)
    dag = nx.DiGraph(dag_dict).reverse()
    dag = _insert_tasks_in_dag(dag, tasks)
    dag = _assign_priority_to_nodes(dag, config)

    _draw_dag(dag, config)

    return dag


def _create_dag_dict(tasks):
    dag_dict = {}
    for id_, task_info in tasks.items():
        # Add the task to the graph as a node.
        depends_on = ensure_list(task_info.get("depends_on", [])).copy()
        depends_on.extend(ensure_list(task_info.get("template", [])))
        depends_on.append(task_info["config"])

        dag_dict[id_] = depends_on

        # If the task produces anything, register the output as a node.
        for target in ensure_list(task_info.get("produces", [])):
            dag_dict[target] = [id_]

    return dag_dict


def _insert_tasks_in_dag(dag, tasks):
    for id_ in dag.nodes:
        if id_ in tasks:
            dag.nodes[id_].update(**tasks[id_], _is_task=True)
        else:
            dag.nodes[id_].update(_is_task=False)

    return dag


def _assign_priority_to_nodes(dag, config):
    """Assign a priority to a node.

    Task priorities trickle down from the last nodes in the DAG to the first nodes. The
    total priority of a task is its own priority plus the discounted sum of priorities
    of its targets.

    """
    discount_factor = config["priority_discount_factor"]
    reversed_dag = dag.reverse()
    for id_ in nx.topological_sort(reversed_dag):
        if reversed_dag.nodes[id_]["_is_task"] and config["priority_scheduling"]:
            sum_priorities = 0
            for pre in reversed_dag.predecessors(id_):
                for pre_task in reversed_dag.predecessors(pre):
                    sum_priorities += dag.nodes[pre_task].get("priority", 0)

            dag.nodes[id_]["priority"] = (
                dag.nodes[id_].get("priority", 0) + discount_factor * sum_priorities
            )
        else:
            pass

    return dag


def _draw_dag(dag, config):
    fig, ax = plt.subplots(figsize=(16, 12))

    fig.suptitle("Task Graph", fontsize=24)

    # Relabel absolute paths to path names.
    project_directory = Path(config["project_directory"])
    mapping = {
        node: Path(node).relative_to(project_directory)
        for node in dag.nodes
        if Path(node).is_absolute()
    }
    dag = nx.relabel_nodes(dag, mapping)

    layout = nx_pydot.pydot_layout(dag, prog="dot")

    nx.draw_networkx_edges(dag, pos=layout, ax=ax)
    nx.draw_networkx_labels(dag, pos=layout, ax=ax)

    # Draw non-task nodes.
    non_task_nodes = [node for node in dag.nodes if not dag.nodes[node]["_is_task"]]
    nx.draw_networkx_nodes(
        dag, pos=layout, nodelist=non_task_nodes, node_color=BLUE, ax=ax
    )

    task_nodes = [node for node in dag.nodes if dag.nodes[node]["_is_task"]]
    if config["priority_scheduling"]:
        node_size = np.array([dag.nodes[node]["priority"] for node in task_nodes])
        node_size_demeaned = node_size - node_size.min()
        node_size_relative = node_size_demeaned / node_size_demeaned.max()
        node_size = node_size_relative * 1_000 + 300

        cmap = LinearSegmentedColormap.from_list("cmap", YELLOW_TO_RED)
        priority_kwargs = {
            "node_size": node_size,
            "node_color": node_size_relative,
            "cmap": cmap,
        }
    else:
        priority_kwargs = {"node_color": BLUE}
    im = nx.draw_networkx_nodes(
        dag, pos=layout, nodelist=task_nodes, **priority_kwargs, ax=ax
    )

    if config["priority_scheduling"]:
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="3%", pad=0.1)
        fig.colorbar(im, cax=cax, orientation="vertical")
        cax.set_title("Priority")

    path = Path(config["hidden_build_directory"], ".dag.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path)
    plt.close()
