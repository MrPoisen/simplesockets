import socket
import threading
import time
import traceback
from typing import Callable


class TCPClient:
    '''
    This class contains functions for connecting and keeping connections alive
    '''
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
        self.__autorecv_thread = threading.Thread(target=self.__reciving_automatic, daemon=True)

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

    @property
    def Address(self):
        return (self.__target_ip, self.__target_port)

    def setup(self, target_ip: str, target_port: int = 25567, recv_buffer: int = 2048, on_connect: Callable = None,
              on_disconnect: Callable = None, on_receive: Callable = None):
        '''
        function sets up the Client

        :param target_ip: IP the Client should connect to
        :param target_port: PORT the Client should connect to
        :param recv_buffer: the receive buffer used for socket.recv()
        :param on_connect: function that will be executed on connection, it takes not arguments
        :param on_disconnect: function that will be executed on disconnection, it takes no arguments
        :param on_receive: function that will be executed on receive, it takes the received data as an argument
        '''
        self.__target_ip = target_ip
        self.__target_port = target_port
        self.__recv_buffer = recv_buffer
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_receive = on_receive

    def reconnect(self) -> bool:
        '''
        tries to reconnect to the Server

        :return: returns a bool if the connecting was successful
        '''
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.event.connected = False
        self.event.disconnected = False
        return self.connect()

    def connect(self) -> bool:
        '''
        tries to connect to the Server

        :return: returns a bool if the connecting was successful
        '''
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
        '''
        tries to send data to the Server

        :param data: data that should be send
        :return: returns True if the sending was successful
        '''
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
        '''
        returns received data

        :return: returns a list of the received data
        '''
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

    def autorecv(self) -> bool:
        '''
        function which activates the auto-receiving thread, automatically saving all incoming data
        '''
        if self.__autorecv is False:
            self.__autorecv = True
            try:
                self.__autorecv_thread.start()
                return True
            except Exception as e:
                self.event.exception.list.append((traceback.format_exc(), e))
                self.event.exception.occurred = True
                self.__autorecv_thread = threading.Thread(target=self.__reciving_automatic, daemon=True)
                return False
        elif self.__autorecv is True:
            self.__autorecv = False
            self.__autorecv_thread = threading.Thread(target=self.__reciving_automatic, daemon=True)
            return True

        return False

    def shutdown(self):
        '''
        sets the flag in the autorecv thread to False and closes the socket
        '''
        self.__autorecv = False
        self.socket.shutdown(1)
        self.socket.close()

    def recv_data(self) -> bytes:
        '''
        function collects all incoming data

        :return: returns received data as bytes
        '''
        chunks = []
        recv_data = True
        while recv_data:
            chunk = self.socket.recv(self.__recv_buffer)
            chunks.append(chunk)
            if len(chunk) < self.__recv_buffer:
                recv_data = False
        return b''.join(chunks)

    def return_exceptions(self, delete: bool = True, reset_exceptions: bool = True) -> list:
        '''
        this function returns all collected exceptions

        :param delete: if the list which collected the exceptions should be cleared
        :param reset_exceptions: if the exception occurred variable should be reset (set to False)
        :return: returns a list of all collected exceptions
        '''
        exceptions = self.event.exception.list.copy()
        if delete:
            self.event.exception.list = []
        if reset_exceptions:
            self.event.exception.occurred = False
        return exceptions

    def disconnect(self) -> bool:
        '''
        tries to disconnect from the Server
        '''
        try:
            self.socket.shutdown(1)
            self.socket.close()
            return True
        except Exception as e:
            self.event.exception.occurred = True
            self.event.exception.list.append((traceback.format_exc(), e))
            return False


