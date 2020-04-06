=========
Debugging
=========

Debugging a workflow should be easy which is why **pipeline** offers multiple ways to do
it.


Basics
------

``pdbpp`` or `pdb++ <https://github.com/pdbpp/pdbpp>`_ is a drop-in replacement for the
standard Python debugger ``pdb``. Check it out, especially the sticky mode.


The ``debug`` flag
------------------

For Python tasks, it is possible to jump into the debugger if a task raises an error
with the debug flag. Add it to build command by typing

.. code-block:: bash

    $ pipeline build --debug


The rendered task template
--------------------------

Sometimes a look at the rendered task template helps. Check out the files in
``bld/.tasks`` and find the file which belongs to your task. The name of the file should
be the name of the task plus the appropriate suffix.

If you find a flaw in the template which cannot be solved by better input for the
template, you can copy the rendered template to your source folder and use it as your
custom template as explained in :ref:`tasks_basics`. Then, change the file to fix the
issue.

In addition to that, please file a `bug report or enhancement issue
<https://github.com/OpenSourceEconomics/pipeline/issues/new/choose>`_ to improve the
templates.
