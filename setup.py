#!/usr/bin/env python

from setuptools import setup

setup(
    name="Festerize",
    version="0.3.0",
    py_modules=["festerize"],
    install_requires=["beautifulsoup4", "click", "requests"],
    entry_points="""
        [console_scripts]
        festerize=festerize:festerize
    """,
)
