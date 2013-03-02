#!/usr/bin/env python
# -*- coding:  utf-8 -*-

"""
http.manage
~~~~~~~~~~~

Production management script of HTTP Request & Response service

:copyright: (c) 2011 - 2013 by Alexandr Lispython (alex@obout.ru).
:license: BSD, see LICENSE for more details.
"""
import sys
import signal
import logging as logging_module
from logging import StreamHandler
from optparse import OptionParser, Option

import tornado.ioloop
from tornado import httpserver, autoreload
from tornado.options import _LogFormatter

from httphq.app import application
from commandor import Command, Commandor

logger = logging_module.getLogger('httphq')

def configure_logging(logging):
    """Configure logging handler"""
    if logging.upper() not in ['DEBUG', 'INFO', 'CRITICAL',
                               'WARNING', 'ERROR']:
        return

    logger.setLevel(getattr(logging_module, logging.upper()))

    if not logger.handlers:
        channel = StreamHandler()
        channel.setFormatter(_LogFormatter(color=False))
        logger.addHandler(channel)
    logger.info("Logging handler configured with level {0}".format(logging))


class Commandor(Commandor):
    """Arguments management utilities
    """

    def run(self, options, args):
        super(Commandor, self).run(options, args)
        self.exit()
        return True

class Start(Command):
    """Start httphq server"""
    commandor = Commandor

    options = [
        Option("-p", "--port",
               metavar=int,
               default=8890,
               help="Port to run http server"),
        Option("-r", "--reload",
               action="store_true",
               dest="reload",
               default=False,
               help="Auto realod source on changes"),
        Option("-h", "--host",
               metavar="str",
               default="127.0.0.1",
               help="Port for server"),
        Option("-l", "--logging",
               metavar="str",
               default="none",
               help="Log level")]

    def run(self, port, reload, host, logging, **kwargs):
        self.display("Configure logging")
        configure_logging(logging)

        ioloop = tornado.ioloop.IOLoop.instance()
        self.application = application

        self.http_server = httpserver.HTTPServer(application)
        self.http_server.listen(host, port)

        if reload:
            self.display("Autoreload enabled")
            autoreload.start(io_loop=ioloop, check_time=100)

        self.display("httphq running on 127.0.0.1:{0}".format(port))

        # Init signals handler
        signal.signal(signal.SIGTERM, self.sig_handler)

        # This will also catch KeyboardInterrupt exception
        signal.signal(signal.SIGINT, self.sig_handler)

        ioloop.start()

    def sig_handler(self, sig, frame):
        """Catch signal and init callback
        """
        tornado.ioloop.IOLoop.instance().add_callback(self.shutdown)

    def shutdown(self):
        """Stop server and add callback to stop i/o loop"""
        self.display("Shutting down service")
        self.http_server.stop()
        self.display("httphq is down")


## class Status(Command):
##     """Status httphq"""
##     commandor = Commandor

## class Stop(Command):
##     """Stop httphq"""
##     commandor = Commandor

## class Restart(Command):
##     """Restart httphq"""
##     commandor = Commandor

def main():
    """Manager entry point"""

    parser = OptionParser(
        usage="%prog [options] <commands> [commands options]",
        add_help_option=False)

    manager = Commandor(parser)
    manager.process()

##     parse_command_line()

##     class HTTPDaemon(Daemon):

##         def run(self):

##             http_server = httpserver.HTTPServer(application)
##             http_server.listen(options.port)

## #            https_server = httpserver.HTTPServer(application, ssl_options={
## #                "certfile": rel("server.crt"),
## #                "keyfile": rel("server.key"),
## #                })
## #            https_server.listen(options.ssl_port)

##             ioloop = tornado.ioloop.IOLoop.instance()
##             ioloop.start()

##     daemon = HTTPDaemon(rel('daemons', 'http-debugger.pid'),
##                         stdout=rel('daemons', 'http-debugger.log'),
##                         stderr=rel('daemons', 'http-debugger.err'))

##     if len(sys.argv) >= 2:
##         if 'start' == sys.argv[len(sys.argv)-1]:
##             daemon.start()
##         elif 'stop' == sys.argv[len(sys.argv)-1]:
##             daemon.stop()
##         elif 'restart' == sys.argv[len(sys.argv)-1]:
##             daemon.restart()
##         elif 'status' == sys.argv[len(sys.argv)-1]:
##             daemon.status()
##         else:
##             sys.exit(2)
##         sys.exit(0)
##     else:
##         print("usage: %s start | stop | restart | status" % sys.argv[0])
##         sys.exit(2)


if __name__ == "__main__":
    main()

