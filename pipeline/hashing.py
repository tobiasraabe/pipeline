import functools
import hashlib
from pathlib import Path

import yaml

from pipeline._yaml import read_yaml


def compare_hashes_of_task(id_, env, dag, config):
    """Compute hashes"""
    hashes = _load_hashes(config)
    hashes[id_] = hashes.get(id_, {})

    have_same_hashes = True

    dependencies_and_targets = list(dag.predecessors(id_)) + list(dag.successors(id_))
    for node in dependencies_and_targets:
        path = Path(node)

        if path.exists():
            hash_ = _compute_hash(path, path.stat().st_mtime)

            if hash_ == hashes[id_].get(node, None):
                pass
            else:
                have_same_hashes = False
                hashes[id_][node] = hash_

        # Currently, we do not check whether templates have changed.
        elif node in env.list_templates():
            pass

        else:
            have_same_hashes = False

    _dump_hashes(hashes, config)

    return have_same_hashes


def save_hash_of_task_target(id_, tasks, config):
    hashes = _load_hashes(config)
    path = Path(tasks[id_]["produces"])
    hash_ = _compute_hash(path, path.stat().st_mtime)
    hashes[id_][tasks[id_]["produces"]] = hash_
    _dump_hashes(hashes, config)


def _load_hashes(config):
    path = Path(config["hidden_build_directory"], ".hashes.yaml")
    hashes = _load_hashes_helper(path, path.stat().st_mtime) if path.exists() else None
    hashes = {} if hashes is None else hashes

    return hashes


@functools.lru_cache()  # noqa: U101
def _load_hashes_helper(path, _last_modified):
    return read_yaml(path.read_text())


def _dump_hashes(hashes, config):
    path = Path(config["hidden_build_directory"], ".hashes.yaml")
    path.write_text(yaml.dump(hashes))


@functools.lru_cache()  # noqa: U101
def _compute_hash(path, _last_modified=None, algorithm="sha256"):
    """Compute the hash of a file.

    Taken from https://stackoverflow.com/a/44873382/7523785.

    """
    h = hashlib.new(algorithm)

    byte_array = bytearray(128 * 1024)
    memory_view = memoryview(byte_array)
    with open(path, "rb", buffering=0) as f:
        for n in iter(lambda: f.readinto(memory_view), 0):
            h.update(memory_view[:n])

    return h.hexdigest()
