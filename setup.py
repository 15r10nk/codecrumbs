#!/usr/bin/env python

import codecs
import os

from setuptools import setup


def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    return codecs.open(file_path, encoding="utf-8").read()


setup(
    name="breadcrumes",
    version="0.1.0",
    author="Frank Hoffmann",
    author_email="15r10nk@polarbit.de",
    maintainer="Frank Hoffmann",
    maintainer_email="15r10nk@polarbit.de",
    license="MIT",
    url="https://github.com/15r10nk/breadcrumes",
    description="leave breadcurmes behind so that other can adopt the changes",
    long_description=read("README.rst"),
    packages=["breadcrumes"],
    python_requires=">=3.5",
    install_requires=["pytest>=3.5.0"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: Pytest",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
    ],
    entry_points={
        "pytest11": [
            "breadcrumes = breadcrumes.pytest",
        ],
    },
)
