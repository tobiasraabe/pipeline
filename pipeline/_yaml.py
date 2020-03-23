import yaml


class YamlLoader(yaml.SafeLoader):
    """Custom YAML loader which forbids duplicate keys.

    Disallow duplicate keys. Workaround for PyYAML issue:
    https://github.com/yaml/pyyaml/issues/165 This disables some uses of YAML merge
    (`<<`) (see the xfailed test_read_yaml_allow_merge)

    """


def construct_maping(loader, node, deep=False):
    """Construct a YAML mapping node, avoiding duplicates"""
    loader.flatten_mapping(node)
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise yaml.constructor.ConstructorError(f"Duplicate key {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


YamlLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_maping,
)


def read_yaml(string):
    """Read the given YAML string.

    The operation is similar to :func:`yaml.safe_load` while forbidding duplicate keys.

    Shamelessly stolen from `encukou <https://github.com/encukou/naucse_render/commit/
    2a81701d73c4abf3aeb4e2855597cba3b718ac13`.

    """
    return yaml.load(string, Loader=YamlLoader)
