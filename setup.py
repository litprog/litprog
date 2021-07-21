# This file is part of the litprog project
# https://github.com/litprog/litprog
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

import os
import sys
import setuptools

try:
    import fastentrypoints  # noqa
except ImportError:
    pass


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

install_requires = read_requirements("default")

package_dir = {"": "src"}

if any(arg.startswith("bdist") for arg in sys.argv):
    import lib3to6
    package_dir = lib3to6.fix(
        package_dir,
        target_version="3.6",
        install_requires=install_requires,
        default_mode='enabled',
    )


package_data_globs = [
    "*.js",
    "*.css",
    "*.html",
    "*.svg",
    "*.png",
    "static/fonts/KaTeX*",
    "static/fonts/katex.css",
    "static/fonts/iosevka-term-ss05-regular*",
    "static/fonts/enriqueta-v10-latin-ext_latin*",
    "static/fonts/bitter-v17-latin-ext_latin*",
]

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
    package_dir=package_dir,
    include_package_data=True,
    package_data={'litprog': package_data_globs},
    zip_safe=True,
    install_requires=install_requires,
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
