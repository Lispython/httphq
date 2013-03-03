#!/usr/bin/env python
# -*- coding:  utf-8 -*-
"""
gottwall
~~~~~~~~

Realtime statistics aggregation platform

:copyright: (c) 2011 - 2013 by Alexandr Lispython (alex@obout.ru).
:license: BSD, see LICENSE for more details.
"""

import sys
import os

from setuptools import setup, find_packages

try:
    readme_content = open(os.path.join(os.path.abspath(
        os.path.dirname(__file__)), "README.rst")).read()
except Exception, e:
    print(e)
    readme_content = __doc__


VERSION = "0.0.3"


def run_tests():
    from tests import suite
    return suite()

py_ver = sys.version_info

#: Python 2.x?
is_py2 = (py_ver[0] == 2)

#: Python 3.x?
is_py3 = (py_ver[0] == 3)

tests_require = [
    'nose',
    'mock==1.0.1']

install_requires = [
    "tornado==2.4.1",
    "commandor==0.1.4"]

if not (is_py3 or (is_py2 and py_ver[1] >= 7)):
    install_requires.append("importlib==1.0.2")

PACKAGE_DATA = []
PROJECT = 'httphq'
for folder in ['static', 'templates']:
    for root, dirs, files in os.walk(os.path.join(PROJECT, folder)):
        for filename in files:
            PACKAGE_DATA.append("%s/%s" % (root[len(PROJECT) + 1:], filename))

setup(
    name="httphq",
    version=VERSION,
    description="HTTP Request & Response service",
    long_description=readme_content,
    author="Alex Lispython",
    author_email="alex@obout.ru",
    maintainer="Alexandr Lispython",
    maintainer_email="alex@obout.ru",
    url="https://github.com/Lispython/httphq",
    packages=find_packages(),
    package_data={'': PACKAGE_DATA},
    entry_points={
        'console_scripts': [
            'httphq = httphq.manage:main',
        ]},
    install_requires=install_requires,
    tests_require=tests_require,
    license="BSD",
    platforms = ['Linux', 'Mac'],
    classifiers=[
        "Environment :: Web Environment",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries"
        ],
    test_suite = '__main__.run_tests'
    )
