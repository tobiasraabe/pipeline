import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx


def create_dag(dag_dict):
    """Create a directed acyclic graph (DAG) capturing dependencies between functions.

    Args:
        dag_dict (dict): Keys are nodes and values are dependencies.

    Returns:
        nx.DiGraph: The DAG.

    """
    return nx.DiGraph(dag_dict).reverse()


def draw_dag(dag, config):
    fig, ax = plt.subplots(figsize=(16, 12))

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FutureWarning)
        nx.draw_networkx(dag, layout=nx.random_layout(dag), ax=ax)

    path = Path(config["hidden_build_directory"], ".dag.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path)
    plt.close()
