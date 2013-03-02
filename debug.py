#!/usr/bin/env python
# -*- coding:  utf-8 -*-

"""
httphq.debug
~~~~~~~~~~~~

Local debug runner

:copyright: (c) 2011 - 2013 by Alexandr Lispython (alex@obout.ru).
:license: BSD, see LICENSE for more details.
"""
import tornado.ioloop
from tornado import httpserver, autoreload
from tornado.options import options, parse_command_line

from httphq.app import application, rel


if __name__ == '__main__':
    parse_command_line()
    http_server = httpserver.HTTPServer(application)
    https_server = httpserver.HTTPServer(application, ssl_options={
        "certfile": rel("..", "server.crt"),
        "keyfile": rel("..", "server.key"),
        })
    http_server.listen(options.port)
    https_server.listen(options.ssl_port)
    ioloop = tornado.ioloop.IOLoop.instance()
    autoreload.start(io_loop=ioloop, check_time=100)
    ioloop.start()
