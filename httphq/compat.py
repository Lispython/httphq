#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Compatibility module
~~~~~~~~~~~~~~~~~~~~

Add utilities to support python2 and python3

:copyright: (c) 2013 by Alexandr Lispython (alex@obout.ru).
:license: BSD, see LICENSE for more details.
:github: http://github.com/Lispython/httphq

"""
import sys

py_ver = sys.version_info

#: Python 2.x?
is_py2 = (py_ver[0] == 2)

#: Python 3.x?
is_py3 = (py_ver[0] == 3)

if is_py2:
    from urllib import unquote, urlencode, quote
    try:
        from cStringIO import StringIO
        BytesIO = StringIO
    except ImportError:
        from StringIO import StringIO
        BytesIO = StringIO
else:
    # Python3
    from urllib.parse import urlencode, unquote, quote
    from io import StringIO, BytesIO
