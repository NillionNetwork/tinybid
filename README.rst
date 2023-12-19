=======
tinybid
=======

Minimal pure-Python library that implements a basic single-item first-price auction via a `secure multi-party computation protocol <https://eprint.iacr.org/2023/1740>`__.

|pypi| |readthedocs| |actions| |coveralls|

.. |pypi| image:: https://badge.fury.io/py/tinybid.svg
   :target: https://badge.fury.io/py/tinybid
   :alt: PyPI version and link.

.. |readthedocs| image:: https://readthedocs.org/projects/tinybid/badge/?version=latest
   :target: https://tinybid.readthedocs.io/en/latest/?badge=latest
   :alt: Read the Docs documentation status.

.. |actions| image:: https://github.com/nillion-oss/tinybid/workflows/lint-test-cover-docs/badge.svg
   :target: https://github.com/nillion-oss/tinybid/actions/workflows/lint-test-cover-docs.yml
   :alt: GitHub Actions status.

.. |coveralls| image:: https://coveralls.io/repos/github/nillion-oss/tinybid/badge.svg?branch=main
   :target: https://coveralls.io/github/nillion-oss/tinybid?branch=main
   :alt: Coveralls test coverage summary.

Installation and Usage
----------------------

This library is available as a `package on PyPI <https://pypi.org/project/tinybid>`__:

.. code-block:: bash

    python -m pip install tinybid

The library can be imported in the usual way:

.. code-block:: python

    import tinybid
    from tinybid import *

Basic Example
^^^^^^^^^^^^^

.. |node| replace:: ``node``
.. _node: https://tinybid.readthedocs.io/en/0.1.0/_source/tinybid.html#tinybid.tinybid.node

Suppose that a workflow is supported by three nodes (parties performing a decentralized auction). The |node|_ objects would be instantiated locally by each of these three parties:

.. code-block:: python

    >>> nodes = [node(), node(), node()]

The preprocessing workflow that the nodes must execute can be simulated. The number of bids that a workflow requires must be known, and it is assumed that all permitted bid prices are integers greater than or equal to ``0`` and strictly less than a fixed maximum value. The number of bids and the number of distinct prices must be known during preprocessing:

.. code-block:: python

    >>> preprocess(nodes, bids=4, prices=16)

Each bidder must submit a request for the opportunity to submit a bid. Below, each of the four bidders creates such a request:

.. code-block:: python

    >>> request_zero = request(identifier=0)
    >>> request_one = request(identifier=1)
    >>> request_two = request(identifier=2)
    >>> request_three = request(identifier=3)

Each bidder can deliver a request to each node, and each node can then locally to generate masks that can be returned to the requesting bidder:

.. code-block:: python

    >>> masks_zero = [node.masks(request_zero) for node in nodes]
    >>> masks_one = [node.masks(request_one) for node in nodes]
    >>> masks_two = [node.masks(request_two) for node in nodes]
    >>> masks_three = [node.masks(request_three) for node in nodes]

.. |bid| replace:: ``bid``
.. _bid: https://tinybid.readthedocs.io/en/0.1.0/_source/tinybid.html#tinybid.tinybid.bid

Each bidder can then generate locally a |bid|_ instance (*i.e.*, a masked bid price):

.. code-block:: python

    >>> bid_zero = bid(masks_zero, 7)
    >>> bid_one = bid(masks_one, 11)
    >>> bid_two = bid(masks_two, 2)
    >>> bid_three = bid(masks_three, 11)

Every bidder can broadcast its masked bid to all the nodes. Each node can locally assemble these as they arrive. Once a node has received all masked bids, it can determine its share of each component of the overall outcome of the auction:

.. code-block:: python

    >>> shares = [
    ...     node.outcome([bid_zero, bid_one, bid_two, bid_three])
    ...     for node in nodes
    ... ]

.. |set| replace:: ``set``
.. _set: https://docs.python.org/3/library/functions.html#func-set

.. |int| replace:: ``int``
.. _int: https://docs.python.org/3/library/functions.html#int

The overall outcome can be reconstructed from the shares by the auction operator. The outcome is represented as a |set|_ containing the |int|_ identifiers of the winning bidders:

.. code-block:: python

    >>> list(sorted(reveal(shares)))
    [1, 3]

Development
-----------
All installation and development dependencies are fully specified in ``pyproject.toml``. The ``project.optional-dependencies`` object is used to `specify optional requirements <https://peps.python.org/pep-0621>`__ for various development tasks. This makes it possible to specify additional options (such as ``docs``, ``lint``, and so on) when performing installation using `pip <https://pypi.org/project/pip>`__:

.. code-block:: bash

    python -m pip install .[docs,lint]

Documentation
^^^^^^^^^^^^^
The documentation can be generated automatically from the source files using `Sphinx <https://www.sphinx-doc.org>`__:

.. code-block:: bash

    python -m pip install .[docs]
    cd docs
    sphinx-apidoc -f -E --templatedir=_templates -o _source .. && make html

Testing and Conventions
^^^^^^^^^^^^^^^^^^^^^^^
All unit tests are executed and their coverage is measured when using `pytest <https://docs.pytest.org>`__ (see the ``pyproject.toml`` file for configuration details):

.. code-block:: bash

    python -m pip install .[test]
    python -m pytest

Alternatively, all unit tests are included in the module itself and can be executed using `doctest <https://docs.python.org/3/library/doctest.html>`__:

.. code-block:: bash

    python src/tinybid/tinybid.py -v

Style conventions are enforced using `Pylint <https://pylint.readthedocs.io>`__:

.. code-block:: bash

    python -m pip install .[lint]
    python -m pylint src/tinybid

Contributions
^^^^^^^^^^^^^
In order to contribute to the source code, open an issue or submit a pull request on the `GitHub page <https://github.com/nillion-oss/tinybid>`__ for this library.

Versioning
^^^^^^^^^^
The version number format for this library and the changes to the library associated with version number increments conform with `Semantic Versioning 2.0.0 <https://semver.org/#semantic-versioning-200>`__.

Publishing
^^^^^^^^^^
This library can be published as a `package on PyPI <https://pypi.org/project/tinybid>`__ by a package maintainer. First, install the dependencies required for packaging and publishing:

.. code-block:: bash

    python -m pip install .[publish]

Ensure that the correct version number appears in ``pyproject.toml``, and that any links in this README document to the Read the Docs documentation of this package (or its dependencies) have appropriate version numbers. Also ensure that the Read the Docs project for this library has an `automation rule <https://docs.readthedocs.io/en/stable/automation-rules.html>`__ that activates and sets as the default all tagged versions. Create and push a tag for this version (replacing ``?.?.?`` with the version number):

.. code-block:: bash

    git tag ?.?.?
    git push origin ?.?.?

Remove any old build/distribution files. Then, package the source into a distribution archive:

.. code-block:: bash

    rm -rf build dist src/*.egg-info
    python -m build --sdist --wheel .

Finally, upload the package distribution archive to `PyPI <https://pypi.org>`__:

.. code-block:: bash

    python -m twine upload dist/*
