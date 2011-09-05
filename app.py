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
import time
from hashlib import md5
import tornado.ioloop
import tornado
from tornado.web import Application
from tornado.options import define, options
from tornado import httpserver
from tornado import autoreload
from tornado.web import HTTPError

from httplib import responses
from random import choice

from taglines import taglines
from utils import Authorization, WWWAuthentication, response, HA1, HA2, H

define("port", default=8889, help="run HTTP on the given port", type=int)
define("ssl_port", default=8890, help="run HTTPS on the given port", type=int)

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
            (r"/human_curl", HurlHandler),
            (r"/ip", IPHandler),
            (r"/get", GETHandler, "GET method"),
            (r"/post", POSTHandler, "POST method"),
            (r"/put", PUTHandler, "PUT method"),
            (r"/head", HEADHandler, "HEAD method"),
            (r"/options", OPTIONSHandler, "OPTIONS method"),
            (r"/delete", DELETEHandler, "DELETE method"),
            (r"/gzip", GZipHandler),
            (r"/user-agent", UserAgentHandler),
            (r"/headers", HeadersHandler),
            (r"/cookies", CookiesHandler, "Returns all user cookies"),
            (r"/cookies/set/(?P<name>.+)/(?P<value>.+)", CookiesHandler,
             "Setup given name and value on client"),
            (r"/status/(?P<status_code>\d{3})", StatusHandler),
            (r"/redirect/(?P<num>\d{1,2})", RedirectHandler),
            (r"/redirect/end", RedirectEndHandler),
            (r"/basic-auth/(?P<username>.+)/(?P<password>.+)", BasicAuthHandler),
            (r"/digest-auth/(?P<qop>.+)/(?P<username>.+)/(?P<password>.+)", DigestAuthHandler)]

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

    def json_response(self, data, finish=True):
        output_json = tornado.escape.json_encode(data)
        # self.set_header("Content-Type", "application/json")
        if finish is True:
            self.finish(output_json)
        else:
            return output_json


class HomeHandler(CustomHandler):
    """Show home page
    """

    def get(self):
        endpoints = []
        replace_map = (
            ("(?P<status_code>\d{3})", "{status_code: int}", str(choice(responses.keys()))),
            ("(?P<name>.+)", "{name: str}", "test_name"),
            ("(?P<value>.+)", "{value: str}", "test_value"),
            ("(?P<num>\d{1,2})", "{redirects_num: int}", '4'),
            ("(?P<username>.+)", "{username: str}", "test_username"),
            ("(?P<password>.+)", "{password: str}", "test_password"),
            ("(?P<qop>.+)", "{quality of protection: auth | auth-int}", "auth"))

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


class HurlHandler(CustomHandler):
    """Human cURL home page
    """

    def get(self):
        self.render("human_curl.html")


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


class RedirectHandler(CustomHandler):
    """Test redirects
    """

    def get(self, num=1):
        num = int(num)
        if num == 1:
            redirect = "/redirect/end"
        else:
            redirect = "/redirect/%s" % (num-1)
        self.redirect(redirect)


class RedirectEndHandler(CustomHandler):
    """Redirects endpoint
    """

    def get(self):
        self.json_response({"tagline": str(choice(taglines)),
                            "code": 200,
                            "finish": True})


class BasicAuthHandler(CustomHandler):
    """HTTP Basic access
    """

    def _request_auth(self):
        """Response no authentication header

        WWW-Authenticate: Basic realm="Fake Realm"
        """
        self.set_header("WWW-Authenticate", WWWAuthentication('Basic',
                                                              {'realm': 'Fake Realm'}).to_header())
        self.set_status(401)
        self.finish()
        return False

    def get(self, username, password):
        try:
            auth = self.request.headers.get("Authorization")
            if auth is None:
                return self._request_auth()
            else:
                try:
                    authorization_info = Authorization.from_string(auth)
                except Exception, e:
                    self._request_auth()

                if not auth.startswith("Basic "):
                    return self._request_auth()

                ## Request authorization header
                ## Authorization: Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ==

                if authorization_info['username'] == username and \
                       authorization_info['password'] == password:
                    self.json_response({"authenticated": True,
                                        'password': password,
                                        'username': username,
                                        'auth-type': 'basic'})
                else:
                    self._request_auth()
        except Exception, e:
            self._request_auth()


