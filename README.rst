pipeline
========

.. image:: https://anaconda.org/opensourceeconomics/pipeline/badges/version.svg
    :target: https://anaconda.org/OpenSourceEconomics/pipeline

.. image:: https://anaconda.org/opensourceeconomics/pipeline/badges/platforms.svg
    :target: https://anaconda.org/OpenSourceEconomics/pipeline

.. image:: https://readthedocs.org/projects/pipeline-wp/badge/?version=latest
    :target: https://pipeline-wp.readthedocs.io/en/latest

.. image:: https://img.shields.io/badge/License-BSD-yellow.svg
    :target: https://opensource.org/licenses/BSD

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

**pipeline** is first and foremost a build system geared to the scientific publication
process. It strives to simplify the way from data over models to results. But, it is
also extensible and flexible and can serve as a general-purpose build system for Python.

How does **pipeline** achieve this goal?

1. **pipeline** does not bother you with declaring dependencies and targets of your
   tasks. It will handle both while you only need to connect the tasks. Outputs are
   hidden from you by default so that you are not bothered with intermediate results. If
   you want have access to the output, simply assign a path.

2. **pipeline** uses both, R and Python, as backends. Users will experience the best of
   both worlds. Currently, R's ``stargazer`` package is unparalleled in its ability to
   produce publication-quality tables and many econometric models are implemented only
   in R. At the same time, users shift more and more to Python which offers a better
   user experience and grows exponentially.

3. **pipeline** leverages `Jinja2 <https://jinja.palletsprojects.com/en/2.11.x/>`_ to
   offer pre-defined templates for common tasks such as regressions (OLS, Logit, Probit)
   and producing regression tables. The templates are available in Python and R. The
   user can also define her own templates to scale tasks rapidly.

Other useful features!

- Use the ``--debug`` flag to enter the post-mortem debugger if your build fails.
- Tasks are not re-run unless anything related to the task has changed.


Installation
------------

.. Same as in docs/installation.rst.

**pipeline** is available on Anaconda.org. Use the following command for installation.

.. code-block:: bash

    $ conda config --add channels conda-forge
    $ conda install -c opensourceeconomics respy

If you plan to use R templates as well, type

.. code-block:: bash

    $ conda config --add channels r
    $ conda install rpy2<3 tidyverse stargazer

to get started with the minimum of packages. It is important that you do not use the
third version of rpy2 as it is unstable.


Usage
-----

Go into your project folder and create a `.pipeline.yaml` file which can be empty. Then,
type

.. code-block:: bash

    pipeline --help

to see which commands are available. Type

.. code-block:: bash

    pipeline collect --config/--tasks/--templates

to inspect the current project configuration, tasks, or templates found in the project.

After you have defined some tasks, hit

.. code-block:: bash

    pipeline build

to execute the tasks.


Getting Started
---------------

To get started with **pipeline**, please visit the `documentation
<https://pipeline-wp.readthedocs.io/>`_.


Todo
----

- **pipeline** is currently a working title. Please reach out to me if you have a
  suggestion for a better title.
- IMplement parallel execution
- Write documentation
  - List current limitations (no robust standard errors, logit cannot be tabularized in python)
- Write more tests
- Extend existing function calls in templates and introduce general arguments which work
  for R and Python.
