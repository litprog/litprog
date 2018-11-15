
import os
import io

from setuptools import setup, find_packages

BASEPATH = os.path.abspath(os.path.dirname(__file__))
README_PATH = os.path.join(BASEPATH, "README.rst")

# Get the long description from the README file
with io.open(README_PATH, encoding='utf-8') as fh:
    long_description = fh.read()

setup(
    name="litprog",
    version="0.1.0",
    description="A Literate Programming Tool",
    long_description=long_description,
    url="https://github.com/mbarkhau/litprog",
    author="Manuel Barkhau",
    author_email="mbarkhau@gmail.com",
    license="MIT",

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 1 - Planning",
        # "Development Status :: 2 - Pre-Alpha",
        # "Development Status :: 3 - Alpha",
        # "Development Status :: 4 - Beta",
        # "Development Status :: 5 - Production/Stable",

        # Indicate who your project is intended for
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",

        # Pick your license as you wish (should match "license" above)
        "License :: OSI Approved :: MIT License",

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
    ],

    # What does your project relate to?
    keywords="development literate markdown",

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),

    # Alternatively, if you want to distribute just a my_module.py, uncomment
    # this:
    #   py_modules=["my_module"],

    install_requires=[
        'docopt',
        'markdown',
        'pyphen',
        'pygments',
        'watchdog',
        'pyside',
        'six',
    ],

    # $ pip install -e .[lint,dev,test]
    extras_require={
        'lint' : ['flake8', 'pylint'],
        'dev'  : ['check-manifest'],
        'Build': ['pyinstaller'],
        'test' : ['coverage', 'pytest'],
    },

    # If there are data files included in your packages that need to be
    # installed, specify them here.
    package_data={
        # "sample": ["package_data.dat"],
    },

    # Although "package_data" is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, "data_file" will be installed into "<sys.prefix>/my_data"
    data_files=[
        # ("my_data", ["data/data_file"])
    ],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        # "console_scripts": [
        #     "sample=sample:main",
        # ],
    },
)