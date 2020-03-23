import os
from pathlib import Path
import jinja2
from pipeline.shared import ensure_list


def collect_templates(custom_templates, tasks=None):
    """Collect all templates.

    Custom or user-defined templates have precedence over default templates.

    """
    tasks = {} if tasks is None else tasks

    custom_templates = jinja2.FileSystemLoader(custom_templates)
    internal_templates = jinja2.PackageLoader("pipeline", "templates")
    task_templates, missing_templates = _collect_missing_templates(
        tasks, custom_templates, internal_templates
    )

    env = jinja2.Environment(
        loader=jinja2.ChoiceLoader(
            [task_templates, custom_templates, internal_templates]
        ),
        undefined=jinja2.StrictUndefined,
    )

    # Register some Python functions which can be used in the templates.
    def register_as_template_function(func):
        env.globals[func.__name__] = func
        return func

    register_as_template_function(tuple)
    register_as_template_function(Path)
    register_as_template_function(ensure_list)

    return env, missing_templates


def _collect_missing_templates(tasks, custom, internal):
    existing_templates = custom.list_templates() + internal.list_templates()

    missing_templates = {}
    for task_info in tasks.values():
        if task_info["template"] not in existing_templates:
            path = (Path(task_info["config"]).parent / task_info["template"]).as_posix()
            missing_templates[task_info["template"]] = path

    return FileLoader(missing_templates.values()), missing_templates


class FileLoader(jinja2.BaseLoader):
    """This loader allows to load single files.

    Why do I even need to program this?

    """

    def __init__(self, files):
        self.files = files

    def get_source(self, environment, template):  # noqa: U100
        if template not in self.files:
            raise jinja2.TemplateNotFound(template)

        source = Path(template).read_text()
        mtime = os.path.getmtime(template)

        return source, template, lambda: mtime == os.path.getmtime(template)

    def list_templates(self):
        return self.files
