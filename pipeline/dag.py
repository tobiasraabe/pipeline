import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

from pipeline.shared import ensure_list


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
        if "produces" in task_info:
            dag_dict[task_info["produces"]] = [id_]

    return dag_dict


def _insert_tasks_in_dag(dag, tasks):
    for id_ in dag.nodes:
        if id_ in tasks:
            dag.nodes[id_].update(**tasks[id_], _is_task=True)
        else:
            dag.nodes[id_].update(_is_task=False)

    return dag


def _assign_priority_to_nodes(dag, config):
    """Assign a priority to a node."""
    discount_factor = config["priority_discount_factor"]
    reversed_dag = dag.reverse()
    for id_ in nx.topological_sort(reversed_dag):
        dag.nodes[id_]["priority"] = dag.nodes[id_].get("priority", 0)

        if config["priority"]:
            sum_priorities = 0
            for pre in reversed_dag.predecessors(id_):
                dag.nodes[pre]["priority"] = dag.nodes[pre].get("priority", 0)
                sum_priorities += dag.nodes[pre]["priority"]

            dag.nodes[id_]["priority"] = (
                dag.nodes[id_]["priority"] + discount_factor * sum_priorities
            )

    return dag


def _draw_dag(dag, config):
    fig, ax = plt.subplots(figsize=(16, 12))

    # Relabel nodes.
    mapping = {node: Path(node).name for node in dag.nodes}
    dag = nx.relabel_nodes(dag, mapping)

    if config["priority"]:
        # Generate node size. By default 300. Squeeze between 300 and 1_300.
        node_size = np.array([dag.nodes[node]["priority"] for node in dag.nodes])
        node_size_demeaned = node_size - node_size.min()
        node_size_relative = node_size_demeaned / node_size_demeaned.max()
        node_size = node_size_relative * 1_000 + 300
        priority_kwargs = {
            "node_size": node_size,
            "node_color": node_size_relative,
            "cmap": "coolwarm",
        }
    else:
        priority_kwargs = {}

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FutureWarning)
        nx.draw_networkx(dag, layout=nx.random_layout(dag), ax=ax, **priority_kwargs)

    path = Path(config["hidden_build_directory"], ".dag.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path)
    plt.close()
