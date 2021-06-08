import socket
import threading
import time
import traceback
from typing import Callable, Union, Tuple, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from simplesockets._support_files.error import SetupError, Exception_Collection
from simplesockets._support_files.Events import Event, Event_System


@dataclass(frozen=True)
class Server_Client:
    socket: socket.socket
    address: tuple
    key: Any = None
    _thread: threading.Thread = None
    _recv_buffer: int = 1024

    def __str__(self):
        return str(self.socket)

    def recv(self):
        """
        function collects incoming data.`

        Returns:
            Socket_Response: returns received data as bytes
        """
        chunks = []
        recv_data = True
        while recv_data:
            chunk = self.socket.recv(self._recv_buffer)
            chunks.append(chunk)
            if len(chunk) < self._recv_buffer:
                recv_data = False
        return Socket_Response(b''.join(chunks), _time(), self)

    def send(self, data: bytes) -> None:
        """
        tries to send data to the Server

        Args:
            data: data that should be send

        Raises:
            ConnectionError: if the sending failed
        """
        data_length = len(data)
        sended_length = 0
        while sended_length < data_length:
            sent = self.socket.send(data[sended_length:])
            if sent == 0:
                raise ConnectionError("socket connection error")
            sended_length += sent

    def disconnect(self):
        """
        closes the socket
        """
        self.socket.close()

    def _add_thread(self, thread: threading.Thread):
        return Server_Client(self.socket, self.address, self.key, thread, self._recv_buffer)

    def _add_key(self, key):
        return Server_Client(self.socket, self.address, key, self._thread, self._recv_buffer)


@dataclass(frozen=True)
class Socket_Response:
    response: Union[bytes, Tuple[bytes]]
    time_: datetime
    from_: Server_Client = None

    def __str__(self):
        return "".join(["Socket_Response(response=", str(self.response), ", time=", str(self.time_)])

    def __len__(self):
        return len(self.response)

    def __getitem__(self, item):
        return self.response[item]

    def equals(self, information) -> bool:
        """
        checks if the response is equal to the given information

        Args:
            information(Union[bytes, Tuple[bytes], Socket_Response]): information which should be compared to the response

        Returns:
            Returns if the response and the information are equal

        """
        if isinstance(information, Socket_Response):
            return self.response == information.response
        elif isinstance(information, bytes) or isinstance(information, tuple):
            return self.response == information
        else:
            raise TypeError("information should be a Socket_Response, bytes or tuple object")

def _time() -> datetime:
    return datetime.now()

