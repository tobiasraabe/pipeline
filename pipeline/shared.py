"""This module contains code which is used across modules."""
import jinja2


def ensure_list(string_or_list):
    """Ensure that the input is converted to a list.

    Parameters
    ----------
    string_or_list : str or list

    Returns
    -------
    list

    Examples
    --------
    >>> ensure_list("a")
    ['a']
    >>> ensure_list(["b"])
    ['b']

    """
    return [string_or_list] if isinstance(string_or_list, str) else string_or_list


def render_task_template(id_, task_info, env, config):
    """Compile the file of the task."""
    template = env.get_template(task_info["template"])

    try:
        rendered_template = template.render(**config, **task_info)
    except jinja2.exceptions.UndefinedError as e:
        raise jinja2.exceptions.UndefinedError(
            f"Task '{id_}' has an undefined variable."
        ).with_traceback(e.__traceback__)
    else:
        return rendered_template