class TCPServer:
    '''
    This class contains functions for accepting connections and keeping connections alive
    '''
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

        self.__accepting_thread = threading.Thread(target=self.__accept_clients, daemon=True)

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

    def __perfom_disconnect(self, address):
        self.clients.pop(address)
        self.__allthreads.pop(address)

        if callable(self.on_disconnect):
            self.on_disconnect(address)

        if self.max_connections is not None and len(self.clients) < self.max_connections:
            self.run = True

    # Prepares the Server
    def setup(self, ip: str = socket.gethostname(), port: int = 25567, listen: int = 5, recv_buffer: int = 2048,
              handle_client=None, on_connect=None, on_disconnect=None, on_receive=None):
        '''
        function prepares the Server

        :param ip: IP of the Server
        :param port: PORT the Server should listen on
        :param listen: parameter for socket.listen()
        :param recv_buffer: the receive buffer used for socket.recv()
        :param handle_client: the function for handling the Clients, should be left as None
        :param on_connect: function that will be executed on connection, it takes the address(tuple) as an argument
        :param on_disconnect: function that will be executed on disconnection, it takes the address(tuple) as an argument
        :param on_receive: function that will be executed on receive, it takes the clientsocket, address, received data
        as an argument
        '''
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
        '''
        function for sending data to a specific clientsocket

        :param data: data which should be send
        :param client_socket: the clientsocket from to which the data should be send to
        :return:
        '''
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
        '''
        function collects all incoming data

        :return: returns received data as bytes
        '''
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
        '''
        returns received data

        :return: returns a list of the received data
        '''
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
                        self.on_receive(client_socket, address, recved)

        except ConnectionResetError as e:
            pass
        except Exception as e:
            self.event.exception.list.append((traceback.format_exc(), e))
            self.event.exception.occurred = True

            self.__perfom_disconnect(address)

    def __accept_clients(self):
        while self.__kill is False:
            time.sleep(0.1)
            while self.event.accepting_thread.run:
                client_socket, address = self.socket.accept()
                ct = threading.Thread(target=self.__start_target, args=(client_socket, address), daemon=True)
                self.clients[address] = [ct, client_socket]

                if callable(self.on_connect):
                    self.on_connect(address)

                ct.start()

                self.__allthreads[address] = ct  # add thread to all threads dict

                if self.max_connections is not None and len(self.clients) >= self.max_connections:
                    self.run = False

    # starts the server
    def start(self):
        '''
        starts the accepting thread
        '''
        self.event.accepting_thread.run = True

    # stops the server
    def stop(self):
        '''
        stops the accepting thread
        '''
        self.event.accepting_thread.run = False

    def restart(self):
        '''
        function tries to restart the accepting thread
        '''
        if self.__kill:
            self.__kill = False
            self.__accepting_thread = threading.Thread(target=self.__accept_clients, daemon=True)
            self.__accepting_thread.start()

        elif self.__kill is False:
            raise Exception("Can't restart stopped or running thread")

    @property
    def killed(self) -> bool:
        '''
        :return: returns if the accepting thread got killed
        '''
        return self.__kill

    def disconnect(self, address: tuple):
        '''
        disconnects a socket from the Server

        :param address: the address of the client which you want to disconnect
        '''
        try:
            client_socket = self.clients.get(address)[1]
            self.clients.pop(address)
            self.__allthreads.pop(address)
            client_socket.shutdown(1)
            client_socket.close()
        except Exception as e:
            self.event.exception.occurred = True
            self.event.exception.list.append((traceback.format_exc(), e))

        if callable(self.on_disconnect):
            self.on_disconnect(address)

    def return_exceptions(self, delete: bool = True, reset_exception: bool = True) -> list:
        '''
        this function returns all collected exceptions

        :param delete: if the list which collected the exceptions should be cleared
        :param reset_exceptions: if the exception occurred variable should be reset (set to False)
        :return: returns a list of all collected exceptions
        '''
        exceptions = self.event.exception.list.copy()
        if delete:
            self.event.exception.list = []
        if reset_exception:
            self.event.exception.occurred = False

        return exceptions

    def exit_accept(self):
        '''
        stops and kills the accepting thread
        '''
        self.__kill = True
        self.event.accepting_thread.run = False