class TCPClient:
    """
    This class contains functions for connecting and keeping connections alive

    Attributes:
        self.EVENT_EXCEPTION (str): Returned by `await_event()` if an exception occurred
        self.EVENT_RECEIVED (str): Returned by `await_event()` if the client received data
        self.EVENT_TIMEOUT (str): Returned by `await_event()` if the function timed out
        self.EVENT_DISCONNECT (str): Returned by `await_event()` if client disconnected
        self.EVENT_CONNECTED (str): Returned by `await_event()` if client connected
        self.event.new_data (bool): Is True if the Client received new data
        self.event.disconnected (bool): Is True if the Client disconnected
        self.event.is_connected (bool): Is True if the Client is connected to the Server
        self.event.connected (bool): Is True if the Client connected
        self.event.exception.occurred (bool): Is True if an exception got caught
        self.event.exception.list (list): contains all caught exceptions
        self.recved_data (list): contains all received data

    """

    EVENT_EXCEPTION = Event("--EXCEPTION--")
    EVENT_RECEIVED = Event("--RECEIVED--")
    EVENT_TIMEOUT = Event("--TIMEOUT--")
    EVENT_DISCONNECT = Event("--DISCONNECT--")
    EVENT_CONNECTED = Event("--CONNECTED--")

    def __init__(self):

        def set_events():
            class Exceptions_:
                occurred: bool = False
                exceptions = Exception_Collection()

            class Events:
                # Exceptions
                exception = Exceptions_()
                # Data
                new_data: bool = False
                # Connection
                disconnected: bool = False
                connected: bool = False
                is_connected: bool = False

            return Events()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.recved_data = []
        self.__autorecv = False
        self.__autorecv_thread = threading.Thread(target=self.__reciving_automatic, daemon=True)

        self.event = set_events()
        self._event_system = Event_System()
        self._event_system.clear()

        self.__allthreads = [self.__autorecv_thread]

        self.__target_ip = None
        self.__target_port = None
        self.__recv_buffer = None

        self.__start_taregt = None

        self.on_connect = None
        self.on_disconnect = None
        self.on_receive = None

        self.__setup_flag = False

    def __str__(self):
        return f'[socket : {str(self.socket)}, target address : ({self.__target_ip},{self.__target_port}), receive buffer: {self.__recv_buffer}]'

    def __repr__(self):
        return f'[{str(self.socket)},({self.__target_ip},{self.__target_port}),{self.__recv_buffer}]'

    def __enter__(self):
        self.connect()
        self.autorecv()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def Address(self) -> tuple:
        """Address of the Client, containing it's ip and port"""
        return (self.__target_ip, self.__target_port)

    def await_event(self, timeout: Optional[int] = 0, disable_on_functions: Optional[bool] = False,) -> Union[
        Tuple[Event, List[Socket_Response]], Tuple[Event, dict], Tuple[Event, None]]:

        """
        waits till an event occurs

        Args:
            timeout: time till timeout in milliseconds
            disable_on_functions: If True, will set __connected and __disconnected flag to False

        Returns:
            returns event and its value(s)
        """
        if disable_on_functions:
            for ev in self._event_system:
                if ev.name == self.EVENT_CONNECTED.name or ev.name == self.EVENT_DISCONNECT.name:
                    self._event_system.remove(ev)

        ev_ = self._event_system.await_event(timeout if timeout != 0 else None)
        if ev_ is False:
            return self.EVENT_TIMEOUT.copy(), None

        ev: Event = self._event_system.first_event()

        if ev == self.EVENT_RECEIVED:
            return ev, self.return_recved_data(True)
        elif ev == self.EVENT_EXCEPTION:
            return ev, self.return_exceptions()
        elif ev == self.EVENT_CONNECTED:
            return ev, None
        elif ev == self.EVENT_DISCONNECT:
            return ev, None

        """
            if disable_on_functions:
                self.__connected = False
                self.__disconnected = False

            from time import time
            start_time = time()
            timeout = timeout / 1000

            while True:
                if self.event.exception.occurred:
                    return self.EVENT_EXCEPTION.copy(), self.return_exceptions()

                if self.event.new_data:
                    return self.EVENT_RECEIVED.copy(), self.return_recved_data()

                if self.__connected:
                    self.__connected = False
                    return self.EVENT_CONNECTED.copy(), None

                if self.__disconnected:
                    self.__disconnected = False
                    return self.EVENT_DISCONNECT.copy(), None

                if timeout > 0 and time() > start_time + timeout:
                    return self.EVENT_TIMEOUT.copy(), None
        """

    def setup(self, target_ip: str, target_port: Optional[int] = 25567, recv_buffer: Optional[int] = 2048,
              on_connect: Optional[Callable] = None, on_disconnect: Optional[Callable] = None,
              on_receive: Optional[Callable] = None):
        """
        function sets up the Client

        Args:
            target_ip: IP the Client should connect to
            target_port: PORT the Client should connect to
            recv_buffer: The receive buffer used for `socket.recv()`
            on_connect: Function that will be executed on connection, it takes not arguments
            on_disconnect: Function that will be executed on disconnection, it takes no arguments
            on_receive: Function that will be executed on receive, it takes the received data as an argument
        """

        self.__target_ip = target_ip
        self.__target_port = target_port
        self.__recv_buffer = recv_buffer
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_receive = on_receive

        self.__setup_flag = True

    def reconnect(self) -> bool:
        """
        tries to reconnect to the Server

        Returns:
            returns a bool if the connecting was successful
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.event.connected = False
        self.event.disconnected = False
        return self.connect()

    def connect(self) -> bool:
        """
        tries to connect to the Server

        Returns:
            returns a bool if the connecting was successful
        """
        if self.__setup_flag is False:
            raise SetupError("Server isn't setup")
        try:
            self.socket.connect((self.__target_ip, self.__target_port))

            self.event.is_connected = True
            self.event.connected = True
            # self.socket.setblocking(False)

            self._event_system.happened(self.EVENT_CONNECTED.copy())

            if callable(self.on_connect):
                self.on_connect()
            return True
        except Exception as e:
            self.event.exception.occurred = True
            self.event.exception.exceptions.add(e, traceback.format_exc())
            self._event_system.happened(self.EVENT_EXCEPTION.copy())
            return False

    def send_data(self, data: bytes) -> bool:
        """
        tries to send data to the Server, returns True if it was succesful

        Args:
            data: data that should be send

        Returns:
            returns True if the sending was successful
        """
        data_length = len(data)
        sended_length = 0
        while sended_length < data_length:
            sent = self.socket.send(data[sended_length:])
            if sent == 0:
                self.event.exception.exceptions.add(ConnectionError("socket connection error"))
                self.event.exception.occurred = True
                self._event_system.happened(self.EVENT_EXCEPTION.copy())
                return False
            sended_length += sent
        return True

    def return_recved_data(self, clear_event: bool = True) -> List[Socket_Response]:
        """
        returns received data

        Returns:
            returns a list of the received data
        """
        self.event.new_data = False
        if clear_event:
            self._event_system.clear_name(self.EVENT_RECEIVED.name)
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
                    self._event_system.happened(self.EVENT_RECEIVED.copy())

            except Exception as e:
                self.event.exception.exceptions.add(e, traceback.format_exc())
                self.event.exception.occurred = True
                self.event.disconnected = True
                self.event.is_connected = False

                self._event_system.happened(self.EVENT_EXCEPTION.copy())
                self._event_system.happened(self.EVENT_DISCONNECT.copy())

                if callable(self.on_disconnect):
                    self.on_disconnect()

    def autorecv(self) -> bool:
        """
        function which activates the auto-receiving thread, automatically saving all incoming data
        """
        if self.__autorecv is False:
            self.__autorecv = True
            try:
                self.__autorecv_thread.start()
                return True
            except Exception as e:
                self.event.exception.exceptions.add(e, traceback.format_exc())
                self.event.exception.occurred = True
                self._event_system.happened(self.EVENT_EXCEPTION.copy())
                self.__autorecv_thread = threading.Thread(target=self.__reciving_automatic, daemon=True)
                return False
        elif self.__autorecv is True:
            self.__autorecv = False
            self.__autorecv_thread = threading.Thread(target=self.__reciving_automatic, daemon=True)
            return True

        return False

    def recv_data(self) -> Socket_Response:
        """
        function collects incoming data. If you want to collect all incoming data automatically, use `Client.autorecv()`

        Returns:
            returns received data as bytes
        """
        chunks = []
        recv_data = True
        while recv_data:
            chunk = self.socket.recv(self.__recv_buffer)
            chunks.append(chunk)
            if len(chunk) < self.__recv_buffer:
                recv_data = False
        return Socket_Response(b''.join(chunks), _time())

    def return_exceptions(self, delete: Optional[bool] = True, reset_exceptions: Optional[bool] = True) -> dict:
        """
        this function returns all collected exceptions. Key is the time and value the Exception

        Args:
            delete: If the list which collected the exceptions should be cleared
            reset_exceptions: If the exception occurred variable should be reset (set to False)

        Returns:
            returns a list of all collected exceptions
        """

        exceptions = self.event.exception.exceptions.exceptions
        if delete:
            self.event.exception.exceptions.clear()
        if reset_exceptions:
            self.event.exception.occurred = False
            for ev in self._event_system:
                if ev.name == self.EVENT_EXCEPTION.name:
                    self._event_system.remove(ev)
        return exceptions

    def disconnect(self) -> bool:
        """
        tries to disconnect from the Server

        Returns:
            returns true if the client disconnected without an exception
        """
        try:
            self.socket.shutdown(1)
            self.socket.close()
            self.event.is_connected = False
            self.event.disconnected = True
            self._event_system.happened(self.EVENT_DISCONNECT.copy())
            self.__init__()
            return True
        except Exception as e:
            self.event.exception.occurred = True
            self.event.exception.exceptions.add(e, traceback.format_exc())
            self._event_system.happened(self.EVENT_DISCONNECT.copy())
            return False

    def close(self):
        """
        Closes the socket
        """
        self.socket.close()


class TCPServer:
    """
    This class contains functions for accepting connections and keeping connections alive

    Attributes:
            self.EVENT_EXCEPTION (str): Returned by `await_event()` if an exception occurred
            self.EVENT_RECEIVED (str): Returned by `await_event()` if the client received data
            self.EVENT_TIMEOUT (str): Returned by `await_event()` if the function timed out
            self.event.new_data (bool): Is True if the Client received new data
            self.event.exception.occurred (bool): Is True if an exception got caught
            self.event.exception.list (list): contains all caught exceptions
            self.recved_data (list): contains all received data
            self.socket (socket.socket): is the Server Socket
            self.clients (dict): contains the address as the key and the client thread and socket as a list as the values

    """

    EVENT_EXCEPTION = Event("--EXCEPTION--")
    EVENT_RECEIVED = Event("--RECEIVED--")
    EVENT_TIMEOUT = Event("--TIMEOUT--")

    def __init__(self, max_connections: Optional[int] = None):
        """
        Initializes the Server

        Args:
            max_connections: how many Clients can connect to the Server

        """
        def get_event():
            class Exceptions:
                occurred = False
                exceptions = Exception_Collection()

            class Accept:
                run = True

            class Events:
                # Exceptions
                exception = Exceptions()
                # Data
                new_data = False
                # Accepting Thread
                accepting_thread = Accept()

            return Events()

        self.__kill = False
        self.socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = {}  # key: address, value : [client_thread,client_socket] / key: address, value: Server_Client
        self.__recv_buffer = 2048

        self.__accepting_thread = threading.Thread(target=self.__accept_clients, daemon=True)

        self.recved_data = [] #Tuple: (client_socket, address, data)

        self.event = get_event()
        self._event_system = Event_System()
        self._event_system.clear()

        self.max_connections = max_connections

        self.__allthreads = {}

        self.__start_target = None

        self.on_connect = None
        self.on_disconnect = None
        self.on_receive = None

        self.__PORT = None
        self.__IP = None

        self.__setup_flag = False

    def __str__(self):
        return f'[socket : {str(self.socket)}, address : ({self.__IP},{self.__PORT}), ' \
               f'receive buffer: {self.__recv_buffer}]'

    def __repr__(self):
        return f'[{str(self.socket)},({self.__IP},{self.__PORT}),{self.__recv_buffer}]'

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __perfom_disconnect(self, address: tuple):
        self.clients.pop(address)
        self.__allthreads.pop(address)

        if callable(self.on_disconnect):
            self.on_disconnect(address)

        if self.max_connections is not None and len(self.clients) < self.max_connections:
            self.run = True

    # Prepares the Server
    def setup(self, ip: Optional[str] = "127.0.0.1", port: Optional[int] = 25567, listen: Optional[int] = 5,
              recv_buffer: Optional[int] = 2048, handle_client: Optional[Callable] = None,
              on_connect: Optional[Callable] = None, on_disconnect: Optional[Callable] = None,
              on_receive: Optional[Callable] = None):
        """
        function prepares the Server

        Args:
            ip: IP of the Server
            port: PORT the Server should listen on
            listen: parameter for `socket.listen()`
            recv_buffer: the receive buffer used for `socket.recv()`
            handle_client: the function for handling the Clients, should be left as None
            on_connect: function that will be executed on connection, it takes the address(tuple) as an argument
            on_disconnect: function that will be executed on disconnection, it takes the address(tuple) as an argument
            on_receive: function that will be executed on receive, it takes the clientsocket, address, received data as
                an argument
        """
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

        self.__setup_flag = True

    # Sends bytes to a target
    def send_data(self, data: Union[bytes, Socket_Response], client: Server_Client) -> bool:
        """
        function for sending data to a client,

        Args:
            data: data which should be send
            client: the client to which the data should be send to

        Returns:
            returns True if the operation was successful without an exception
        """
        if isinstance(data, Socket_Response):
            data = data.response

        try:
            client.send(data)
        except Exception as e:
            self.event.exception.exceptions.add(e, traceback.format_exc())
            self.event.exception.occurred = True

            self._event_system.happened(self.EVENT_EXCEPTION.copy())
            return False
        return True

    # recv data from a target
    def recv_data(self, client: Server_Client) -> Socket_Response:
        """
        function collects incoming data

        Returns:
            returns received data as bytes
        """
        return client.recv()

    # returns all received data and clears self.recved_data and sets new_data_recved to False
    def return_recved_data(self) -> List[Socket_Response]:
        """
        Returns received data. They are returned as Socket_Response objects

        Returns:
            returns a list of Socket_Response objects
        """
        self.event.new_data = False
        self._event_system.clear_name(self.EVENT_RECEIVED.name)
        data = self.recved_data.copy()
        self.recved_data.clear()
        return data

    # handles the connection
    def __handle_client(self, client: Server_Client):
        try:
            while True:
                try:
                    recved = self.recv_data(client)
                except ConnectionResetError:
                    return None
                #recved = self.recv_data(client_socket)
                if len(recved) > 0:
                    self.event.new_data = True
                    self.recved_data.append(recved)

                    if callable(self.on_receive):
                        self.on_receive(client, recved)

        except Exception as e:
            self.event.exception.exceptions.add(e, traceback.format_exc())
            self.event.exception.occurred = True

            self._event_system.happened(self.EVENT_EXCEPTION.copy())

            self.__perfom_disconnect(client.address)

    def __accept_clients(self):
        while self.__kill is False:
            time.sleep(0.1)
            while self.event.accepting_thread.run:
                try:
                    client_socket, address = self.socket.accept()
                except OSError:
                    self.exit_accept()
                    return
                server_client = Server_Client(client_socket, address, _recv_buffer=self.__recv_buffer)

                ct = threading.Thread(target=self.__start_target, args=(server_client,), daemon=True)
                server_client = server_client._add_thread(ct)
                #self.clients[address] = [ct, client_socket]

                self.clients[address] = server_client

                if callable(self.on_connect):
                    self.on_connect(server_client)

                ct.start()

                self.__allthreads[address] = ct  # add thread to all threads dict

                if self.max_connections is not None and len(self.clients) >= self.max_connections:
                    self.run = False

    def await_event(self, timeout: Optional[int] = 0) -> Union[
        Tuple[Event, dict], Tuple[Event, List[Socket_Response]], Tuple[Event, None]]:
        """
        waits till an event occurs

        Args:
            timeout: time till timeout in milliseconds. Zero means no timeout.

        Returns:
            Union[Tuple[str, list], Tuple[str, None]]: returns event and its value(s)

        """

        event_: bool = self._event_system.await_event(timeout if timeout != 0 else None)
        if event_:
            event: Event = self._event_system.first_event()
            if event == self.EVENT_EXCEPTION:
                return event, self.return_exceptions()
            elif event == self.EVENT_RECEIVED:
                return event, self.return_recved_data()
        else:
            return self.EVENT_TIMEOUT.copy(), None


        """from time import time
        start_time = time()
        timeout = timeout / 1000

        while True:
            if self.event.exception.occurred:
                return self.EVENT_EXCEPTION, self.return_exceptions()

            if self.event.new_data:
                return self.EVENT_RECEIVED, self.return_recved_data()

            if timeout > 0 and time() > start_time + timeout:
                return self.EVENT_TIMEOUT, None
        """

    # starts the server
    def start(self):
        """
        starts the accepting thread

        Raises:
            SetupError: If `Client.setup()` wasn't called before
        """
        if self.__setup_flag is False:
            raise SetupError("Server isn't setup")

        self.event.accepting_thread.run = True

    # stops the server
    def stop(self):
        """
        stops the accepting thread
        """
        self.event.accepting_thread.run = False

    def restart(self):
        """
        function tries to restart the accepting thread
        """
        if self.__kill:
            self.__kill = False
            self.__accepting_thread = threading.Thread(target=self.__accept_clients, daemon=True)
            self.__accepting_thread.start()

        elif self.__kill is False:
            raise Exception("Can't restart stopped or running thread")

    @property
    def killed(self) -> bool:
        """

        Returns: returns if the accepting thread got killed or not

        """

        return self.__kill

    def disconnect(self, address: tuple):
        """
        disconnects a socket from the Server

        Args:
            address: the address of the client which you want to disconnect
        """

        try:
            client: Server_Client = self.clients.get(address)
            self.clients.pop(address)
            self.__allthreads.pop(address)
            client.disconnect()
        except Exception as e:
            self.event.exception.occurred = True
            self.event.exception.exceptions.add(e, traceback.format_exc())

            self._event_system.happened(self.EVENT_EXCEPTION.copy())

        if callable(self.on_disconnect):
            self.on_disconnect(address)

    def return_exceptions(self, delete: Optional[bool] = True, reset_exception: Optional[bool] = True) -> dict:
        """
        Returns the collected exceptions as a dict. Key is the time and value the Exception

        Args:
            delete: If the list which collected the exceptions should be cleared
            reset_exception: If the exception occurred variable should be reset (set to False)

        Returns:
            returns a list of all collected exceptions

        """

        exceptions = self.event.exception.exceptions.exceptions.copy()
        if delete:
            self.event.exception.exceptions.clear()
        if reset_exception:
            self.event.exception.occurred = False
            self._event_system.clear_name(self.EVENT_EXCEPTION.name)

        return exceptions

    def exit_accept(self):
        """
        stops and kills the accepting thread
        """
        self.__kill = True
        self.event.accepting_thread.run = False

    def close(self):
        """
        Closes the socket
        """
        self.socket.close()
        clients = list(self.clients.values())
        for client in clients:
            client.disconnect()
            client._thread.join()
        self.__accepting_thread.join()