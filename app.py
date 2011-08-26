#!/usr/bin/env python
# -*- coding:  utf-8 -*-
"""
http.app
~~~~~~~~~

Core of HTTP Request & Response service

:copyright: (c) 2011 by Alexandr Sokolovskiy (alex@obout.ru).
:license: BSD, see LICENSE for more details.
"""

import os
import sys
import tornado.ioloop
import tornado
from tornado.web import Application
from tornado.options import define, options
from tornado import httpserver
from tornado import autoreload
from tornado.web import HTTPError
from daemon import Daemon
from httplib import responses
from random import choice

from taglines import taglines

define("port", default=8889, help="run on the given port", type=int)

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))


def rel(*args):
    return os.path.join(PROJECT_ROOT, *args)

STATUSES_WITHOUT_BODY = (204, 205, 304)
STATUSES_WITH_LOCATION = (301, 302, 303, 305, 307)
STATUSES_WITH_AUHT = (401, )
STATUSES_WITH_PROXY_AUTH = (407, )


def get_status_extdescription(status):
    if status in STATUSES_WITH_PROXY_AUTH:
        return "Will also return this extra header: Proxy-Authenticate: Basic realm=\"Fake Realm\""
    elif status in STATUSES_WITH_AUHT:
        return "Will also return this extra header: WWW-Authenticate: Basic realm=\"Fake Realm\""
    elif status in STATUSES_WITH_LOCATION:
        return "Will also return this extra header: Location: http://http.obout.ru"
    elif status in STATUSES_WITHOUT_BODY:
        return "Won't return a response body"
    else:
        return None


class HTTPApplication(Application):
    """Base application
    """

    def __init__(self):
        self.dirty_handlers = [
            (r"/", HomeHandler),
            (r"/ip", IPHandler),
            (r"/get", GETHandler, "GET method"),
            (r"/post", POSTHandler, "POST method"),
            (r"/put", PUTHandler, "PUT method"),
            (r"/head", HEADHandler, "HEAD method"),
            (r"/options", OPTIONSHandler, "OPTIONS method"),
            (r"/delete", DELETEHandler, "DELETE method"),
            (r"/user-agent", UserAgentHandler),
            (r"/headers", HeadersHandler),
            (r"/cookies", CookiesHandler, "Returns all user cookies"),
            (r"/cookies/set/(?P<name>.+)/(?P<value>.+)", CookiesHandler,
             "Setup given name and value on client"),
            (r"/status/(?P<status_code>\d{3})", StatusHandler)]

        settings = dict(
            site_title=u"HTTP Request & Response service",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=False,
            cookie_secret="11oETzfjkrebfgjKXQLKHFJKkjjnFLDnDKJjNSDAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
            autoescape=None,
        )
        tornado.web.Application.__init__(self, [(h[0], h[1]) for h in self.dirty_handlers], **settings)


class CustomHandler(tornado.web.RequestHandler):
    """Custom handler with good methods
    """

    def __init__(self, *args, **kwargs):
        super(CustomHandler, self).__init__(*args, **kwargs)
        self.set_header("Server", "LightBeer/0.568")

    def json_response(self, data):
        output_json = tornado.escape.json_encode(data)
        self.set_header("Content-Type", "application/json")
        self.finish(output_json)


class HomeHandler(CustomHandler):
    """Show home page
    """

    def get(self):
        endpoints = []
        replace_map = (
            ("(?P<status_code>\d{3})", "{status_code: int}", str(choice(responses.keys()))),
            ("(?P<name>.+)", "{name: str}", "test_name"),
            ("(?P<value>.+)", "{value: str}", "test_value"))

        for point in self.application.dirty_handlers:
            default_url = point[0]
            api_format = point[0]
            for r in replace_map:
                default_url = default_url.replace(r[0], r[2])
                api_format = api_format.replace(r[0], r[1])
            description = point[2] if len(point) >= 3 else point[1].__doc__.strip()
            endpoint = {"default_url": default_url,
                        "api_format": api_format,
                        "description": description}
            endpoints.append(endpoint)

        responses_groups = (
            (100, 200, "1xx Informational", []),
            (200, 300, "2xx Success", []),
            (300, 400, "3xx Redirection", []),
            (400, 500, "4xx Client Error", []),
            (500, 600, "5xx Server Error", []))

        groups = []
        for i, group in enumerate(responses_groups):
            groups.append([group[0], group[1], group[2],
                           [(k, v, get_status_extdescription(k)) for k, v in responses.items()
                            if group[0] <= k < group[1]]])

        self.render("index.html", endpoints=endpoints, groups=groups)


