#!/usr/bin/env python
# -*- coding:  utf-8 -*-

"""
httphq.utils
~~~~~~~~~~~~

Helpers for handlers

:copyright: (c) 2011 - 2013 by Alexandr Lispython (alex@obout.ru).
:license: BSD, see LICENSE for more details.
:github: http://github.com/Lispython/httphq
"""
import sys

try:
    from urllib2 import parse_http_list
except ImportError:
    from urllib.request import parse_http_list

from hashlib import md5
from tornado.escape import utf8


def parse_dict_header(value):
    """Parse key=value pairs from value list
    """
    result = {}
    for item in parse_http_list(value):
        if "=" not in item:
            result[item] = None
            continue
        name, value = item.split('=', 1)
        if value[:1] == value[-1:] == '"':
            value = value[1:-1] # strip "
        result[name] = value
    return result


def parse_authorization_header(header):
    """Parse authorization header and build Authorization object

    Authorization: Digest username="Mufasa",
                 realm="testrealm@host.com",
                 nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093",
                 uri="/dir/index.html",
                 qop=auth, # not required
                 nc=00000001, # required if qop is auth or auth-int
                 cnonce="0a4f113b", # required if qop is auth or auth-int
                 response="6629fae49393a05397450978507c4ef1",
                 opaque="5ccc069c403ebaf9f0171e9517f40e41"
    """
    if not header:
        return
    try:
        auth_type, auth_info = header.split(None, 1) # separate auth type and values
        auth_type = auth_type.lower()
    except ValueError:
        print(sys.exc_info()[0])
        return

    if auth_type == 'basic':
        try:
            username, password = auth_info.decode('base64').split(':', 1)
        except Exception:
            return
        return Authorization('basic', {'username': username,
                                       'password': password})
    elif auth_type == 'digest':
        auth_map = parse_dict_header(auth_info)

        required_map = {
            'auth': ("username", "realm", "nonce", "uri", "response", "opaque"),
            'auth-int': ("realm", "nonce", "uri", "qop", "nc", "cnonce", "response", "opaque")}
        required = required_map.get(auth_map.get('qop', 'auth'))

        for key in required:
            if not key in auth_map:
                return
        return Authorization('digest', auth_map)
    elif auth_type == 'oauth':
        auth_map = parse_dict_header(auth_info)
        return Authorization('OAuth', auth_map)
    else:
        raise ValueError("Unknown auth type %s" % auth_type)


def parse_authenticate_header(header):
    """Parse WWW-Authenticate response header

    WWW-Authenticate: Digest
                 realm="testrealm@host.com",
                 qop="auth,auth-int",
                 nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093",
                 opaque="5ccc069c403ebaf9f0171e9517f40e41"
    """
    if not header:
        return
    try:
        auth_type, auth_info = header.split(None, 1)
        auth_type = auth_type.lower()
    except ValueError:
        print(sys.exc_info()[0])
        return
    return WWWAuthentication(auth_type, parse_dict_header(auth_info))


class WWWAuthentication(dict):
    """WWWAuthentication header object
    """

    AUTH_TYPES = ("Digest", "Basic", "OAuth")

    def __init__(self, auth_type='basic', data=None):
        if auth_type.lower() not in [t.lower() for t in self.AUTH_TYPES]:
            raise RuntimeError("Unsupported auth type: %s" % auth_type)
        dict.__init__(self, data or {})
        self._auth_type = auth_type

    @staticmethod
    def from_string(value):
        """Build Authenticate object from header value

        - `value`: Authorization field value
        """
        return parse_authenticate_header(value)

    def to_header(self):
        """Convert values into WWW-Authenticate header value
        """
        d = dict(self)
        return "%s %s" % (self._auth_type.title(), ", ".join("%s=\"%s\"" % (k, v)
                                                             for k, v in d.items()))


