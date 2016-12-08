#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author:End1ng

import socket

import tornado.httpclient
import tornado.httpserver
import tornado.ioloop
import tornado.web
from urlparse import urlparse
from tornado.options import define, options, parse_command_line

class ProxyHandler(tornado.web.RequestHandler):

    @tornado.web.asynchronous
    def get(self):
        try:
            req = tornado.httpclient.HTTPRequest(
                    self.request.uri,
                    method=self.request.method,
                    body=self.request.body if self.request.body else None,
                    headers=self.request.headers,
                    request_timeout=5,
                    follow_redirects=True,
                    allow_nonstandard_methods=True)
            asy_client = tornado.httpclient.AsyncHTTPClient()
            asy_client.fetch(req, self.on_response)

        except tornado.httpclient.HTTPError as httperror:
            self.set_status(500)
            self.write(str(response.error))
            self.finish()

    def on_response(self, response):

        if response.error:
            self.set_status(500)
            self.write(str(response.error))
            self.finish()
        else:

            content_type = response.headers.get_list('content-type')
            headers = self._headers.keys()
            cookies = response.headers.get_list('Set-Cookie')

            self.set_status(response.code)
            for header in headers:
                value = response.headers.get(header)
                if value:
                    self.set_header(header, value)
            if cookies:
                for i in cookies:
                    self.add_header('Set-Cookie', i)
            try:
                if response.code != 304:
                    self.write(response.body)
            except:
                pass
            self.finish()

    @tornado.web.asynchronous
    def post(self):
        self.get()

    # copy from internet
    @tornado.web.asynchronous
    def connect(self):
        req_stream = self.request.connection.stream

        host, port = self.request.uri.split(':')
        port = int(port)

        def req_close(data=None):
            if conn_stream.closed():
                return
            if data:
                conn_stream.write(data)
            conn_stream.close()

        def write_to_server(data):
            conn_stream.write(data)

        def proxy_close(data=None):
            if req_stream.closed():
                return
            if data:
                req_stream.write(data)
            req_stream.close(data)

        def write_to_client(data):
            req_stream.write(data)

        def on_connect():
            req_stream.read_until_close(req_close, write_to_server)
            conn_stream.read_until_close(proxy_close, write_to_client)
            req_stream.write(b'HTTP/1.0 200 Connection established\r\n\r\n')

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        conn_stream = tornado.iostream.IOStream(s)
        conn_stream.connect((host, port), on_connect)

if __name__ == '__main__':
    define("port", default=8888, help="port", type=int)
    define("debug", default=False, help="debug", type=bool)

    tornado.options.parse_command_line()

    print "Starting Proxy on port %s" % (options.port)

    handlers = [
        (r'.*', ProxyHandler),
    ]

    app = tornado.web.Application(handlers=handlers,debug=options.debug)
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()