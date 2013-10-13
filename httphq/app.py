#!/usr/bin/env python
# -*- coding:  utf-8 -*-
"""
http.app
~~~~~~~~~

Core of HTTP Request & Response service

:copyright: (c) 2011 by Alexandr Lispython (alex@obout.ru).
:license: BSD, see LICENSE for more details.
:github: http://github.com/Lispython/httphq
"""

import os
import sys
import time
import tornado.ioloop
import tornado
import hmac
import binascii
try:
    import urlparse
except ImportError:
    # Python3
    from urllib import parse as urlparse

try:
    from urlparse import parse_qs
    parse_qs # placate pyflakes
except ImportError:
    try:
        # Python3
        from urllib.parse import parse_qs
    except ImportError:
        # fall back for Python 2.5
        from cgi import parse_qs

from tornado.web import Application
from tornado.options import define, options
from tornado import httpserver
from tornado import autoreload
from tornado.web import HTTPError
from tornado.escape import utf8

from random import choice
from string import ascii_letters, ascii_uppercase, ascii_lowercase

try:
    from hashlib import sha1
    sha = sha1
except ImportError:
    # hashlib was added in Python 2.5
    import sha


from httphq.taglines import taglines
from httphq.utils import Authorization, WWWAuthentication, response, HA1, HA2, H
from httphq.settings import responses
from httphq.compat import unquote, urlencode, quote, BytesIO

define("port", default=8889, help="run HTTP on the given port", type=int)
define("ssl_port", default=8890, help="run HTTPS on the given port", type=int)

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))


def rel(*args):
    return os.path.join(PROJECT_ROOT, *args)

STATUSES_WITHOUT_BODY = (204, 205, 304)
STATUSES_WITH_LOCATION = (301, 302, 303, 305, 307)
STATUSES_WITH_AUHT = (401, )
STATUSES_WITH_PROXY_AUTH = (407, )


