===============
Getting Started
===============

To get started with **pipeline**, we will take a look at a demo project over at
`OpenSourceEconomics <https://github.com/OpenSourceEconomics/pipeline-demo-project>`_.


.pipeline.yaml
--------------

At the top of the project lies a ``.pipeline.yaml``. If the file is empty, it simply
indicates the top of the project. To inspect the default configuration, type

.. code-block:: bash

    $ pipeline collect --config

If you want to deviate from the current configuration, add your keys and values to
``.pipeline.yaml``.


src, tasks, and templates
-------------------------

By default, **pipeline** assumes that your tasks rest somewhere in ``src`` and searches
the directory recursively. Tasks are defined in ``.yaml`` files. Let us take a look at
``src/data_management.yaml``.

.. code-block:: yaml

    create-random-data:
      template: create_random_data.py

Tasks are defined as dictionaries where the key, ``create-random-data``, is the unique
identifier for the task. The bare minimum for a task to be executed is the ``template``
parameter. It defines which script to execute to run the task.

In this case, we want to run ``create_random_data.py`` to generate random data for
further analysis. If you take a look at the file, you will see a pretty normal Python
scipt except for the ``{{ produces }}`` field when the data is saved. The doubled curly
braces are used in `Jinja2 <https://jinja.palletsprojects.com/en/2.11.x/>`_ templates to
insert variables. Here, you have two options: First, you can leave it as it is and
**pipeline** will fill in a path for ``{{ produces }}`` or, secondly, you can go back to
your ``data_management.yaml`` and insert ``produces: {{ build_directory
}}/data/random-data.csv`` below template, to make the output path explicit.

Next, we want to run OLS and logistic regressions on our random data. For that, we
define an ``analysis.yaml``. If you look at the file, you will find even more curly
braces. For **pipeline**, not only are templates evaluated with Jinja2, but also your
task files. The syntax is easy to understand and says, that you want to execute the task
twice, for ``"ols"`` and ``"logit"``. Insert the loop variable to your task id to make
it unique and use the method to select the pre-defined ``ols.r`` template. Formula gives
you the equation of the regression you want to run. A part of **pipeline**'s
user-friendliness is due to the ``depends_on`` key. Here, you would have normally given
the path to the random data, but with **pipeline** you only need to reference the task
id which generated the data.

Why have we run the regressions in R? Because R has ``stargazer``, an amazing package to
produce publication-ready regression tables. Let us look at ``tables.yaml``. We define a
new task ``regression-table`` and select the ``stargazer.r`` template. There is also a
``stargazer.py`` template, but it is less powerful and cannot combine OLS and logistic
regressions and deal with different dependent variables. Under ``depends_on``, we
reference the previous two tasks which ran the regressions. At last, we explicitly use
``produces`` because we want to inspect the regression table in the end. The table will
be converted to ``.html``, but Latex is also possible with ``.tex`` as the file suffix.


Execute the tasks
-----------------

To execute the pipeline, hit

.. code-block:: bash

    pipeline build


bld
---

You will find your regression table in ``bld``.

There is also a hidden folder named ``.pipeline``. It contains intermediate or internal
files produced by **pipeline**. You can also find a visualization of the projects
directed acyclic graph (DAG).
