===============
Task priorities
===============

A similar workflow is available as a `demo project <https://github.com/
OpenSourceEconomics/pipeline-demo-project/tree/master/priority-scheduling>`_.

With pipeline you are able to assign priorities to tasks such that the execution of
tasks with higher priorities is preferred over tasks with lower priority.

This feature was designed with task queues for complex bootstraps or Monte Carlo
simulations in mind. Given that the necessary number of trials is unknown prior to the
analysis, it is necessary to start, resume, and add more tasks to the task queue.

As an example, let us assume you want to compute the confidence intervals for
coefficients of an OLS regression with case resampling bootstrap. To acquire the
coefficients, you have to sample a data set, fit a regression, extract the statistics
and present the information from n trials.

If you start the task queue for the bootstrap without task priorities, the regressions
are as likely to be executed than a new data set is sampled. If you pause the execution
at some point in time to have a look at the statistics and decide whether more trials
are needed, it might be the case that you have not run many regressions, but already
sampled more data sets than necessary.

To overcome this problem, you can assign task priorities. There are two ways to do this.
First, you can assign a priority to each individual task in the ``.yaml`` files. A task
definition might look like this:

.. code-block:: jinja

    {% for i in range(n_trials) %}

    sample-data-{{ i }}:
      template: sample_data.py
      priority: 1

    ols-{{ i }}:
      template: ols.py
      depends_on: sample-data
      priority: 2

    extract-information-{{ i }}:
      template: extract_information.py
      depends_on: ols
      priority: 3

    {% endfor %}

    plot-distribution:
      template: plot_distribution.py
      depends_on:
        {% for i in range(n_trials) %}
        - extract-information-{{ i }}
        {% endfor %}
      priority: 4

Priorities can be positive and negative and tasks with higher priority are always
preferred. The default priority of a task is zero.

Running a pipeline with such priorities would ensure that a continued execution from
sampling to extraction is preferred over sampling additional data sets.

Although, it is simple to assign priorities in this example, pipeline offers an
additional and more convenient solution. Ultimately, you are interested in the
distribution of statistics. So, we put a priority of 1 on the last task which plots the
distribution.

.. code-block:: jinja

    plot-distribution:
      template: plot_distribution.py
      depends_on:
        {% for i in range(n_trials) %}
        - extract-information-{{ i }}
        {% endfor %}
      priority: 1

Now, we want this priority to also influence the priority of preceding tasks. The
natural way to do this is to say the priority :math:`P` of a task :math:`i` is defined
by its individual priority :math:`p` and the sum of priorities of its child tasks
:math:`j`.

.. math:: P_i = p_i + \sum_j P_j

Walking backwards through the workflow from end nodes to starting nodes, priorities
trickle down the task graph. Unfortunately, every task has a priority of one in the end
and we have no priorities. Here is workflow of the remaining three tasks with implicit
priorities in round brackets.

.. code-block:: jinja

    {% for i in range(n_trials) %}

    sample-data-{{ i }}:
      template: sample_data.py
      (priority: 1)

    ols-{{ i }}:
      template: ols.py
      depends_on: sample-data
      (priority: 1)

    extract-information-{{ i }}:
      template: extract_information.py
      depends_on: ols
      (priority: 1)

    {% endfor %}

The trick is to make priorities decay while they are trickling down the task graph.
Thus, the user is able to set a discount factor. Task priorities are now calculated with

.. math:: P_i = p_i + \delta \sum_j P_j

where :math:`\delta` is the discount factor. If the discount factor is set to 0.5 and we
assign a priority of 1 to the last task, the implicit priorities are

.. code-block:: jinja

    {% for i in range(n_trials) %}

    sample-data-{{ i }}:
      template: sample_data.py
      (priority: 0.125)

    ols-{{ i }}:
      template: ols.py
      depends_on: sample-data
      (priority: 0.25)

    extract-information-{{ i }}:
      template: extract_information.py
      depends_on: ols
      (priority: 0.5)

    {% endfor %}

    plot-distribution:
      template: plot_distribution.py
      depends_on:
        {% for i in range(n_trials) %}
        - extract-information-{{ i }}
        {% endfor %}
      priority: 1

The discount factor can be set in ``.pipeline.yaml`` with

.. code-block:: yaml

    # .pipeline.yaml

    priority_discount_factor: 0.5

In general, scheduling tasks by priorities is disabled. You can always use the flags
``--priority/--no-priority`` for the build steps to turn the feature on and off. The
flags also overwrite behavior defined in ``.pipeline.yaml`` with

.. code-block:: yaml

    # .pipeline.yaml

    priority: true
