#!/usr/bin/env python
# -*- coding:  utf-8 -*-

"""
http.manage
~~~~~~~~~~~

Production management script of HTTP Request & Response service

:copyright: (c) 2011 by Alexandr Sokolovskiy (alex@obout.ru).
:license: BSD, see LICENSE for more details.
"""
import sys

import tornado.ioloop
from tornado import httpserver
from tornado.options import options, parse_command_line
from daemon import Daemon

from app import application, rel


def main():
    """Manager entry point"""

    parse_command_line()

    class HTTPDaemon(Daemon):

        def run(self):

            http_server = httpserver.HTTPServer(application)
            http_server.listen(options.port)

#            https_server = httpserver.HTTPServer(application, ssl_options={
#                "certfile": rel("server.crt"),
#                "keyfile": rel("server.key"),
#                })
#            https_server.listen(options.ssl_port)

            ioloop = tornado.ioloop.IOLoop.instance()
            ioloop.start()

    daemon = HTTPDaemon(rel('daemons', 'http-debugger.pid'),
                        stdout=rel('daemons', 'http-debugger.log'),
                        stderr=rel('daemons', 'http-debugger.err'))

    if len(sys.argv) >= 2:
        if 'start' == sys.argv[len(sys.argv)-1]:
            daemon.start()
        elif 'stop' == sys.argv[len(sys.argv)-1]:
            daemon.stop()
        elif 'restart' == sys.argv[len(sys.argv)-1]:
            daemon.restart()
        elif 'status' == sys.argv[len(sys.argv)-1]:
            daemon.status()
        else:
            sys.exit(2)
        sys.exit(0)
    else:
        print("usage: manage.py %s start | stop | restart | status" % sys.argv[1])
        sys.exit(2)


if __name__ == "__main__":
    main()

