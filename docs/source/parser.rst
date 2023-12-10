.. _parser:

================
NIB Parser Model
================

.. autoclass:: nibarchive.NIBFormatError
    :members:


.. autofunction:: nibarchive.is_nib

.. autofunction:: nibarchive.varint

    The bit encoding can be defined as follows:

    .. code-block:: text

        ┌───────────┬──────────────────────────────────┐
        │ Value     │ Bitcoding                        │
        ├───────────┼──────────────────────────────────┤
        │ 0-127     │ 1 b b b b b b b                  │ b := number from 0 to 9
        ├───────────┼──────────────────────────────────┤
        │ 128-16383 │ 0 b b b b b b b  1 b b b b b b b │
        └───────────┴──────────────────────────────────┘

.. autoclass:: nibarchive.NIBArchiveParser
    :members:


