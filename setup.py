import os

from setuptools import setup, find_packages
import flipy


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="flipy",
    author="FreeWheel",
    description="FreeWheel Linear Programming Interface for Python",
    long_description=read('README.md'),
    version=flipy.version,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],
    classifiers=[
        'Operating System :: Microsoft :: Windows', 'Operating System :: MacOS :: MacOS X', 'Operating System :: POSIX',
        'Natural Language :: English', 'Programming Language :: Python :: 3.6', 'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3 :: Only'
    ],
)
