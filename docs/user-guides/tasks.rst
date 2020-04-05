=====
Tasks
=====

.. _tasks_basics:

Basics
------

This section goes into the details of tasks. Tasks have to be defined by the user and
are the essential building blocks of a workflow which can be executed with **pipeline**.

Tasks are defined in a ``.yaml`` file which is a dictionary. The keys of the dictionary
are the ids of the tasks and the values are dictionaries with more information on the
specific task. Each task dictionary consists of at least three explicit attributes, an
id, a template, and a target.

- The unique id allows to identify the task among others and automatically generate
  placeholder names for the targets of the task.

- The template defines what the task does. Templates can be any Python or R file either
  given by the user or pre-defined by **pipeline**.

- The target yields a(multiple) path(s) to the output of the task.

As an example, assume the user has a Python script called ``simulate_data.py`` which
creates an artificial data set. Such a task may look like this:

.. code-block:: yaml

    simulated-data:
      template: simulate_data.py
      produces: {{ build_directory }}/data/simulate_data.csv

In this example, ``simulated-data`` is the unique id of the task. It cannot be assigned
again in the whole workflow. ``template`` refers to the script which is executed.
``produces`` can be a path or a list of paths in POSIX format (forward slashes) where
the output(s) of the tasks are stored. ``{{ build_directory }}`` will be replaced by the
path to the build directory for convenience. (For more information see
:doc:`configuration`.) The data set will be stored as a ``csv`` file.


Explicit / implicit target paths
--------------------------------

With **pipeline** you do not need to assign output paths to tasks. This might be handy
in case you only need the aforementioned simulated data set for regressions and summary
statistics, but you do not need to take a look at the file yourself.

In this case, first, delete the ``produces`` key and its value. The task becomes

.. code-block:: yaml

    simulated-data:
      template: simulate_data.py

Secondly, we need to provide a way for **pipeline** to inject its auto-generated output
path. In the file ``simulate_data.py``, change the following call:

.. code-block:: python

    df.to_csv("{{ build_directory }}/data/simulate_data.csv")  # original
    df.to_csv("{{ produces }}")  # new

Now, **pipeline** will inject its own output path. But, how can you link following tasks
to a task target whose exact location is unknown to you? Next section.


Declaring dependencies
----------------------

If a task depends on another task or more specifically its output, use the
``depends_on`` keyword. It is recommended to use the id of the preceding task because
even if you decide to rename the output, the link between the tasks persists.

As an example, assume there is another task which runs an OLS regression on the
simulated data set. The tasks may look like this:

.. code-block:: yaml

    ols-regression:
      template: ols.py
      depends_on: simulated-data

If a task depends on an existing data set which is not generated within the pipeline,
you have to use paths like the following example.

.. code-block:: yaml

    ols-regression:
      template: ols.py
      depends_on: {{ source_directory }}/data/real-data.csv

Inside the ``ols.py`` template, use ``{{ depends_on }}`` to inject the path.


Multiple dependencies and outputs
---------------------------------

**pipeline**'s magic currently only works with single inputs and outputs of tasks. This
pattern is desirable because the workflow becomes a collection of atomic tasks which is
better for parallelization and the redundancy of some code pieces becomes clear. The
repetitive tasks could be replaced by a single template.

But, it is also possible to assign multiple dependencies and outputs which has to be
done explicitly. Take a look at the following example:

.. code-block:: yaml

    multi-deps-and-outputs-task:
      templates: task.py
      depends_on:
        - dependency_1
        - dependency_2
      produces:
        - {{ build_directory }}/output_1.csv
        - {{ build_directory }}/output_2.csv

Within the template ``task.py``, reference a single dependency or output with the
correct list index.

.. code-block:: python

    first_dependency = "{{ depends_on[0] }}"
    second_output = "{{ produces[1] }}"


More Jinja
----------

Up to now, the expressions inside the curly braces within the tasks have not been
explained explicitly. The main point is that not only task templates are rendered with
Jinja, but also the files which define the tasks.

For example you may use a loop to launch a repetitive task and use variables defined
within the loop in the template. See the following section for an example.

The Jinja documentation offers exhaustive resources on this topic which can be found
`here <https://jinja.palletsprojects.com/en/2.11.x/templates>`_. Some examples are

- ``{% ... %}`` for statements.
- ``{{ ... }}`` for expressions to print to the template output.
- ``{# ... #}`` for comments not included in the template output.
- ``#  ... ##`` for line statements.
- ``{% for i in range(10) %}...{% endfor %}`` for loops.
- ``{% if i < 3 %}...{% elif i < 5 %}...{% else %}...{% endif %}`` for conditional
  statements.


.. _tasks_custom_variables:

Custom variables in templates
-----------------------------

All variables variables defined in a task dictionary are available in the template file.
For example, a data set should be generated with multiple seeds, then the task may look
like

.. code-block::

    {% for i in range(10) %}
    create-random-data-{{ i }}:
        template: create_random_data.py
        produces: {{ build_directory }}/data/random_data_{{ i }}.pkl
        seed: {{ i }}
    {% endfor %}

and inside the template there exist a function with

.. code-block:: python

    def generate_random_data():
        np.random.seed({{seed}})


.. _tasks_global_variables_in_tasks_and_templates:

Global variables in tasks and templates
---------------------------------------

Sometimes, it is good to have a global variable inside the tasks and templates. For
example, you might want to loop over several dependent variables and run your OLS
regression. Later, you want to collect the regressions and make a regression table.
Coding the same list of dependent variables two times may lead to errors and unnecessary
duplication.

To overcome this issue, use :ref:`global variables inside the project configuration
<configuration_globals>`. It is a dictionary and maybe used like this:

.. code-block::

    {% for dependent_variable in globals['dependent_variables'] %}
        ...
    {% endfor %}


Forbidden Keys
--------------

- ``_is_debug``
- ``_is_task``
- ``_is_unfinished``
