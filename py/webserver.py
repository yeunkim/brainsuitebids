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
if len(sys.argv) != 2:
    print("Usage: python webserver.py <directory_to_server>")
    print("Error: expected 1 argument, got %d" % (len(sys.argv) - 1))
    exit(1)

os.chdir(sys.argv[1])
PORT = 8080
Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
SocketServer.TCPServer.allow_reuse_address = True # Allow reuse of port after ^C

server = None
while True:
    try:
        server = SocketServer.TCPServer(("", PORT), Handler)
        break
    except:
        PORT = PORT + 1


print("==============================")
print("Web server serving: %s on port %d" % (os.path.abspath(sys.argv[1]), PORT))
import socket
tempSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
tempSocket.connect(("8.8.8.8", 80))
IP = tempSocket.getsockname()[0]
tempSocket.close()
print("To view web interface, navigate to: %s:%d" %(IP, PORT))
print("Note: Check IP address configuration if program is being run from a VM or a Docker Container.")
print("==============================")

try:
    server.serve_forever()

except:
    print("Web server shutting down")
    server.shutdown()
    server.server_close()
    exit(0)


