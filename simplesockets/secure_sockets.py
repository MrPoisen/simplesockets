from typing import Optional, Callable

from .simple_sockets import TCPClient, TCPServer, Server_Client, Socket_Response, _time
from ._support_files.error import SetupError

from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Random import get_random_bytes

import time
import threading
import traceback

class SecureClient(TCPClient):
    def __init__(self):
        super().__init__()
        self._key = get_random_bytes(32)
        self._cipher = AES.new(self._key, AES.MODE_EAX)

    @property
    def key(self) -> bytes:
        """Returns the 256 bit AES key value"""
        return self._key

    @property
    def cipher(self):
        """Returns the AES Cipher object"""
        return self._cipher

    def recv_data(self, raw: bool = False) -> Socket_Response:
        """
        function collects incoming data. If you want to collect all incoming data automatically, use `Client.autorecv()`

        Args:
            raw: if False, received data will not be decrypted with the key
        Returns:
            returns received data as bytes
        """
        chunks = []
        recv_data = True
        while recv_data:
            chunk = self.socket.recv(self._recv_buffer)
            chunks.append(chunk)
            if len(chunk) < self._recv_buffer:
                recv_data = False
        result = b''.join(chunks)
        if not raw:
            result = self._cipher.decrypt(result)
            self._cipher = AES.new(self._key, AES.MODE_EAX, self.cipher.nonce)
        return Socket_Response(result, _time())

    def send_data(self, data: bytes) -> bool:
        """
        tries to send data to the Server, returns True if it was successful

        Args:
            data: data that should be send

        Returns:
            returns True if the sending was successful
        """
        data = self._cipher.encrypt(data)
        self._cipher = AES.new(self._key, AES.MODE_EAX, self.cipher.nonce)
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

    def connect(self) -> bool:
        """
        tries to connect to the Server

        Returns:
            returns a bool if the connecting was successful
        """

        if self._setup_flag is False:
            raise SetupError("Server isn't setup")
        try:
            self.socket.connect((self._target_ip, self._target_port))

            self.event.is_connected = True
            self.event.connected = True
            # self.socket.setblocking(False)

            self._event_system.happened(self.EVENT_CONNECTED.copy())

            #  exchange keys

            # get public rsa key
            key = self.recv_data(True).response #doesn't work, must receice manually
            key = RSA.import_key(key)

            # send AES key
            cipher_rsa = PKCS1_OAEP.new(key)
            encrypt_key = cipher_rsa.encrypt(self._key)
            encrypted_nonce = cipher_rsa.encrypt(self._cipher.nonce)
            self.socket.send(encrypt_key)
            self.socket.send(encrypted_nonce)

            if callable(self.on_connect):
                self.on_connect()
            return True
        except Exception as e:
            self.event.exception.occurred = True
            self.event.exception.exceptions.add(e, traceback.format_exc())
            self._event_system.happened(self.EVENT_EXCEPTION.copy())
            return False

class SecureServer(TCPServer):
    """
    This class contains functions for accepting connections and keeping connections alive
    It also automatically

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
    def __init__(self, max_connections: int = None):
        super().__init__(max_connections)
        self._privatkey = None
        self._publickey = None
        self._exported_publickey = None

    def setup(self, ip: Optional[str] = "127.0.0.1", port: Optional[int] = 25567, listen: Optional[int] = 5,
              recv_buffer: Optional[int] = 2048, handle_client: Optional[Callable] = None,
              on_connect: Optional[Callable] = None, on_disconnect: Optional[Callable] = None,
              on_receive: Optional[Callable] = None, keysize: int = 2048):
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
        super().setup(ip, port, listen, recv_buffer, handle_client, on_connect, on_disconnect, on_receive)
        self._privatkey = RSA.generate(keysize)
        self._publickey = self._privatkey.public_key()
        self._exported_publickey = self._publickey.export_key()

    @property
    def privatekey(self) -> RSA.RsaKey:
        """Returns the private RSA key"""
        return self._privatkey

    @property
    def publickey(self) -> RSA.RsaKey:
        """Returns the public RSA key"""
        return self._publickey

    def _accept_clients(self):
        """
        This function handle the accepting of connections, the key exchange and the start of the thread,
        handling the connection
        """
        while self._kill is False:
            time.sleep(0.1)
            while self.event.accepting_thread.run:
                try:
                    client_socket, address = self.socket.accept()
                except OSError:
                    self.exit_accept()
                    return

                server_client = Server_Client(client_socket, address, recv_buffer=self._recv_buffer)

                # send public RSA KEY
                client_socket.sendall(self._exported_publickey)

                # receive encrypted AES key
                encrypted_key = server_client.recv()
                encrypted_nonce = server_client.recv()

                # decrypt key and nonce
                cipher_rsa = PKCS1_OAEP.new(self._privatkey)
                key = cipher_rsa.decrypt(encrypted_key.response)
                nonce = cipher_rsa.decrypt(encrypted_nonce.response)

                # create AES key
                cipher_aes = AES.new(key, AES.MODE_EAX, nonce)

                # add key to Server_Client object
                server_client = server_client._add_cipher(key, cipher_aes)

                ct = threading.Thread(target=self._start_target, args=(server_client,), daemon=True)
                server_client = server_client._add_thread(ct)
                #self.clients[address] = [ct, client_socket]

                self.clients[address] = server_client

                if callable(self.on_connect):
                    self.on_connect(server_client)

                ct.start()

                self._allthreads[address] = ct  # add thread to all threads dict

                if self.max_connections is not None and len(self.clients) >= self.max_connections:
                    self.run = False