class Authorization(dict):
    """Authorization header object
    """

    AUTH_TYPES = ("Digest", "Basic", "OAuth")

    def __init__(self, auth_type='basic', data=None):
        if auth_type.lower() not in [t.lower() for t in self.AUTH_TYPES]:
            raise RuntimeError("Unsupported auth type: %s" % auth_type)
        dict.__init__(self, data or {})
        self._auth_type = auth_type

    @staticmethod
    def from_string(value):
        """Build Authorization object from header value

        - `value`: Authorization field value
        """
        return parse_authorization_header(value)

    def to_header(self):
        """Convert values into WWW-Authenticate header value
        """
        d = dict(self)
        return "%s %s" % (self._auth_type.title(), ", ".join("%s=\"%s\"" % (k, v)
                                                             for k, v in d.items()))


    # Digest auth properties http://tools.ietf.org/html/rfc2069#page-4

    realm = property(lambda x: x.get('realm'), doc="""
    A string to be displayed to users so they know which username and
    password to use.  This string should contain at least the name of
    the host performing the authentication and might additionally
    indicate the collection of users who might have access.  An example
    might be "registered_users@gotham.news.com".  The realm is a
    "quoted-string" as specified in section 2.2 of the HTTP/1.1
    specification.""")

    domain = property(lambda x: x.get('domain'), doc="""domain
    A comma-separated list of URIs, as specified for HTTP/1.0.  The
    intent is that the client could use this information to know the
    set of URIs for which the same authentication information should be
    sent.  The URIs in this list may exist on different servers.  If
    this keyword is omitted or empty, the client should assume that the
    domain consists of all URIs on the responding server.""")

    nonce = property(lambda x: x.get('nonce'))
    opaque = property(lambda x: x.get('opaque'))
    username = property(lambda x: x.get('username'))
    password = property(lambda x: x.get('password'))
    uri = property(lambda x: x.get('uri'))
    qop = property(lambda x: x.get('qop'))
    cnonce = property(lambda x: x.get('cnonce'))
    responce = property(lambda x: x.get('responce'))
    nc = property(lambda x: x.get('nc'))
    stale = property(lambda x: x.get('stale'))
    algorithm = property(lambda x: x.get('alghoritm'))


# Digest auth helpers
# qop is a quality of protection

def H(data):
    return md5(utf8(data)).hexdigest()


def HA1(realm, username, password):
    """Create HA1 hash by realm, username, password

    HA1 = md5(A1) = MD5(username:realm:password)
    """
    return H("%s:%s:%s" % (username,
                           realm,
                           password))


def HA2(credentails, request):
    """Create HA2 md5 hash

    If the qop directive's value is "auth" or is unspecified, then HA2:
        HA2 = md5(A2) = MD5(method:digestURI)
    If the qop directive's value is "auth-int" , then HA2 is
        HA2 = md5(A2) = MD5(method:digestURI:MD5(entityBody))
    """
    if credentails.get("qop") == "auth" or credentails.get('qop') is None:
        return H("%s:%s" % (request['method'], request['uri']))
    elif credentails.get("qop") == "auth-int":
        for k in 'method', 'uri', 'body':
            if k not in request:
                raise ValueError("%s required" % k)
        return H("%s:%s:%s" % (request['method'],
                               request['uri'],
                               H(request['body'])))
    raise ValueError


def response(credentails, password, request):
    """Compile digest auth response

    If the qop directive's value is "auth" or "auth-int" , then compute the response as follows:
       RESPONSE = MD5(HA1:nonce:nonceCount:clienNonce:qop:HA2)
    Else if the qop directive is unspecified, then compute the response as follows:
       RESPONSE = MD5(HA1:nonce:HA2)

    Arguments:
    - `credentails`: credentails dict
    - `password`: request user password
    - `request`: request dict
    """
    response = None
    HA1_value = HA1(credentails.get('realm'), credentails.get('username'), password)
    HA2_value = HA2(credentails, request)
    if credentails.get('qop') is None:
        response = H(":".join([HA1_value, credentails.get('nonce'), HA2_value]))
    elif credentails.get('qop') == 'auth' or credentails.get('qop') == 'auth-int':
        for k in 'nonce', 'nc', 'cnonce', 'qop':
            if k not in credentails:
                raise ValueError("%s required for response H" % k)
        response = H(":".join([HA1_value,
                               credentails.get('nonce'),
                               credentails.get('nc'),
                               credentails.get('cnonce'),
                               credentails.get('qop'),
                               HA2_value]))
    else:
        raise ValueError("qop value are wrong")

    return response
