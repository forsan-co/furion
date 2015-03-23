from socks5 import Socks5Client
import SocketServer
import struct
# from helpers import hexstring


# http://code.activestate.com/recipes/491264-mini-fake-dns-server/
class DNSQuery:
    def __init__(self, data):
        self.data = data
        self.domain = ''

        tipo = (ord(data[2]) >> 3) & 15  # Opcode bits
        if tipo == 0:  # Standard query
            ini = 12
            lon = ord(data[ini])
            while lon != 0:
                self.domain += data[ini + 1:ini + lon + 1] + '.'
                ini += lon + 1
                lon = ord(data[ini])

    def response(self, ip):
        if self.domain:
            packet = self.data[:2] + "\x81\x80"
            packet += self.data[4:6] + self.data[4:6] + '\x00\x00\x00\x00'  # Questions and Answers Counts
            packet += self.data[12:]  # Original Domain Name Question
            packet += '\xc0\x0c'  # Pointer to domain name
            packet += '\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04' # Response type, ttl and resource data length -> 4bytes
            packet += str.join('', map(lambda x: chr(int(x)), ip.split('.')))  # 4bytes of IP
        return packet


class DNSProxyHandler(SocketServer.BaseRequestHandler):
    """UDP DNS Proxy handler"""
    def handle(self):
        data = self.request[0].strip()
        sock = self.request[1]

        sc = Socks5Client(self.local_addr, data=(self.dns_server, 53), enable_ssl=False)
        server = sc.connect()
        server.sendall(struct.pack('!H', len(data)) + data)
        result = server.recv(65535)
        server.close()
        sock.sendto(result[2:], self.client_address)


class DNSQueryHandler(SocketServer.BaseRequestHandler):
    """UDP DNS Request handler"""
    def handle(self):
        data = self.request[0].strip()
        sock = self.request[1]

        query = DNSQuery(data)
        sc = Socks5Client(self.upstream_addr, username=self.upstream_username, password=self.upstream_password,
                          data=(query.domain, 0), dns_only=True)
        ip = sc.connect()
        sock.sendto(query.response(ip), self.client_address)