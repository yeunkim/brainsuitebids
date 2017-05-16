from __future__ import print_function
import sys
import os
try:
    import SimpleHTTPServer
except ImportError:
    import http.server as SimpleHTTPServer

try:
    import SocketServer
except ImportError:
    import socketserver as SocketServer

#No handling of bad arguments; will be called in shell script with proper public directory arg
os.chdir(sys.argv[1])

PORT = 8080
Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
SocketServer.TCPServer.allow_reuse_address = True # Allow reuse of port after ^C
server = SocketServer.TCPServer(("", PORT), Handler)

print("Web server serving: " + os.path.abspath(sys.argv[1]))

try:
    server.serve_forever()
except:
    print("Web server shutting down")
    server.shutdown()
    server.server_close()
    exit(0)


