# This file is part of the litprog project
# https://github.com/litprog/litprog
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

import os
import sys
import setuptools

def project_path(*sub_paths):
    project_dirpath = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(project_dirpath, *sub_paths)


def read(*sub_paths):
    with open(project_path(*sub_paths), mode="rb") as fobj:
        return fobj.read().decode("utf-8")


def read_requirements(subset):
    return [
        line.strip()
        for line in read("requirements", "pypi_" + subset +".txt").splitlines()
        if line.strip() and not line.startswith("#")
    ]


long_description = "\n\n".join((read("README.md"), read("CHANGELOG.md")))

try:
    import lib3to6
    cmdclass = {'build_py': lib3to6.build_py}
except ImportError:
    cmdclass = {}


setuptools.setup(
    name="litprog",
    license="MIT",
    author="Manuel Barkhau",
    author_email="mbarkhau@gmail.com",
    url="https://github.com/litprog/litprog",
    version="2021.1005a0",
    keywords="literate programming markdown litprog",
    description="Literate Programming using Markdown.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=['litprog'],
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=True,
    install_requires=read_requirements("default"),
    extras_require={
        'html': read_requirements("html"),
        'pdf': read_requirements("html") + read_requirements("pdf"),
    },
    entry_points="""
        [console_scripts]
        lit=litprog.cli:cli
    """,
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
