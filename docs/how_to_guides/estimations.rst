===========
Estimations
===========

pipeline offers :doc:`../templates/index` for various estimation methods. To generate
multiple models, the ``formula`` is a powerful tool.


Formulas
--------

This `article in R for Data Science
<https://r4ds.had.co.nz/model-basics.html#formulas-and-model-families>`_ gives an
overview on the flexibility of formulas in R.

In Python, the basic syntax is completely the same and this `part of the statsmodels
documentation <https://www.statsmodels.org/dev/examples/notebooks/generated/
formulas.html>`_ is more compact than the previous suggestion.

Additionally, Python formulas are more powerful because they give direct access to the
underlying series and its methods. In Python you can do

.. code-block:: python

    formula = "y ~ x < 0"
    formula = "y ~ x.lt(0)"  # equivalent

which dynamically generates a dummy variable or even

.. code-block:: python

    formula = "y ~ x.astype(float)"

which might be convenient for prototyping, but should be avoided due to clarity.
