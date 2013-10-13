#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
httphq
~~~~~~

HTTP Request & Response service

:copyright: (c) 2013 by Alexandr Lispython (alex@obout.ru).
:license: , see LICENSE for more details.
:github: http://github.com/Lispython/projectname
"""

__all__ = 'get_version',
__author__ = "GottWal team"
__license__ = "BSD, see LICENSE for more details"
__maintainer__ = "Alexandr Lispython"

try:
    __version__ = __import__('pkg_resources') \
        .get_distribution('httphq').version
except Exception:
    __version__ = 'unknown'

if __version__ == 'unknown':
    __version_info__ = (0, 0, 6)
else:
    __version_info__ = __version__.split('.')
__build__ = 0x000006


def get_version():
    return __version__
