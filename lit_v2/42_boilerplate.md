
## Common Boilerplate

### License Header

All files start with some legal boilerplate. I honestly can't say what legal relevance of this is, probably it's mostly just ceremonial.

```python
# lp: boilerplate::preamble::license_header

# This file is part of the litprog project
# https://gitlab.com/mbarkhau/litprog
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
```

Since the litprog tool is self hosting, there is a good chance that it breaks itself during development. Adding source files to git offers a convenient way to revert to a previously known good state.

### Generated Preamble

In case somebody browses the generated files, we add some more boilerplate to each file to warn them that their changes will be overwritten.

```python
# lp: boilerplate::preamble::generated

###################################
#    This is a generated file.    #
# This file should not be edited. #
#  Changes will be overwritten!   #
###################################
```

### Logging

Most modules have their own local logger named `log`. If `litprog` is used as a library, then logging configuration is left to the importing module. If the `litprog` cli command is used, then logging is configured via the `litprog.cli` submodule.

```python
# lp: boilerplate::module::logger
import logging

log = logging.getLogger(__name__)
```


### The `litprog` Package

All generated code is written to `src/litprog/`, starting with `src/litprog/__init__.py` which is empty except for the version string.

```yaml
filepath: "src/litprog/__init__.py"
inputs  : ["boilerplate::preamble::*", "dunder_version"]
```

Note that version strings may appear to be hard-coded, but they are in fact programmatically updated before each release using `make bump_version` or `pycalver bump`.

```python
# lp: dunder_version

__version__ = "v201901.0001-alpha"
```

### Common Imports

Across the implementation of LitProg there are commonly used aliases for imported modules. In general, the plain `import x` or `import longlib as ll` imports are preferred over `from x import y` so that usage code always includes the context from where they came.

```python
# lp: boilerplate::module::imports
import os
import io
import re
import sys
import math
import time
import enum
import os.path
import collections
import typing as typ
import pathlib2 as pl
import operator as op
import datetime as dt
import itertools as it
import functools as ft

InputPaths = typ.Sequence[str]
FilePaths = typ.Iterable[pl.Path]

ExitCode = int
```

Since the reader may not have access to the output files and be able to look at all symbols that have been imported into a module, it is better to establish idioms/conventions about imported modules and have fully qualified references to the attributes of a module, rather than relying on those attributes having been imported and injected into the scope of the current module.

