
HTTP Request & Response service
===============================

Simple service for testing HTTP/HTTPS requests.
All endpoint responses are JSON-encoded exclude `/status/{status_code: int} <http://h.wrttn.me/status/200>`_.
It's useful for testing how your own scripts deal with varying responses and requests.

.. image:: https://travis-ci.org/Lispython/httphq.png
	   :target: https://travis-ci.org/Lispython/httphq

INSTALLATION
------------

You can use ``easy_install`` or ``pip`` to install `httphq`:

``pip install httphq``

or

``easy_install httphq``

ENDPOINTS
---------

- `/ <http://h.wrttn.me/>`_ —  Show home page
- `/ip <http://h.wrttn.me/ip>`_ — Returns client IP and proxies
- `/get <http://h.wrttn.me/get>`_  — GET method
- `/post <http://h.wrttn.me/post>`_ — POST method
- `/put <http://h.wrttn.me/put>`_ — PUT method
- `/head <http://h.wrttn.me/head>`_ — HEAD method
- `/options <http://h.wrttn.me/options>`_ — OPTIONS method
- `/delete <http://h.wrttn.me/delete>`_ — DELETE method
- `/user-agent <http://h.wrttn.me/user-agent>`_ — Returns user agent
- `/headers <http://h.wrttn.me/headers>`_ — Returns sended headers
- `/cookies <http://h.wrttn.me/cookies>`_ — Returns all user cookies
- `/cookies/set/{name: str}/{value: str} <http://h.wrttn.me/cookies/set/test_name/test_value>`_ — Setup given name and value on client
- `/status/{status_code: int} <http://h.wrttn.me/status/403>`_ — Returns given HTTP status code
- `/basic-auth/{username: str}/{password: str} <http://h.wrttn.me/basic-auth/test_username/test_password>`_ — Basic access authentication
- `/digest-auth/{qop: auth | auth-int}/{username: str}/{password: str} <http://h.wrttn.me/digest-auth/auth/test_username/test_password>`_ — Digest access authentication


HTTP status codes
-----------------

1xx Informational
~~~~~~~~~~~~~~~~~

- `100 <http://h.wrttn.me/status/100>`_ — Continue
- `101 <http://h.wrttn.me/status/101>`_ — Switching Protocols

