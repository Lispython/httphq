#!/usr/bin/env python
# -*- coding:  utf-8 -*-


import unittest
from httphq.utils import (parse_dict_header, parse_authorization_header,
                          parse_authenticate_header, Authorization, WWWAuthentication,
                          H, HA1, HA2, response)

class UtilsTestCase(unittest.TestCase):
    def setUp(self):
        self.authorization_value = 'Digest username="Mufasa", '\
                                   'realm="testrealm@host.com", '\
                                   'nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093", '\
                                   'uri="/dir/index.html", ' \
                                   'response="e966c932a9242554e42c8ee200cec7f6", '\
                                   'nc="00000001", ' \
                                   'cnonce="0a4f113b", ' \
                                   'opaque="5ccc069c403ebaf9f0171e9517f40e41"'


        self.www_authenticate_value = 'Digest realm="testrealm@host.com", '\
                                       'nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093", '\
                                       'opaque="5ccc069c403ebaf9f0171e9517f40e41"'

    def test_parse_authorization_header(self):
        control = dict((('username', "Mufasa"),
                        ('realm', "testrealm@host.com"),
                        ('nonce', "dcd98b7102dd2f0e8b11d0f600bfb0c093"),
                        ('uri', "/dir/index.html"),
                        ('nc', '00000001'),
                        ('cnonce', "0a4f113b"),
                        ('response', "e966c932a9242554e42c8ee200cec7f6"),
                        ('opaque', "5ccc069c403ebaf9f0171e9517f40e41")))


        parsed_authorization_header = parse_authorization_header(self.authorization_value)

        self.assertTrue(isinstance(parsed_authorization_header, Authorization))
        self.assertEqual(parsed_authorization_header._auth_type.lower(), 'digest')
        for k, v in control.items():
            self.assertEqual(parsed_authorization_header[k], v)

        parsed_authorization_header2 = Authorization.from_string(self.authorization_value)

        self.assertTrue(isinstance(parsed_authorization_header2, Authorization))
        self.assertEqual(parsed_authorization_header2._auth_type.lower(), 'digest')
        for k, v in control.items():
            self.assertEqual(parsed_authorization_header2[k], v)

        compiled_header_value = parsed_authorization_header.to_header()
        for k, v in control.items():
            self.assertTrue('%s="%s"' % (k, v) in compiled_header_value)


    def test_parse_authenticate_value(self):
        control = dict((('realm', "testrealm@host.com"),
                       ('nonce', "dcd98b7102dd2f0e8b11d0f600bfb0c093"),
                       ('opaque', "5ccc069c403ebaf9f0171e9517f40e41")))

        parsed_authenticate = parse_authenticate_header(self.www_authenticate_value)

        self.assertTrue(isinstance(parsed_authenticate, WWWAuthentication))
        self.assertEqual(parsed_authenticate._auth_type.lower(), 'digest')
        for k, v in control.items():
            self.assertEqual(parsed_authenticate[k], v)

        parsed_authenticate2 = WWWAuthentication.from_string(self.www_authenticate_value)

        self.assertTrue(isinstance(parsed_authenticate2, WWWAuthentication))
        self.assertEqual(parsed_authenticate2._auth_type.lower(), 'digest')
        for k, v in control.items():
            self.assertEqual(parsed_authenticate2[k], v)

        compiled_header_value = parsed_authenticate.to_header()
        for k, v in control.items():
            self.assertTrue('%s="%s"' % (k, v) in compiled_header_value)


    def test_parse_dict_header(self):
        value = 'username="Mufasa", '\
                'realm="testrealm@host.com", '\
                'nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093", '\
                'uri="/dir/index.html",' \
                'response="e966c932a9242554e42c8ee200cec7f6", '\
                'opaque="5ccc069c403ebaf9f0171e9517f40e41"'
        control = dict((
            ('username', "Mufasa"),
            ('realm', "testrealm@host.com"),
            ('nonce', "dcd98b7102dd2f0e8b11d0f600bfb0c093"),
            ('uri', "/dir/index.html"),
            ('response', "e966c932a9242554e42c8ee200cec7f6"),
            ('opaque', "5ccc069c403ebaf9f0171e9517f40e41")))

        for k, v in parse_dict_header(value).items():
            self.assertEqual(v, control[k])

    def test_Hx(self):
        cr = {'username': 'test_username',
              'password': 'test_password',
              'realm': 'Fake area',
              'nonce': "dcd98b7102dd2f0e8b11d0f600bfb0c093",
              'uri': "/dir/index.html",
              'nc': '00000001',
              'cnonce': "0a4f113b",
              'response': "e966c932a9242554e42c8ee200cec7f6",
              'opaque': "5ccc069c403ebaf9f0171e9517f40e41"}

        request = {'method': 'GET',
                   'uri': '/dir/index.html',
                   'body': 'request body'}
        self.assertEqual(HA1(cr['realm'], cr['username'], cr['password']),
                          H("%s:%s:%s" % (cr['username'], cr['realm'], cr['password'])))

        # test qop == auth
        cr['qop'] = 'auth'
        self.assertEqual(HA2(cr, request), H("%s:%s" % (request['method'], request['uri'])))

        # test qop == auth-int
        cr['qop'] = 'auth-int'
        self.assertEqual(HA2(cr, request), H("%s:%s:%s" % (request['method'], request['uri'], H(request['body']))))

        # test qop == 'bad-auth'
        cr['qop'] = 'bad-auth'
        self.assertRaises(ValueError, HA2, cr, request)


        # test qop == None
        cr['qop'] = None
        self.assertEqual(response(cr, cr['password'], request),
                          H(":".join([HA1(cr['realm'], cr['username'], cr['password']),
                                      cr.get('nonce'), HA2(cr, request)])))

        # test qop == auth
        cr['qop'] = 'auth'
        self.assertEqual(response(cr, cr['password'], request),
                          H(":".join([HA1(cr['realm'], cr['username'], cr['password']),
                                      cr.get('nonce'),
                                      cr.get('nc'),
                                      cr.get('cnonce'),
                                      cr.get('qop'),
                                      HA2(cr, request)])))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(UtilsTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest="suite")


