import functools
import hashlib
from pathlib import Path

from pony import orm

from pipeline.database import Hash
from pipeline.shared import ensure_list
from pipeline.shared import render_task_template


@orm.db_session
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
    have_same_hashes = True

    dependencies_and_targets = list(dag.predecessors(id_)) + list(dag.successors(id_))
    for node in dependencies_and_targets:
        path = Path(node)

        if node in env.list_templates() or path.exists():
            if node in env.list_templates():
                rendered_task = render_task_template(id_, dag.nodes[id_], env, config)
                hash_ = _compute_hash_of_string(rendered_task)
            else:
                hash_ = _compute_hash_of_file(path, path.stat().st_mtime)

            try:
                hash_in_db = Hash[id_, node]
                assert hash_ == hash_in_db.hash
            except orm.ObjectNotFound:
                Hash(task=id_, dependency=node, hash_=hash_)
                have_same_hashes = False
            except AssertionError:
                hash_in_db.hash = hash_
                have_same_hashes = False

        else:
            have_same_hashes = False

    return have_same_hashes


@orm.db_session
def save_hashes_of_task_dependencies(id_, env, dag, config):
    """Save file hashes of the dependencies of a task."""
    for dependency in dag.predecessors(id_):
        if dependency in env.list_templates():
            rendered_task = render_task_template(id_, dag.nodes[id_], env, config)
            hash_ = _compute_hash_of_string(rendered_task)
        else:
            path = Path(dependency)
            hash_ = _compute_hash_of_file(path, path.stat().st_mtime)

        try:
            hash_in_db = Hash[id_, dependency]
        except orm.ObjectNotFound:
            Hash(task=id_, dependency=dependency, hash_=hash_)
        else:
            hash_in_db.hash = hash_


@orm.db_session
def save_hash_of_task_target(id_, dag):
    """Loop over the targets of a task and save the hashes of the files."""
    for string_path in ensure_list(dag.nodes[id_]["produces"]):
        path = Path(string_path)
        hash_ = _compute_hash_of_file(path, path.stat().st_mtime)

        try:
            hash_in_db = Hash[id_, string_path]
        except orm.ObjectNotFound:
            Hash(task=id_, dependency=string_path, hash_=hash_)
        else:
            hash_in_db.hash = hash_


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
