=========
Templates
=========

pipeline comes with some pre-defined templates for common tasks in a scientific project.
Check out the templates to see what options are available and what internal code is
executed.

Most templates come with a set of general parameters which work for all backends and
template-specific parameters.

If you want to learn about Jinja2 templates in general, see

- `Jinja2's documentation <http://jinja.palletsprojects.com/en/2.11.x/>`_.
- this `primer on Jinja templating
  <https://realpython.com/primer-on-jinja-templating/>`_.


.. toctree::
   :maxdepth: 1
   :caption: Utilities

   load_data
   save_data

.. toctree::
   :maxdepth: 1
   :caption: Estimation

   estimation
   logit
   ologit
   ols
   oprobit
   probit


.. toctree::
   :maxdepth: 1
   :caption: Results

   stargazer


.. toctree::
   :maxdepth: 1
   :caption: Figures

   distplot
   figure
   regplot
