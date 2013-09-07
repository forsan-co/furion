import ssl
import socket
import SocketServer
import threading
from Queue import Queue

TIME_OUT = 30
POOL_SIZE = 50

class ThreadPoolMixIn(SocketServer.ThreadingMixIn):
    """Thread pool mixin"""

    def serve_forever(self, pool_size=POOL_SIZE):
        self.requests = Queue(pool_size)

        for x in range(pool_size):
            t = threading.Thread(target = self.process_request_thread)
            t.setDaemon(1)
            t.start()

        while True:
            self.handle_request()

        self.server_close()

    def process_request_thread(self):
        while True:
            SocketServer.ThreadingMixIn.process_request_thread(self, *self.requests.get())

    def handle_request(self):
        try:
            request, client_address = self.get_request()
        except socket.error:
            return
        if self.verify_request(request, client_address):
            self.requests.put((request, client_address))

class SecureTCPServer(SocketServer.TCPServer):
    """TCP server with SSL"""
    
    allow_reuse_address = True

    def __init__(self, pem_path, server_address, handler_class):
        SocketServer.BaseServer.__init__(self, server_address, handler_class)

        af, socktype, proto, canonname, sa = socket.getaddrinfo(
            self.server_address[0], self.server_address[1], 0, socket.SOCK_STREAM)[0]
        sock = socket.socket(af, socktype, proto)
        #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIME_OUT)

        # Don't do handshake on connect for ssl (which will block http://bugs.python.org/issue1251)
        self.socket = ssl.wrap_socket(sock, pem_path, pem_path, server_side=True, do_handshake_on_connect=False)
        self.server_bind()
        self.server_activate()


class Socks5Server(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    """Threading Socks5 server"""
    allow_reuse_address = True

class TPSocks5Server(ThreadPoolMixIn, SocketServer.TCPServer):
    """Thread Pool Socks5 server"""
    pass
    
class SecureSocks5Server(SocketServer.ThreadingMixIn, SecureTCPServer):
    """Secure Socks5 server"""
    pass

class TPSecureSocks5Server(ThreadPoolMixIn, SecureTCPServer):
    """Thread Pool Secure Socks5 server"""
    pass
    

class PingServer(ThreadPoolMixIn, SocketServer.UDPServer):
    """UDP Ping server"""
    pass

# Test server
# svr = PingServer(('0.0.0.0', 8888), PingHandler)
# svr.serve_forever(5)

