from simplesockets.simplesockets import TCPServer, TCPClient
from simplesockets.securesocket import TCPServer_secure, TCPClient_secure
import socket
import traceback

class TCPClient_ipv6(TCPClient):
    def __init__(self):
        super().__init__()
        super().socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
        self.__target_info = None

    def setup(self, target_info = ("localhost", 9999, 0, 0), recv_buffer=2048):
        self.__target_info = target_info
        super().__recv_buffer = recv_buffer

    def connect(self):
        try:
            super().socket.connect(self.__target_info)
            super().is_connected = True
            return True
        except Exception as e:
            super().__all_exceptions.append((traceback.format_exc(), e))
            super().exception = True
            return False

    def reconnect(self):
        super().socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
        self.connect()

class TCPServer_ipv6(TCPServer):
    def __init__(self, max_connections):
        super().__init__(max_connections)
        super().socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
        self.__target_info = None

    def setup(self, target_info = ("::1", 9999, 0, 0), listen=5, recv_buffer=2048, handle_client=None):
        self.__target_info = target_info
        if handle_client is not None:
            super().__start_target = handle_client
        else:
            super().__start_target = super().__handle_client

        super().__recv_buffer = recv_buffer

        super().socket.bind(self.__target_info)
        super().socket.listen(listen)
        super().__accepting_thread.start()

class TCPClient_secure_ipv6(TCPClient_secure):
    def __init__(self):
        pass