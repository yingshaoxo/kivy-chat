import socket
import asyncore

connected_sockets = dict()

class SocketHandler(asyncore.dispatcher_with_send):

    def handle_read(self):
        data = self.recv(8192)
        #print(connected_sockets)
        if data:
            print(data)
            for i in [i for i in connected_sockets.values() if i != self.socket]:
                i.send(data)
            print(len(connected_sockets.keys()))

    def handle_close(self):
        del connected_sockets[self.addr]
        self.close()

class SocketServer(asyncore.dispatcher):

    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

    def handle_accepted(self, sock, addr):
        #print('Incoming connection from %s' % repr(addr))
        connected_sockets.update({addr: sock})
        handler = SocketHandler(sock)

socket_server = SocketServer('0.0.0.0', 5920)

asyncore.loop()
