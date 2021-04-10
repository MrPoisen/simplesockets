import socket
import threading
import time
import traceback


class TCPClient:
    def __init__(self):

        def set_events():
            class Exceptions:
                occurred = False
                list = []

            class Event:
                # Exceptions
                exception = Exceptions()
                # Data
                new_data = False
                # Connection
                disconnected = False
                connected = False
                is_connected = False

            return Event()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.recved_data = []
        self.__autorecv = False
        self.__autorecv_thread = threading.Thread(target=self.__reciving_automatic)

        self.event = set_events()

        self.__allthreads = [self.__autorecv_thread]

        self.__target_ip = None
        self.__target_port = None
        self.__recv_buffer = None

        self.__start_taregt = None

        self.on_connect = None
        self.on_disconnect = None
        self.on_receive = None

    def __str__(self):
        return f'[socket : {str(self.socket)}, target address : ({self.__target_ip},{self.__target_port}), ' \
               f'receive buffer: {self.__recv_buffer}]'

    def __repr__(self):
        return f'[{str(self.socket)},({self.__target_ip},{self.__target_port}),{self.__recv_buffer}]'

    def setup(self, target_ip: str, target_port: int = 25567, recv_buffer: int = 2048, on_connect=None,
              on_disconect=None, on_receive=None):
        self.__target_ip = target_ip
        self.__target_port = target_port
        self.__recv_buffer = recv_buffer
        self.on_connect = on_connect
        self.on_disconnect = on_disconect
        self.on_receive = on_receive

    def reconnect(self) -> bool:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.event.connected = False
        self.event.disconnected = False
        return self.connect()

    def connect(self) -> bool:
        try:
            self.socket.connect((self.__target_ip, self.__target_port))

            self.event.is_connected = True
            self.event.connected = True
            # self.socket.setblocking(False)
            if callable(self.on_connect):
                self.on_connect()
            return True
        except Exception as e:
            self.event.exception.occurred = True
            self.event.exception.list.append((traceback.format_exc(), e))
            return False

    def send_data(self, data: bytes) -> bool:
        data_length = len(data)
        sended_length = 0
        while sended_length < data_length:
            sent = self.socket.send(data[sended_length:])
            if sent == 0:
                self.event.exception.list.append((RuntimeError("socket connection error")))
                self.event.exception.occurred = True
                return False
            sended_length += sent
        return True

    def return_recved_data(self) -> list:
        self.event.new_data = False
        data = self.recved_data.copy()
        self.recved_data = []
        return data

    def __reciving_automatic(self):
        while self.__autorecv:
            try:
                recved = self.recv_data()

                if len(recved) > 0:
                    if callable(self.on_receive):
                        self.on_receive(recved)

                    self.recved_data.append(recved)
                    self.event.new_data = True

            except Exception as e:
                self.event.exception.list.append((traceback.format_exc(), e))
                self.event.exception.occurred = True
                self.event.disconnected = True
                self.event.is_connected = False

                if callable(self.on_disconnect):
                    self.on_disconnect()

    def autorecv(self):
        if self.__autorecv is False:
            self.__autorecv = True
            try:
                self.__autorecv_thread.start()
            except Exception as e:
                self.event.exception.list.append((traceback.format_exc(), e))
                self.event.exception.occurred = True
                self.__autorecv_thread = threading.Thread(target=self.__reciving_automatic)
                self.__autorecv_thread.start()

    def shutdown(self):
        self.__autorecv = False
        self.__autorecv_thread = threading.Thread(target=self.__reciving_automatic)
        self.socket.close()

    def recv_data(self) -> bytes:
        chunks = []
        recv_data = True
        while recv_data:
            chunk = self.socket.recv(self.__recv_buffer)
            chunks.append(chunk)
            if len(chunk) < self.__recv_buffer:
                recv_data = False
        return b''.join(chunks)

    def return_exceptions(self, delete: bool = True, reset_exceptions: bool = True) -> list:
        exceptions = self.event.exception.list.copy()
        if delete:
            self.event.exception.list = []
        if reset_exceptions:
            self.event.exception.occurred = False
        return exceptions

    def exit(self):
        for number, thread in enumerate(self.__allthreads):
            try:
                thread.join()
            except Exception:
                self.__allthreads.pop(number)


