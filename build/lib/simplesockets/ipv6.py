from simplesockets.simple_sockets import TCPServer, TCPClient
from simplesockets.securesockets import S_Server, PyCryptodome_Socket
import socket
import traceback
import threading

class TCPClient_ipv6(TCPClient):
    def __init__(self):
        super().__init__()
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
        self.__target_info = None

    def setup(self, target_info = ("localhost", 9999, 0, 0), recv_buffer=2048, on_connect=None, on_disconnect=None,
              on_receive=None):
        self.__target_info = target_info
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_receive = on_receive
        super().__recv_buffer = recv_buffer

    def connect(self) -> bool:
        try:
            super().socket.connect(self.__target_info)
            self.event.is_connected = True
            self.event.connected = True
            if callable(self.on_connect):
                self.on_connect()
            return True
        except Exception as e:
            self.event.exception.occurred = True
            self.event.exception.list.append((traceback.format_exc(), e))
            return False

    def reconnect(self):
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
        self.event.connected = False
        self.event.disconnected = False
        return self.connect()

class TCPServer_ipv6(TCPServer):
    def __init__(self, max_connections):
        super().__init__(max_connections)
        super().socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
        self.__target_info = None

    def setup(self, target_info:tuple = ("::1", 9999, 0, 0), listen=5, recv_buffer=2048, handle_client=None,
              on_connect=None, on_disconnect=None):
        self.__target_info = target_info
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        if handle_client is not None:
            super().__start_target = handle_client
        else:
            super().__start_target = super().__handle_client

        super().__recv_buffer = recv_buffer

        self.socket.bind(self.__target_info)
        self.socket.listen(listen)
        self.__accepting_thread.start()

    def exit(self):
        def join_():
            closing_connection = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
            closing_connection.connect(self.__target_info)
            closing_connection.close()
            self.socket.close()
            self.__accepting_thread.join()
            for thread in self.__allthreads.values():
                try:
                    thread.join()
                except Exception:
                    continue

        self.__kill = True
        self.event.accepting_thread.run = False
        kill = threading.Thread(target=join_, daemon=True)
        kill.start()

class S_Client_ipv6(PyCryptodome_Socket.Client_):
    def __init__(self):
        super().__init__()
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
        self.__target_info = None

    def setup(self, target_info=("localhost", 9999, 0, 0), recv_buffer=2048, on_connect=None, on_disconnect=None,
              on_receive=None):
        if on_connect is None:
            on_connect = super().__on_connect

        self.__target_info = target_info
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_receive = on_receive
        super().__recv_buffer = recv_buffer

    def connect(self, username:str,pw:str) -> bool:
        self.user = username
        self.pw =pw
        try:
            super().socket.connect(self.__target_info)
            self.event.is_connected = True
            self.event.connected = True
            if callable(self.on_connect):
                self.on_connect()
            return True
        except Exception as e:
            self.event.exception.occurred = True
            self.event.exception.list.append((traceback.format_exc(), e))
            return False

    def reconnect(self, username, pw):
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
        self.event.connected = False
        self.event.disconnected = False
        return self.connect(username, pw)

class S_Server_ipv6(S_Server.Server_):
    def __init__(self, max_connections):
        super().__init__(max_connections)
        super().socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
        self.__target_info = None

    def setup(self, file, target_info: tuple = ("::1", 9999, 0, 0), listen=5, recv_buffer=2048, handle_client=None,
              on_connect=None, on_disconnect=None):
        self.__target_info = target_info
        self.file = file

        if on_connect is not None:
            on_connect = super().__on_connect

        if on_disconnect is not None:
            on_disconnect = super().__on_disconnect

        self.on_connect = on_connect
        self.on_disconnect = on_disconnect

        if handle_client is not None:
            super().__start_target = handle_client
        else:
            super().__start_target = super().__handle_client

        super().__recv_buffer = recv_buffer

        self.socket.bind(self.__target_info)
        self.socket.listen(listen)
        self.__accepting_thread.start()

    def exit(self):
        def join_():
            closing_connection = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
            closing_connection.connect(self.__target_info)
            closing_connection.close()
            self.socket.close()
            self.__accepting_thread.join()
            for thread in self.__allthreads.values():
                try:
                    thread.join()
                except Exception:
                    continue

        self.__kill = True
        self.event.accepting_thread.run = False
        kill = threading.Thread(target=join_, daemon=True)
        kill.start()