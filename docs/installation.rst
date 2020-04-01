============
Installation
============

.. Synchronize with README.rst!

**pipeline** is available on `Anaconda.org
<https://anaconda.org/OpenSourceEconomics/pipeline>`_. Use the following command for
installation.

.. code-block:: bash

    $ conda config --add channels conda-forge
    $ conda install -c opensourceeconomics respy

If you plan to use R templates as well, type

.. code-block:: bash

    $ conda config --add channels r
    $ conda install rpy2<3 r-feather r-functional r-irkernel r-mass r-stargazer \
                    r-tidyverse r-xtable

to get started with the minimum of packages. It is important that you do not use the
third version of rpy2 on `Windows` as it is not supported.