random_string = lambda x=10: ''.join([choice(ascii_letters + ascii_uppercase + ascii_lowercase)
                                   for x in range(x)])


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
            (r"/robots.txt", RobotsResourceHandler),
            (r"/humans.txt", HumansResourceHandler),
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
            (r"/digest-auth/(?P<qop>.+)/(?P<username>.+)/(?P<password>.+)", DigestAuthHandler),
            (r"/oauth/(?P<version>.+)/request_token/(?P<consumer_key>.+)/(?P<consumer_secret>.+)/(?P<token_key>.+)/(?P<token_secret>.+)", OAuthRequestTokenHandler),
            (r"/oauth/(?P<version>.+)/authorize/(?P<pin>.+)", OAuthAuthorizeHandler),
            (r"/oauth/(?P<version>.+)/access_token/(?P<consumer_key>.+)/(?P<consumer_secret>.+)/(?P<tmp_token_key>.+)/(?P<tmp_token_secret>.+)/(?P<verifier>.+)/(?P<token_key>.+)/(?P<token_secret>.+)", OAuthAccessTokenHandler),
            (r"/oauth/(?P<version>.+)/protected_resource/(?P<consumer_secret>.+)/(?P<token_secret>.+)", OAuthProtectedResourceHandler)]

        settings = dict(
            site_title="HTTP Request & Response service",
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
        output_json = utf8(tornado.escape.json_encode(data))
        # self.set_header("Content-Type", "application/json")
        if finish is True:
            self.finish(output_json)
        else:
            return output_json

    def get_data(self):
        data = {}
        data['args'] = dict([(k, v) for k, v in self.request.arguments.items()])
        data['headers'] = dict([(k, v) for k, v in self.request.headers.items()])
        data['ip'] = self.request.headers.get(
            "X-Real-Ip", self.request.headers.get(
                "X-RealI-IP",
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


class HomeHandler(CustomHandler):
    """Show home page
    """

    def get(self):
        endpoints = []

        replace_map = (
            ("(?P<status_code>\d{3})", "{status_code: int}", str(choice(list(responses.keys())))),
            ("(?P<name>.+)", "{name: str}", "test_name"),
            ("(?P<value>.+)", "{value: str}", "test_value"),
            ("(?P<num>\d{1,2})", "{redirects_num: int}", '4'),
            ("(?P<username>.+)", "{username: str}", "test_username"),
            ("(?P<password>.+)", "{password: str}", "test_password"),
            ("(?P<qop>.+)", "{quality of protection: auth | auth-int}", "auth"),
            ("(?P<version>.+)", "{version: float}", "1.0"),
            ("(?P<consumer_key>.+)", "{consumer_key: str}", random_string(15)),
            ("(?P<consumer_secret>.+)", "{consumer_secret: str}", random_string(15)),
            ("(?P<pin>.+)", "{pin: str}", random_string(10)),
            ("(?P<verifier>.+)", "{pin: str}", random_string(10)),
            ("(?P<token_key>.+)", "{token_key: str}", random_string(10)),
            ("(?P<token_secret>.+)", "{token_secret: str}", random_string(10)),
            ("(?P<tmp_token_key>.+)", "{tmp_token_key: str}", random_string(10)),
            ("(?P<tmp_token_secret>.+)", "{tmp_token_secret: str}", random_string(10)),
#            ("(?<consumer_secret>.+)", "{consumer_secret: str}", random_string(15)),
            )

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


class RobotsResourceHandler(CustomHandler):
    """Robots.txt file
    """

    def get(self):
        self.set_header("Content-Type", "text/plain")
        self.render("robots.txt")

class HumansResourceHandler(CustomHandler):
    """Humans.txt file
    """
    def get(self):
        self.set_header("Content-Type", "text/plain")
        self.render("humans.txt")


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
                except Exception:
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
        except Exception:
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
                except Exception:
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

        except Exception:
            print(sys.exc_info()[1])
            self._request_auth(qop)


def normalize_url(url):
    if url is not None:
        scheme, netloc, path, params, query, fragment = urlparse.urlparse(url)

        # Exclude default port numbers.
        if scheme == 'http' and netloc[-3:] == ':80':
            netloc = netloc[:-3]
        elif scheme == 'https' and netloc[-4:] == ':443':
            netloc = netloc[:-4]
        if scheme not in ('http', 'https'):
            raise ValueError("Unsupported URL %s (%s)." % (url, scheme))

        # Normalized URL excludes params, query, and fragment.
        return  urlparse.urlunparse((scheme, netloc, path, None, None, None))
    else:
        return None


def normalize_parameters(url):
    """Normalize url parameters

    The parameters collected in Section 3.4.1.3 are normalized into a
    single string as follow: http://tools.ietf.org/html/rfc5849#section-3.4.1.3.2
    """
    items = []
    # Include any query string parameters from the provided URL
    query = urlparse.urlparse(url)[4]
    parameters = parse_qs(utf8(query), keep_blank_values=True)
    for k, v in parameters.iteritems():
        parameters[k] = unquote(v[0])
    url_items = parameters.items()
    url_items = [(utf8(k), utf8(v)) for k, v in url_items if k != 'oauth_signature']
    items.extend(url_items)

    items.sort()
    encoded_str = urlencode(items)
    # Encode signature parameters per Oauth Core 1.0 protocol
    # spec draft 7, section 3.6
    # (http://tools.ietf.org/html/draft-hammer-oauth-07#section-3.6)
    # Spaces must be encoded with "%20" instead of "+"
    return encoded_str.replace('+', '%20').replace('%7E', '~')


def url_escape(value):
    """Returns a valid URL-encoded version of the given value."""
    """Escape a URL including any /."""
    return quote(value.encode('utf-8'), safe='~')


class SignatureMethod(object):
    """A way of signing requests.

    The OAuth protocol lets consumers and service providers pick a way to sign
    requests. This interface shows the methods expected by the other `oauth`
    modules for signing requests. Subclass it and implement its methods to
    provide a new way to sign requests.
    """

    def signing_base(self, request, consumer_secret, token_secret):
        """Calculates the string that needs to be signed.

        This method returns a 2-tuple containing the starting key for the
        signing and the message to be signed. The latter may be used in error
        messages to help clients debug their software.

        """
        raise NotImplementedError

    def sign(self, request, consumer_secret, token_secret):
        """Returns the signature for the given request, based on the consumer
        and token_secret also provided.

        You should use your implementation of `signing_base()` to build the
        message to sign. Otherwise it may be less useful for debugging.

        """
        raise NotImplementedError

    def check(self, request, consumer_secret, token_secret, signature):
        """Returns whether the given signature is the correct signature for
        the given consumer and token signing the given request."""
        built = self.sign(request, consumer_secret, token_secret)
        return built == signature


class SignatureMethod_HMAC_SHA1(SignatureMethod):
    name = 'HMAC-SHA1'

    def signing_base(self, request, consumer_secret, token_secret=None):
        if not request.get('normalized_url') or request.get('method') is None:
            raise ValueError("Base URL for request is not set.")

        sig = (
            url_escape(request['method']),
            url_escape(request['normalized_url']),
            url_escape(request['normalized_parameters']),
        )

        key = '%s&' % url_escape(consumer_secret)
        if token_secret:
            key += url_escape(token_secret)

        raw = '&'.join(sig)
        return key, raw

    def sign(self, request, consumer_secret, token_secret=None):
        """Builds the base signature string.
        """
        key, raw = self.signing_base(request, consumer_secret, token_secret)

        hashed = hmac.new(key, raw, sha)

        # Calculate the digest base 64.
        return binascii.b2a_base64(hashed.digest())[:-1]


class SignatureMethod_PLAINTEXT(SignatureMethod):
    """OAuth PLAINTEXT signature

    oauth_signature is set to the concatenated encoded values
    of the Consumer Secret and Token Secret, separated by a ‘&’ character
    (ASCII code 38), even if either secret is empty. The result MUST be encoded again.
    """

    name = 'PLAINTEXT'

    def signing_base(self, request, consumer_secret, token_secret):
        """Concatenates the consumer key and secret with the token's secret.
        """

        sig = '%s&' % url_escape(consumer_secret)
        if token_secret:
            sig = sig + url_escape(token_secret)
        return sig, sig

    def sign(self, request, consumer_secret, token_secret):
        key, raw = self.signing_base(request, consumer_secret, token_secret)
        return url_escape(raw)


SIGNATURES_METHODS = {
    # 'RSA-SHA1': SignatureMethod_RSA_SHA1
    'HMAC-SHA1': SignatureMethod_HMAC_SHA1,
    'PLAINTEXT': SignatureMethod_PLAINTEXT}


class OAuthBaseHandler(CustomHandler):
    """Base oauth handler with specified methods
    """
    REQUIRED_FIELDS = ('oauth_consumer_key', 'oauth_nonce', 'oauth_signature',
                       'oauth_signature_method', 'oauth_timestamp')
    TIMESTAMP_TRESHOLD = 300
    VERSIONS = ('1.0', '2.0')

    def _check_timestamp(self, timestamp):
        """Verify that timestamp is recentish.
        """
        timestamp = int(timestamp)
        now = int(time.time())
        lapsed = now - timestamp
        if lapsed > self.TIMESTAMP_TRESHOLD:
            self.set_status(401)
            self.finish('Expired timestamp: given %d and now %s has a ' \
                        'greater difference than threshold %d' % (timestamp, int(time.time()),
                    self.TIMESTAMP_TRESHOLD))
            return False
        return True

    def _request_auth(self):
        """Response no authentication header

        WWW-Authenticate: OAuth realm="Fake Realm"
        """
        self.set_header("WWW-Authenticate", WWWAuthentication('OAuth',
                                                              {'realm': 'Fake Realm'}).to_header())
        self.set_status(401)
        self.finish()
        return False

    def get_authorization(self):
        auth = self.request.headers.get("Authorization")
        if auth:
            authorization = Authorization.from_string(auth)
            for k in self.REQUIRED_FIELDS:
                if k not in authorization.keys():
                    self._request_auth()
                    self.finish()
        else:
            d = {}
            for k in self.REQUIRED_FIELDS:
                if k not in self.request.arguments.keys():
                    self._request_auth()
                    self.finish()
                d[k] = self.request.arguments.get(k)[0]
            authorization = Authorization('OAuth', d)

        return authorization

    def _check_signature(self, authorization, consumer_secret, token_secret=None):
        signature_method = SIGNATURES_METHODS.get(authorization['oauth_signature_method'], 'PLAINTEXT')
        if not signature_method:
            self.set_status(404)
            self.finish()

        request_info = {
            'method': self.request.method,
            'normalized_url': normalize_url(self.request.full_url()),
            'normalized_parameters': normalize_parameters(self.request.full_url()),
            }

        if not signature_method().check(request_info, consumer_secret, token_secret, authorization['oauth_signature']):
            self.set_status(403)
            self.finish({"success": False,
                     'tagline': str(choice(taglines)),
                     'signature_string': signature_method().signing_base(request_info, consumer_secret, token_secret)[1],
                         'signature_hash': signature_method().sign(request_info, consumer_secret, token_secret)})
            return False
        return True


class OAuthRequestTokenHandler(OAuthBaseHandler):
    """OAuth request token
    """

    def get(self, version, consumer_key, consumer_secret, token_key, token_secret):
        if version not in self.VERSIONS:
            raise HTTPError(400)

        authorization = self.get_authorization()
        if not authorization:
            raise HTTPError(400)

        self._check_timestamp(authorization.get('oauth_timestamp'))
        if self._check_signature(authorization, consumer_secret):
            self.finish(urlencode({
                "oauth_token": token_key,
                "oauth_token_secret": token_secret}))

    def post(self, version, consumer_key, consumer_secret, token_key, token_secret):
        return self.get(version, consumer_key, consumer_secret, token_key, token_secret)


class OAuthAuthorizeHandler(OAuthBaseHandler):
    """OAuth authorize handler
    """

    def get(self, version, pin):
        try:
            oauth_token = self.request.arguments.get('oauth_token')[0]
        except (IndexError, TypeError):
            self.set_status(500)
            self.finish("oauth token required")
        else:
            self.json_response({'verifier': pin})


class OAuthAccessTokenHandler(OAuthBaseHandler):
    """OAuth access token handler
    """

    def get(self, version, consumer_key, consumer_secret, tmp_token_key, tmp_token_secret,
            verifier, token_key, token_secret):
        if version not in self.VERSIONS:
            raise HTTPError(400)

        authorization = self.get_authorization()
        self._check_timestamp(authorization.get('oauth_timestamp'))

        if self._check_signature(authorization, str(consumer_secret), str(tmp_token_secret)):
            # token and token_secret for protected sources
            self.finish(urlencode({
                "oauth_token": token_key,
                "oauth_token_secret": token_secret}))

    def post(self, version, consumer_key, consumer_secret, tmp_token_key, tmp_token_secret,
             verifier, token_key, token_secret):
        self.get(version, consumer_key, consumer_secret, tmp_token_key, tmp_token_secret, verifier,
                 token_key, token_secret)


class OAuthProtectedResourceHandler(OAuthBaseHandler):
    """OAuth protected resource handler
    """

    def get(self, version, consumer_secret, token_secret):
        if version not in self.VERSIONS:
            raise HTTPError(400)
        authorization = self.get_authorization()

        self._check_timestamp(authorization.get('oauth_timestamp'))
        if self._check_signature(authorization, consumer_secret, token_secret):
            # token and token_secret for protected sources
            data = self.get_data()
            data['success'] = True
            self.finish(data)

    def post(self):
        return self.get()


class METHODHandler(CustomHandler):
    """Base class for methods handlers
    """
    pass


class GZipHandler(METHODHandler):
    """Returns Gziped response
    """

    def get(self):
        from gzip import GzipFile

        data = self.get_data()
        data['gzipped'] = True
        json_response = self.json_response(data, finish=False)

        tmp_buffer = BytesIO()

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

    certfile = rel("server.crt")
    keyfile = rel("server.key")

    if os.path.exists(certfile) and os.path.exists(keyfile):
        https_server = httpserver.HTTPServer(application, ssl_options={
            "certfile": certfile,
            "keyfile": keyfile})
        https_server.listen(options.ssl_port)

    http_server.listen(options.port)
    ioloop = tornado.ioloop.IOLoop.instance()
    autoreload.start(io_loop=ioloop, check_time=100)
    ioloop.start()