class DigestAuthHandler(BasicAuthHandler):
    """HTTP Digest authentication

    Digest authentication by RFC 2617
    with support qop auth and auth-int
    """

    def _request_auth(self, qop=None):
        """Build challenge header for request without Authorization header
        """

        # Generating server nonce, format propsed by RFC 2069 is
        # H(client-IP:time-stamp:private-key).
        nonce = H("%s:%d:%s" % (self.request.remote_ip,
                                  time.time(),
                                  os.urandom(10)))

        # A string of data, specified by the server, which should be
        # returned by the client unchanged.
        opaque = H(os.urandom(10))
        self.set_header("WWW-Authenticate",
                        WWWAuthentication('Digest',
                                          {'realm': "Fake Realm",
                                           'nonce': nonce,
                                           'qop': 'auth,auth-int,auth-ints' if qop is None else qop,
                                           'opaque': opaque}).to_header())
        self.set_status(401)
        self.finish()
        return False

    def get(self, username, password, qop=None):
        if qop not in ('auth', 'auth-int'):
            qop = None
        ## Response no authenticated header
        ## WWW-Authenticate: Digest realm="testrealm@host.com",
        ##                 qop="auth,auth-int",
        ##                 nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093",
        ##                 opaque="5ccc069c403ebaf9f0171e9517f40e41"
        ##
        ## HTTP Digest auth request header
        ## Authorization:Digest username="cebit;hans-joachim.ring@lvermgeo.rlp.de",
        ##                 realm="mapbender_registry",
        ##                 nonce="1c6437cc7cba6c72df4d50c46cff2f15",
        ##                 uri="/http_auth/24150",
        ##                 response="6bd4212340a437c7486184d362c6e946",
        ##                 opaque="b28db91512b288b4a97030aa968487d5",
        ##                 qop=auth,
        ##                 nc=00000002,
        ##                 cnonce="8a2782a5b869595d"

        try:
            auth = self.request.headers.get("Authorization")
            if auth is None:
                return self._request_auth(qop)
            else:
                try:
                    authorization_info = Authorization.from_string(auth)
                except Exception, e:
                    self._request_auth(qop)
                else:
                    request_info = dict()
                    request_info['uri'] = self.request.uri
                    request_info['body'] = self.request.body
                    request_info['method'] = self.request.method
                    response_hash = response(authorization_info, password, request_info)
                    if response_hash == authorization_info['response']:
                        self.json_response({"authenticated": True,
                                            'password': password,
                                            'username': username,
                                            'auth-type': 'digest'})
                    else:
                        self.set_status(403)
                        self.finish()

        except Exception, e:
            print(e)
            self._request_auth(qop)


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


class GZipHandler(METHODHandler):
    """Returns Gziped response
    """

    def get(self):
        from gzip import GzipFile
        try:
            from cString import StringIO
        except ImportError:
            from StringIO import StringIO

        data = self.get_data()
        data['gzipped'] = True
        json_response = self.json_response(data, finish=False)

        tmp_buffer = StringIO()

        gziped_buffer = GzipFile(
            fileobj=tmp_buffer,
            mode="wb",
            compresslevel=7)
        gziped_buffer.write(json_response)
        gziped_buffer.close()

        gzipped_data = tmp_buffer.getvalue()

        self.set_header("Content-Encoding", 'gzip')
        self.set_header("Content-Length", str(len(gzipped_data)))

        tmp_buffer.close()
        self.finish(gzipped_data)


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
        self.set_header("Allow", ", ".join(self.SUPPORTED_METHODS))
        self.set_header("Public", ", ".join(self.SUPPORTED_METHODS))
        self.json_response(self.get_data())


class Middleware(object):

    def __init__(self, application):
        self.application = application

    def __call__(self, request, *args, **kwargs):
        return self.application(request, *args, **kwargs)


application = HTTPApplication()


if __name__ == "__main__":
    tornado.options.parse_command_line()
    http_server = httpserver.HTTPServer(application)
    https_server = httpserver.HTTPServer(application, ssl_options={
        "certfile": rel("server.crt"),
        "keyfile": rel("server.key"),
        })
    http_server.listen(options.port)
    https_server.listen(options.ssl_port)
    ioloop = tornado.ioloop.IOLoop.instance()
    autoreload.start(io_loop=ioloop, check_time=100)
    ioloop.start()
