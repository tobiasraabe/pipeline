import functools
import hashlib
from pathlib import Path

import yaml

from pipeline._yaml import read_yaml
from pipeline.shared import ensure_list
from pipeline.shared import render_task_template


def compare_hashes_of_task(id_, env, dag, config):
    """Compare hashes of dependencies and targets of a task.

    This function checks whether a task needs to be executed again by comparing the
    hashes of its dependencies and its targets with hashes in the database.

    If a file is missing, a hash does not match, the task is marked for execution.

    Parameters
    ----------
    id_ : str
        ID of the task.
    env : jinja2.Environment
        An environment which manages the templates.
    dag : nx.DiGraph
        The DAG containing the complete workflow.
    config : dict
        The workflow configuration.

    Return
    ------
    have_same_hashes : bool
        ``True`` if the hashes of all dependencies and targets match else ``False``

    """
    hashes = _load_hashes(config)
    hashes[id_] = hashes.get(id_, {})

    have_same_hashes = True

    dependencies_and_targets = list(dag.predecessors(id_)) + list(dag.successors(id_))
    for node in dependencies_and_targets:
        path = Path(node)

        if path.exists() or node in env.list_templates():
            if path.exists():
                hash_ = _compute_hash_of_file(path, path.stat().st_mtime)
            else:
                rendered_task = render_task_template(id_, dag.nodes[id_], env, config)
                hash_ = _compute_hash_of_string(rendered_task)

            if hash_ == hashes[id_].get(node, None):
                pass

            else:
                have_same_hashes = False
                hashes[id_][node] = hash_

        else:
            have_same_hashes = False

    _dump_hashes(hashes, config)

    return have_same_hashes


def save_hashes_of_task_dependencies(id_, env, dag, config):
    """Save file hashes of the dependencies of a task."""
    hashes = _load_hashes(config)
    for dependency in dag.predecessors(id_):
        if dependency in env.list_templates():
            pass
        else:
            path = Path(dependency)
            hash_ = _compute_hash_of_file(path, path.stat().st_mtime)
            hashes[id_][dependency] = hash_

    _dump_hashes(hashes, config)


def save_hash_of_task_target(id_, dag, config):
    """Loop over the targets of a task and save the hashes of the files."""
    hashes = _load_hashes(config)

    for string_path in ensure_list(dag.nodes[id_]["produces"]):
        path = Path(string_path)
        hash_ = _compute_hash_of_file(path, path.stat().st_mtime)
        hashes[id_][string_path] = hash_

    _dump_hashes(hashes, config)


def _load_hashes(config):
    """Load the hashes from disk."""
    path = Path(config["hidden_build_directory"], ".hashes.yaml")
    hashes = _load_hashes_helper(path, path.stat().st_mtime) if path.exists() else None
    hashes = {} if hashes is None else hashes

    return hashes


@functools.lru_cache()  # noqa: U101
def _load_hashes_helper(path, _last_modified):
    """Load the hashes from disk while caching.

    The function :func:`functools.lru_cache` caches the results of a function depending
    on the function inputs. To read the file only if the content has changed, pass the
    point in time when file was last modified as an argument. Although unused by the
    function itself, ``_last_modified`` ensures that hashes are loaded from cache if the
    file has not been modified between to requests.

    """
    return read_yaml(path.read_text())


def _dump_hashes(hashes, config):
    """Dump hashes to disk."""
    path = Path(config["hidden_build_directory"], ".hashes.yaml")
    path.write_text(yaml.dump(hashes))


@functools.lru_cache()  # noqa: U101
def _compute_hash_of_file(path, _last_modified=None, algorithm="sha256"):
    """Compute the hash of a file.

    The function uses caching to avoid computing the same hash twice if the same file is
    requested and has not been modified in the meantime.

    Taken from https://stackoverflow.com/a/44873382/7523785.

    See Also
    --------
    _load_hashes_helper

    """
    h = hashlib.new(algorithm)

    byte_array = bytearray(128 * 1024)
    memory_view = memoryview(byte_array)
    with open(path, "rb", buffering=0) as f:
        for n in iter(lambda: f.readinto(memory_view), 0):
            h.update(memory_view[:n])

    return h.hexdigest()


def _compute_hash_of_string(string, algorithm="sha256"):
    """Compute hash of a string."""
    h = hashlib.new(algorithm)
    h.update(string.encode("utf-8"))

    return h.hexdigest()
