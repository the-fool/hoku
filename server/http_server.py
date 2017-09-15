import http
import logging
import socketserver

socketserver.TCPServer.allow_reuse_address = True


class HttpHandler(http.server.SimpleHTTPRequestHandler):
    pass


def run_http_server(port=5555):
    httpd = socketserver.TCPServer(("0.0.0.0", port), HttpHandler)
    logging.debug("serving at port {}".format(port))
    httpd.serve_forever()
