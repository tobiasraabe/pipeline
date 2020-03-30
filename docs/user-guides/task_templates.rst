==============
Task Templates
==============

Custom variables in templates
-----------------------------

All variables variables defined in a task dictionary are available in the template file.
For example, a data set should be generated with multiple seeds, then the task may look
like

.. code-block:: yaml

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


Forbidden Keys
--------------

- ``_is_debug``
- ``_is_task``
- ``_is_unfinished``
