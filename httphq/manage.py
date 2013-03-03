#!/usr/bin/env python
# -*- coding:  utf-8 -*-

"""
http.manage
~~~~~~~~~~~

Production management script of HTTP Request & Response service

:copyright: (c) 2011 - 2013 by Alexandr Lispython (alex@obout.ru).
:license: BSD, see LICENSE for more details.
:github: http://github.com/Lispython/httphq
"""

import time
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
        return True

class Server(Command):
    """httphq server"""
    commandor = Commandor


class Start(Command):
    """Start httphq server"""
    parent = Server

    options = [
        Option("-p", "--port",
               metavar=int,
               default=8891,
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
        self.http_server.listen(port, host)

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
        io_loop = tornado.ioloop.IOLoop.instance()
        io_loop.add_timeout(time.time() + 2, io_loop.stop)

        self.display("httphq is down")


def main():
    """Manager entry point"""

    parser = OptionParser(
        usage="%prog [options] <commands> [commands options]",
        add_help_option=False)

    manager = Commandor(parser)
    manager.process()

if __name__ == "__main__":
    main()