class StatusHandler(CustomHandler):
    """Returns given HTTP status code
    """

    def get(self, status_code):
        status_code = int(status_code)
        if status_code not in responses.keys():
            raise HTTPError(404)

        self.set_status(status_code)

        if status_code in STATUSES_WITHOUT_BODY:
            self.finish()
        elif status_code in STATUSES_WITH_LOCATION:
            self.set_header("Location", self.request.host)
        elif status_code in STATUSES_WITH_AUHT:
            self.set_header("WWW-Authenticate", 'Basic realm="Fake Realm"')
        elif status_code in STATUSES_WITH_PROXY_AUTH:
            self.set_header("Proxy-Authenticate", 'Basic realm="Fake Realm"')
        else:
            self.json_response({"tagline": str(choice(taglines)),
                            "code": status_code,
                            "description": responses.get(status_code)})


class UserAgentHandler(CustomHandler):
    """Returns user agent
    """

    def get(self):
        output = {"user-agent": self.request.headers.get("User-Agent")}
        self.json_response(output)


class IPHandler(CustomHandler):
    """Returns client IP and proxies
    """

    def get(self):
        output = {"ip": self.request.remote_ip}
        hs = ("X-Real-Ip", "X-Forwarded-For", "X-Real-IP")
        for h in hs:
            if self.request.headers.get(h):
                output[h] = self.request.headers.get(h)
        self.json_response(output)


class HeadersHandler(CustomHandler):
    """Returns sended headers
    """

    def get(self):
        output = {}
        for k, v in self.request.headers.items():
            output[k] = v
        self.json_response(output)


class CookiesHandler(CustomHandler):
    """Cookies handler
    """

    def get(self, name=None, value=None):
        if name and value:
            self.set_cookie(name, value)
            self.redirect("/cookies")
        cookies = dict([(k, v.value) for k, v in self.cookies.items()])
        self.json_response(cookies)


class METHODHandler(CustomHandler):
    """Base class for methods handlers
    """

    def get_data(self):
        data = {}
        data['args'] = dict([(k, v) for k, v in self.request.arguments.items()])
        data['headers'] = dict([(k, v) for k, v in self.request.headers.items()])
        data['ip'] = self.request.headers.get("X-Real-Ip",
                                              self.request.headers.get("X-RealI-IP",
                                                                       self.request.headers.get("X-Forwarded-For", self.request.remote_ip)))
        data['url'] = self.request.full_url()
        data['request_time'] = self.request.request_time()
        data['start_time'] = self.request._start_time

        if self.request.method in ("POST", "PUT", "PATCH"):
            data['body'] = self.request.body
            data['files'] = {}
            for k, v in self.request.files.items():
                data['files'][k] = [dict(filename=x['filename'],
                                         content_type=x['content_type'],
                                         body=x['body'] if len(x['body']) < 500 else x['body'][:500])
                                    for x in v]
        return data


class GETHandler(METHODHandler):
    """GET method
    """

    def get(self):
        self.json_response(self.get_data())


class POSTHandler(METHODHandler):
    """POST method
    """

    def post(self):
        self.set_status(201)
        self.json_response(self.get_data())


class DELETEHandler(METHODHandler):
    """DELETE method
    """

    def delete(self):
        self.json_response(self.get_data())


class PUTHandler(METHODHandler):
    """PUT method
    """

    def put(self):
        self.json_response(self.get_data())


class HEADHandler(METHODHandler):
    """HEAD method
    """

    def head(self):
        self.json_response(self.get_data())


class OPTIONSHandler(METHODHandler):
    """OPTIONS method
    """

    def options(self):
        self.json_response(self.get_data())


class Middleware(object):

    def __init__(self, application):
        self.application = application

    def __call__(self, request, *args, **kwargs):
        return self.application(request, *args, **kwargs)


application = HTTPApplication()


def main():
    tornado.options.parse_command_line()
    http_server = httpserver.HTTPServer(application)
    http_server.listen(options.port)
    ioloop = tornado.ioloop.IOLoop.instance()
    autoreload.start(io_loop=ioloop, check_time=100)
    ioloop.start()


def production():
    print("Production application manager")

    tornado.options.parse_command_line()

    class HTTPDaemon(Daemon):

        def run(self):
            http_server = httpserver.HTTPServer(application)
            http_server.listen(options.port)
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
