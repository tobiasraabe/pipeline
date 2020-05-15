=============
Configuration
=============

The configuration is defined in a ``.pipeline.yaml`` file which sits at the top of the
project.


Defaults
--------

The configuration can be left completely empty. In this case, sensible defaults are set.
You can inspect these default by typing

.. code-block:: bash

    # Windows example

    $ pipeline collect --config

    {'build_directory': 'C:/Users/user/project/bld',
     'custom_templates': [],
     'hidden_build_directory': 'C:/Users/user/project/bld/.pipeline',
     'hidden_task_directory': 'C:/Users/user/project/bld/.tasks',
     'project_directory': 'C:/Users/user/project',
     'source_directory': 'C:/Users/user/project/src',
     'user_config_file': 'C:/Users/user/project/.pipeline.yaml'}


You can overwrite any of the defaults by using the same dictionary key and a different
value inside ``.pipeline.yaml``. For example, to change the ``build_directory``, add

.. code-block:: yaml

    # .pipeline.yaml

    build_directory: build

which will be interpreted as a relative path to the project directory or the
``.pipeline.yaml`` file. You can also use absolute paths which will not be extended.


Custom templates
----------------

``custom_templates`` can be a path or a list of paths to files or directories which will
be loaded as templates.

This options is partly for convenience as you can also always use ``template:
<path-to-template>/template.py`` inside tasks. To shorten the path and only use
``template: template.py`` add the path to the template to this option.

The other and more powerful purpose of this option is to overwrite existing templates.
For instance, you might use some exotic data format which is currently not supported by
:doc:`../templates/load_data`, but you still want to use the OLS and other templates.

Then, create a template with the same file name as the template you want to overwrite.
Extend the existing function ``load_data()``.

.. code-block:: python

    # load_data.py


    def load_data(path):
        path = Path(path)

        if path.suffix == ".feather":
            df = pd.read_feather(path)

        elif path.suffix == ".orc":
            df = pd.read_orc(path)

        ...

At last, insert the path to this template in ``custom_templates`` and your
``load_data.py`` will have precedence over the existing template.


.. _configuration_globals:

Global variables
----------------

Every variable defined inside the ``.pipeline.yaml`` is passed to render task
specifications or task templates and, thus, acts like a global variable. To avoid name
collisions, you can use more nested structures like a ``global`` dictionary inside the
task specification.

.. code-block:: yaml

    # .pipeline.yaml

    globals:
      dependent_variables: [y1, y2, y3]

If you want to know how to use them inside tasks and templates, see
:ref:`tasks_global_variables_in_tasks_and_templates`.

Note that a :ref:`custom variable <tasks_custom_variables>` called ``globals`` in the
tasks templates creates a name collision.