class TCPServer:

    def __init__(self, max_connections=None):
        def get_event():
            class Exceptions:
                occurred = False
                list = []

            class Accept:
                run = True

            class Event:
                # Exceptions
                exception = Exceptions()
                # Data
                new_data = False
                # Accepting Thread
                accepting_thread = Accept()

            return Event()

        self.__kill = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = {}  # key: address, value : [client_thread,client_socket]
        self.__recv_buffer = 2048

        self.__accepting_thread = threading.Thread(target=self.__accept_clients)

        self.recved_data = []

        self.event = get_event()

        self.max_connections = max_connections

        self.__allthreads = {}

        self.__start_target = None

        self.on_connect = None
        self.on_disconnect = None
        self.on_receive = None

        self.__PORT = None
        self.__IP = None

    def __str__(self):
        return f'[socket : {str(self.socket)}, address : ({self.__IP},{self.__PORT}), ' \
               f'receive buffer: {self.__recv_buffer}]'

    def __repr__(self):
        return f'[{str(self.socket)},({self.__IP},{self.__PORT}),{self.__recv_buffer}]'

    # Prepares the Server
    def setup(self, ip: str = socket.gethostname(), port: int = 25567, listen: int = 5, recv_buffer: int = 2048,
              handle_client=None, on_connect=None, on_disconnect=None, on_receive=None):

        self.__PORT = port
        self.__IP = ip
        self.socket.bind((ip, port))
        self.socket.listen(listen)
        self.__recv_buffer = recv_buffer
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_receive = on_receive

        if handle_client is not None:
            self.__start_target = handle_client
        else:
            self.__start_target = self.__handle_client

        self.__accepting_thread.start()  # starts the accepting thread while the while loop is still false

    # Sends bytes to a target
    def send_data(self, data: bytes, client_socket: socket.socket) -> bool:
        data_length = len(data)
        sended_length = 0
        while sended_length < data_length:
            sent = client_socket.send(data[sended_length:])
            if sent == 0:
                self.event.exception.list.append((RuntimeError("socket connection error")))
                self.event.exception.occurred = True
                return False

            sended_length += sent
        return True

    # recv data from a target
    def recv_data(self, client_socket: socket.socket) -> bytes:
        chunks = []
        recv_data = True
        chunk = client_socket.recv(self.__recv_buffer)
        chunks.append(chunk)
        if len(chunk) >= self.__recv_buffer:
            while recv_data:
                chunk = client_socket.recv(self.__recv_buffer)
                chunks.append(chunk)
                if len(chunk) < self.__recv_buffer:
                    recv_data = False

        return b''.join(chunks)

    # returns all received data and clears self.recved_data and sets new_data_recved to False
    def return_recved_data(self):
        self.event.new_data = False
        data = self.recved_data.copy()
        self.recved_data = []
        return data

    # handles the connection
    def __handle_client(self, client_socket, address):
        try:
            while True:
                recved = self.recv_data(client_socket)
                if len(recved) > 0:
                    self.event.new_data = True
                    self.recved_data.append((client_socket, address, recved))

                    if callable(self.on_receive):
                        self.on_receive(recved)

        except Exception as e:
            self.event.exception.list.append((traceback.format_exc(), e))
            self.event.exception.occurred = True

            self.clients.pop(address)
            self.__allthreads.pop(address)

            if callable(self.on_disconnect):
                self.on_disconnect(address)

            if self.max_connections is not None and len(self.clients) < self.max_connections:
                self.run = True

    def __accept_clients(self):
        while self.__kill is False:
            time.sleep(0.1)
            while self.event.accepting_thread.run:
                client_socket, address = self.socket.accept()
                ct = threading.Thread(target=self.__start_target, args=(client_socket, address))
                self.clients[address] = [ct, client_socket]

                if callable(self.on_connect):
                    self.on_connect(address)

                ct.start()

                self.__allthreads[address] = ct  # add thread to all threads dict

                if self.max_connections is not None and len(self.clients) >= self.max_connections:
                    self.run = False

    # starts the server
    def start(self):
        self.event.accepting_thread.run = True

    # stops the server
    def stop(self):
        self.event.accepting_thread.run = False

    def restart(self):
        if self.__kill:
            self.__kill = False
            self.__accepting_thread = threading.Thread(target=self.__accept_clients)
            self.__accepting_thread.start()

        elif self.__kill is False:
            raise Exception("Can't restart stopped or running thread")

    def killed(self) -> bool:
        return self.__kill

    def disconnect(self, address: tuple):
        client_socket = self.clients.get(address)[1]
        self.clients.pop(address)
        self.__allthreads.pop(address)
        client_socket.close()

        if callable(self.on_disconnect):
            self.on_disconnect(address)

    def return_exceptions(self, delete: bool = True, reset_exception: bool = True) -> list:
        exceptions = self.event.exception.list.copy()
        if delete:
            self.event.exception.list = []
        if reset_exception:
            self.event.exception.occurred = False

        return exceptions

    def exit(self):
        def join_():
            closing_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            closing_connection.connect((self.__IP, self.__PORT))
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

    def exit_accept(self):
        self.__kill = True
        self.event.accepting_thread.run = False
