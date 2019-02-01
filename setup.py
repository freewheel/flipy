#coding:utf-8
import os
import sys

from setuptools import setup, find_packages
import flippy


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "flippy",
    author = "FreeWheel",
    description = "FreeWheel Linear Programming API for Python",
    long_description = read('README.md'),
    version = flippy.version,
    packages = find_packages(),

    include_package_data = True,

    install_requires = [],
    classifiers=[
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 2 :: Only'
    ],
)