2xx Success
~~~~~~~~~~~
- `200 <http://h.wrttn.me/status/200>`_ — OK
- `201 <http://h.wrttn.me/status/201>`_ — Created
- `202 <http://h.wrttn.me/status/202>`_ — Accepted
- `203 <http://h.wrttn.me/status/203>`_ — Non-Authoritative Information
- `204 <http://h.wrttn.me/status/204>`_ — No Content [ Won't return a response body ]
- `205 <http://h.wrttn.me/status/205>`_ — Reset Content [ Won't return a response body ]
- `206 <http://h.wrttn.me/status/206>`_ — Partial Content

3xx Redirection
~~~~~~~~~~~~~~~
- `300 <http://h.wrttn.me/status/300>`_ — Multiple Choices
- `301 <http://h.wrttn.me/status/301>`_ — Moved Permanently [ Will also return this extra header: Location: http://http.obout.ru ]
- `302 <http://h.wrttn.me/status/302>`_ — Found [ Will also return this extra header: Location: http://h.wrttn.me ]
- `303 <http://h.wrttn.me/status/303>`_ — See Other [ Will also return this extra header: Location: http://h.wrttn.me ]
- `304 <http://h.wrttn.me/status/304>`_ — Not Modified [ Won't return a response body ]
- `305 <http://h.wrttn.me/status/305>`_ — Use Proxy [ Will also return this extra header: Location: http://h.wrttn.me ]
- `306 <http://h.wrttn.me/status/306>`_ — (Unused)
- `307 <http://h.wrttn.me/status/307>`_ — Temporary Redirect [ Will also return this extra header: Location: http://h.wrttn.me ]

4xx Client Error
~~~~~~~~~~~~~~~~

- `400 <http://h.wrttn.me/status/400>`_ — Bad Request
- `401 <http://h.wrttn.me/status/401>`_ — Unauthorized [ Will also return this extra header: WWW-Authenticate: Basic realm="Fake Realm" ]
- `402 <http://h.wrttn.me/status/402>`_ — Payment Required
- `403 <http://h.wrttn.me/status/403>`_ — Forbidden
- `404 <http://h.wrttn.me/status/404>`_ — Not Found
- `405 <http://h.wrttn.me/status/405>`_ — Method Not Allowed
- `406 <http://h.wrttn.me/status/406>`_ — Not Acceptable
- `407 <http://h.wrttn.me/status/407>`_ — Proxy Authentication Required [ Will also return this extra header: Proxy-Authenticate: Basic realm="Fake Realm" ]
- `408 <http://h.wrttn.me/status/408>`_ — Request Timeout
- `409 <http://h.wrttn.me/status/409>`_ — Conflict
- `410 <http://h.wrttn.me/status/410>`_ — Gone
- `411 <http://h.wrttn.me/status/411>`_ — Length Required
- `412 <http://h.wrttn.me/status/412>`_ — Precondition Failed
- `413 <http://h.wrttn.me/status/413>`_ — Request Entity Too Large
- `414 <http://h.wrttn.me/status/414>`_ — Request-URI Too Long
- `415 <http://h.wrttn.me/status/415>`_ — Unsupported Media Type
- `416 <http://h.wrttn.me/status/416>`_ — Requested Range Not Satisfiable
- `417 <http://h.wrttn.me/status/417>`_ — Expectation Failed


5xx Server Error
~~~~~~~~~~~~~~~~

- `500 <http://h.wrttn.me/status/500>`_ — Internal Server Error
- `501 <http://h.wrttn.me/status/501>`_ — Not Implemented
- `502 <http://h.wrttn.me/status/502>`_ — Bad Gateway
- `503 <http://h.wrttn.me/status/503>`_ — Service Unavailable
- `504 <http://h.wrttn.me/status/504>`_ — Gateway Timeout
- `505 <http://h.wrttn.me/status/505>`_ — HTTP Version Not Supported


EXAMPLES
--------

.. code-block:: text

    curl http://h.wrttn.me/get | python -mjson.tool
    {
        "args": {},
        "headers": {
            "Accept": "*/*",
            "Host": "h.wrttn.me",
    "User-Agent": "curl/7.19.7 (i486-pc-linux-gnu) libcurl/7.19.7 OpenSSL/0.9.8k zlib/1.2.3.3 libidn/1.15"
    },
    "url": " http://h.wrttn.me/get"
    }


    curl -X POST -F "name=value" http://h.wrttn.me/post | python -mjson.tool
    {
        "args": {
            "name": [
                "value"
            ]
        },
        "body": "------------------------------eb288eb3d3e4\r\nContent-Disposition: form-data; name=\"name\"\r\n\r\nvalue\r\n------------------------------eb288eb3d3e4--\r\n",
        "files": {},
        "headers": {
            "Accept": "*/*",
            "Content-Length": "144",
            "Content-Type": "multipart/form-data; boundary=----------------------------eb288eb3d3e4",
            "Expect": "100-continue",
            "Host": "h.wrttn.me",
    "User-Agent": "curl/7.19.7 (i486-pc-linux-gnu) libcurl/7.19.7 OpenSSL/0.9.8k zlib/1.2.3.3 libidn/1.15"
    },
    "ip": "127.0.0.1",
    "request_time": 0.04458308219909668,
    "start_time": 1313996082.806412,
    "url": "http://h.wrttn.me/post"
    }


    curl -X POST -F "test_files=@/tmp/testfile1.txt" -F "test_files=@/tmp/testfile2.txt" http://h.wrttn.me/post | python -mjson.tool
    {
        "args": {},
        "files": {
            "pictures": [
                {
                    "body": ";klrjewfghjnq3rjehg;fqnr___j3bnr4lgfbv4riy5bguy4br5y\n",
                    "content_type": "text/plain",
                    "filename": "testfile1.txt"
                },
                {
                    "body": ";klrlfkejwknfqwdrkjnbkfgjb3erj\n",
                    "content_type": "text/plain",
                    "filename": "testfile2.txt"
                }
            ]
        },
        "body": "",
        "headers": {
            "Accept": "*/*",
            "Content-Length": "428",
            "Content-Type": "multipart/form-data; boundary=----------------------------af3ea881bfa9",
            "Expect": "100-continue",
            "Host": "h.wrttn.me",
    "User-Agent": "curl/7.19.7 (i486-pc-linux-gnu) libcurl/7.19.7 OpenSSL/0.9.8k zlib/1.2.3.3 libidn/1.15"
    },
    "ip": "127.0.0.1",
    "request_time": 0.04804205894470215,
    "start_time": 1313953495.331477,
    "url": "http://h.wrttn.me/post"
    }


SEE ALSO
--------

`http://hurl.it <http://hurl.it/>`_, `httpbin <http://httpbin.org>`_, `postbin <http://postbin.org>`_, `ifconfig.me <http://ifconfig.me/>`_, `httpstat.us <http://httpstat.us>`_


CONTRIBUTE
----------

Fork https://github.com/Lispython/httphq/ , create commit and pull request.


THANKS
------

To `Kenneth Reitz <http://kennethreitz.com/pages/open-projects.html>`_  who develop `httpbin.org <http://httpbin.org>`_
