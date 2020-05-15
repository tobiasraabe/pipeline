import numbers
import os
from pathlib import Path

import jinja2

from pipeline.shared import ensure_list


def collect_templates(custom_templates, tasks=None):
    """Collect all templates.

    Custom or user-defined templates have precedence over default templates.

    """
    tasks = {} if tasks is None else tasks

    custom_templates = _FileAndDirectoryLoader(custom_templates)
    internal_templates = jinja2.PackageLoader("pipeline", "templates")
    task_templates, missing_templates = _collect_missing_templates(
        tasks, custom_templates, internal_templates
    )

    env = jinja2.Environment(
        loader=jinja2.ChoiceLoader(
            [task_templates, custom_templates, internal_templates]
        ),
        undefined=jinja2.StrictUndefined,
        keep_trailing_newline=True,
        line_comment_prefix="#",
    )

    # Register some Python functions which can be used in the templates. Must be
    # enclosed in this function to pick up the environment.
    def register_as_template_function(func):
        env.globals[func.__name__] = func
        return func

    register_as_template_function(tuple)
    register_as_template_function(Path)
    register_as_template_function(ensure_list)
    register_as_template_function(ensure_r_vector)

    return env, missing_templates


def _collect_missing_templates(tasks, custom, internal):
    existing_templates = custom.list_templates() + internal.list_templates()

    missing_templates = {}
    for task_info in tasks.values():
        if task_info["template"] not in existing_templates:
            path = (Path(task_info["config"]).parent / task_info["template"]).as_posix()
            missing_templates[task_info["template"]] = path

    return _FileAndDirectoryLoader(missing_templates.values()), missing_templates


class _FileAndDirectoryLoader(jinja2.BaseLoader):
    """This loader allows to load single files and directories."""

    def __init__(self, paths):
        self.files = []
        for path in paths:
            if Path(path).is_dir():
                files_in_dir = [file.as_posix() for file in Path(path).glob("*")]
                self.files.extend(files_in_dir)
            else:
                self.files.append(path)

    def get_source(self, environment, template):  # noqa: U100
        if template not in self.files:
            raise jinja2.TemplateNotFound(template)

        source = Path(template).read_text()
        mtime = os.path.getmtime(template)

        return source, template, lambda: mtime == os.path.getmtime(template)

    def list_templates(self):
        return self.files


def ensure_r_vector(x):
    """Ensures that the input is rendered as a vector in R.

    It is way more complicated to define an array in R than in Python because an array
    in R cannot end with an comma.

    Examples
    --------
    >>> ensure_r_vector("string")
    "c('string')"
    >>> ensure_r_vector(1)
    'c(1)'
    >>> ensure_r_vector(list("abcd"))
    "c('a', 'b', 'c', 'd')"
    >>> ensure_r_vector((1, 2))
    'c(1, 2)'

    """
    if isinstance(x, str):
        out = f"c('{x}')"
    elif isinstance(x, numbers.Number):
        out = f"c({x})"
    elif isinstance(x, (tuple, list)):
        mapped = map(lambda l: str(l) if isinstance(l, numbers.Number) else f"'{l}'", x)
        concatenated = ", ".join(mapped)
        out = f"c({concatenated})"
    else:
        raise NotImplementedError(
            f"'ensure_r_vector' is not defined for dtype {type(x)}"
        )

    return out
