from simplesockets._support_files import b_veginer
from simplesockets._support_files import RSA
from simplesockets._support_files import cipher
from simplesockets.simple_sockets import TCPClient, TCPServer, Server_Client, Socket_Response, _time

from typing import Callable, Optional
import json
import time
import os
import traceback


class SecureClient(TCPClient):
    def __init__(self):
        """

        Attributes:
            self.user (str): should contain the username of the Client
            self.pw (str): should contain the password of the Client
            self.seperators (list): bytes separating the the received information's
            self.own_keys (list): contains the Keys, first the private, second the public
            self.server_key (RSA_Public_Key): should contain the Key of the Server
            self.users_keys (dict): should contain as a key the username, as the value the public Key

        """
        super().__init__()
        self.user: str = ""
        self.pw = ""

        self.seperators: list = [b'type_targ_sepLnpEwEljZi', b'targ_data_sepcLkGqydgGY']

        private = RSA.get_private_key()
        public = private.public_key()
        self.own_keys: list = [private, public] #0:private, 1:public

        self.server_key: RSA.RSA_PUBLIC_KEY = None
        self.users_keys:dict = {} #Key: username, value: public key

        self.__first_keys = True

    @property
    def connected_users(self) -> list:
        """list of all users in the self.users_keys dict"""
        return list(self.users_keys.keys())

    def __enrcypt_data(self, data: bytes, key: RSA.RSA_PUBLIC_KEY) -> bytes:
        Combined_key = b_veginer.Combined_Key(b_veginer.get_vigenere_key(64),
                                              b_veginer.Combined_Key.get_transposition_key((4, 100)))
        pad = b_veginer.Pad(Combined_key, (2, 10), (2, 10))
        encrypted = pad.encrypt(data)
        encr_key = key.encrypt(Combined_key.export_key(), 1)
        return b''.join([encrypted, b'$$$$', encr_key])

    def __decypt_data(self, data: bytes, prkey: RSA.RSA_PRIVATE_KEY) -> bytes:
        encrypted, combined_key = data.split(b'$$$$')
        Combined_key = b_veginer.Combined_Key.import_key(prkey.decrypt(combined_key, 1))
        pad = b_veginer.Pad(Combined_key)
        return pad.decrypt(encrypted)

    def setup(self, target_ip: str, target_port: Optional[int] = 25567, recv_buffer: Optional[int] = 2048,
              on_connect: Optional[Callable] = None, on_disconnect: Optional[Callable] = None,
              on_receive: Optional[Callable] = None):
        """
        function sets up the Client

        Args:
            target_ip: IP the Client should connect to
            target_port: PORT the Client should connect to
            recv_buffer: PORT the Client should connect to
            on_connect: function that will be executed on connection, it takes not arguments
            on_disconnect: function that will be executed on disconnection, it takes no arguments
            on_receive: function that will be executed on receive, it takes the received data as an argument

        """
        if on_connect is None:
            on_connect = self.on_connect

        super().setup(target_ip, target_port, recv_buffer, on_connect, on_disconnect, on_receive)

    def login_data(self, user: str, password):
        """
        overwrites self.user and self.pw with given arguments

        Args:
            user: username
            password: password
        """
        self.user = user
        self.pw = password

    def on_connect(self) -> bool:
        """
        this function is executed on connection
        """
        # Exchange
        recved = super().recv_data()
        self.server_key = RSA.import_key(recved.response)
        self.send_data(target=b'Server', type=b'key', data=self.own_keys[1].unofficial_export(), key=self.server_key)

        #Login

        login = self.user.encode() + b'%|%' + self.pw.encode()
        self.send_data(b'Server', b'login', login, key=self.server_key)
        target, type, data = self.recv_data().response

        if type == b'Rejected':
            self.socket.close()
            return False

        if type == b'keys':
            if self.__first_keys:
                self.__first_keys = False
            keys = {}
            try:
                pairs = data.split(b'!!next!!')
                for pair in pairs:
                    if len(pair) > 0:
                        user, key = pair.split(b'user-key')
                        keys[user.decode()] = RSA.import_key(key)
                self.users_keys = keys.copy()
            except Exception as e:
                self.event.exception.occurred = True
                self.event.exception.exceptions.add(e, traceback.format_exc())

                self._event_system.happened(self.EVENT_EXCEPTION.copy())
            return True

    def recv_data(self) -> Socket_Response:
        """
        function collects all incoming data

        Returns:
            tuple, first the target, second the type, third the data

        """
        recv = super().recv_data()
        type, rest = recv.response.split(self.seperators[0])
        target, data = rest.split(self.seperators[1])

        #Decrypt
        try:
            type = self.own_keys[0].decrypt(type, 1)
            target = self.__decypt_data(target, self.own_keys[0])
        except ValueError:
            pass

        data = self.__decypt_data(data, self.own_keys[0])

        return Socket_Response((target, type, data), _time())

    def send_data(self, target: bytes, type: bytes, data: bytes, username: Optional[str] = None,
                  key: Optional[RSA.RSA_PUBLIC_KEY] = None, encr_rest: bool = True) -> bool:
        """
        Sends data to the the username or given socket encrypted with a key

        Args:
            target: information used for target
            type: information used for type
            data: data to send
            username: the username of the user to send, if not given, you must give a key
            key: the RSA Public Key used for encryption,  if not given, you must give an username
            encr_rest: if type and target should be encrypted

        Returns:
            returns True if the sending was successful

        """

        if key is not None and username is None:
            pass
        elif key is None and username is not None:
            if username is not self.user:
                key = self.users_keys.get(username)
            else:
                key = self.own_keys[1]
        else:
            return False

        if key is None:
            return False

        if encr_rest:
            target = self.__enrcypt_data(target, self.server_key)
            type = self.server_key.encrypt(type, 1)

        data = self.__enrcypt_data(data, key)

        to_send = type + self.seperators[0] + target + self.seperators[1] + data
        return super().send_data(to_send)

    def get_key(self, username: str) -> RSA.RSA_PUBLIC_KEY:
        """
        function returns a key for a username

        Args:
            username: username used for finding the key

        Returns:
            returns a RSA Public key

        """
        return self.users_keys.get(username)


class SecureServer(TCPServer):
    def __init__(self, max_connections: Optional[int] = None):
        """

        Args:
            max_connections: how many Clients can connect to the Server

        Attributes:
            self.users: contains the address as the key and the username as the value
            self.own_keys: contains the private Key and the public Key
            self.client_keys: contains the username as the key and the public Key as the value
            self.to_send_client_keys: contains the username as the key and the public Key as bytes as the value
            self.seperators: contains bytes separating the received information's
            self.filepath: path to a json file containing usernames and their passwords
            self.indent: indent used for json

        """
        super().__init__(max_connections)
        self.users = {}  # Key: address, value: username

        private = RSA.get_private_key()
        public = private.public_key()

        self.own_keys = [private, public]  # 0 is private, 1 is public
        self.client_keys = {}  # Key: username, value: public key
        self.to_send_client_keys = {}  # Key: username, value: public key as bytes

        self.seperators = [b'type_targ_sepLnpEwEljZi', b'targ_data_sepcLkGqydgGY']

        self.filepath = None

        self.indent = 4

    def __enrcypt_data(self, data: bytes, key: RSA.RSA_PUBLIC_KEY) -> bytes:
        Combined_key = b_veginer.Combined_Key(b_veginer.get_vigenere_key(64),
                                              b_veginer.Combined_Key.get_transposition_key((4, 100)))
        pad = b_veginer.Pad(Combined_key, (2, 10), (2, 10))
        encrypted = pad.encrypt(data)
        try:
            encr_key = key.encrypt(Combined_key.export_key(), 1)
        except Exception as e:
            # TODO: key.encrypt seems to be transposition key
            raise e

        return b''.join([encrypted, b'$$$$', encr_key])

    def __decypt_data(self, data: bytes, prkey: RSA.RSA_PRIVATE_KEY) -> bytes:
        encrypted, combined_key = data.split(b'$$$$')
        Combined_key = b_veginer.Combined_Key.import_key(prkey.decrypt(combined_key, 1))
        pad = b_veginer.Pad(Combined_key)
        return pad.decrypt(encrypted)


    def setup(self, ip: Optional[str] = "127.0.0.1", port: Optional[int] = 25567,
              listen: Optional[int] = 5, recv_buffer: Optional[int] = 2048, handle_client: Optional[Callable] = None,
              on_connect: Optional[Callable] = None, on_disconnect: Optional[Callable] = None,
              on_receive: Optional[Callable] = None, filepath: str = None):
        """
        prepares the Server

        Args:
            filepath: absolut Path of the json file containing usernames and their passwords
            ip: IP of the Server
            port: PORT the Server should listen on
            listen: parameter for socket.listen()
            recv_buffer: the receive buffer used for socket.recv()
            handle_client: the function for handling the Clients, should be left as None
            on_connect: function that will be executed on connection, it takes the address(tuple) as an argument
            on_disconnect: function that will be executed on disconnection, it takes the address(tuple) as an argument
            on_receive: function that will be executed on receive, it takes the clientsocket, address, received data

        Raises:
            Exception: When filepath is missing and no alternative on_connect function is given
        """
        if on_connect is None:
            on_connect = self.on_connect

        if on_disconnect is None:
            on_disconnect = self.on_disconnect

        if isinstance(filepath, str):
            try:
                filepath = os.path.expanduser(filepath)
                with open(filepath, "r") as file:
                    json.load(file)
            except Exception:
                self.filepath = None
                if on_connect is not None:
                    raise Exception("You must give a filepath to a json file, containing information about users "
                                    "and their passwords")
            else:
                self.filepath = filepath

        super().setup(ip, port, listen, recv_buffer, handle_client, on_connect=on_connect,
                      on_disconnect=on_disconnect, on_receive=on_receive)

    def on_connect(self, address: tuple):
        """
        this function gets call when a new client connects to the Server
        """
        # exchange keys
        client = self.clients.get(address)[1]
        super().send_data(self.own_keys[1].unofficial_export(), client)
        target, type_, data = self.recv_data(client).response
        public_key: bytes = self.__decypt_data(data, self.own_keys[0])
        # login

        target, type_, login_data = self.recv_data(client).response
        login_data = self.__decypt_data(login_data, self.own_keys[0]).decode()
        user, pw = login_data.split('%|%')
        check = self.check_user(user, pw)

        if check:

            self.client_keys[user] = RSA.import_key(public_key)
            self.to_send_client_keys[user] = public_key
            self.users[address] = user
            time.sleep(0.05)
            to_send_keys = self.to_send_client_keys.copy()
            client_keys = b''
            for user, key in to_send_keys.items():
                client_keys = client_keys + user.encode() + b'user-key' + key + b'!!next!!'
            self.send_data(target=b'Client', type=b'keys', data=client_keys, username=user)

        else:
            self.send_data(target=b'Client', type=b'Rejected', data=b'Rejected',
                           key=RSA.import_key(public_key), client=client)
            self.disconnect(address)

    def on_disconnect(self, address: tuple):
        """
        this function gets called when a client gets disconnected

        Args:
            address: the address, containing Ip and Port

        """
        try:
            username = self.users.pop(address)
            self.client_keys.pop(username)
            self.to_send_client_keys.pop(username)
        except Exception as e:
            self.event.exception.occurred = True
            self.event.exception.exceptions.add(e, traceback.format_exc())

            self._event_system.happened(self.EVENT_EXCEPTION.copy())

    def load_users(self, get: Optional[str] = None) -> dict:  # json
        """
        this function loads the json file with the users and their passwords

        Args:
            get: calls the dict.get() function with the given parameter

        Returns:
            returns a dict

        """
        with open(self.filepath, 'r') as file:
            loaded = json.loads(file.read())
        if get is None:
            return loaded
        else:
            return loaded.get(get)

    def save_users(self, users: dict, get: Optional[str] = None):  # json
        """
        saves the users and their password dict

        Args:
            users: the users dictionary
            get: calls the dict.get() function with the given parameter

        """
        with open(self.filepath, 'r') as file:
            read_: dict = json.loads(file.read())

        if get is not None:
            read_[get] = users
        else:
            read_ = users

        with open(self.filepath, 'w') as file:
            json.dump(read_, file, indent=self.indent)

    def add_user(self, username: str, pw: str, get: Optional[str] = None):
        """
        adds a username and a password to the already given json file

        Args:
            username: the username
            pw: the password
            get: calls the dict.get() function with the given parameter

        """
        users = self.load_users(get)
        hashed_pw = cipher.gen_hash(pw)
        users[username] = hashed_pw
        self.save_users(users, get)

    def check_user(self, username: str, pw: str, get: Optional[str] = None) -> bool:  # pw not hashed already
        """
        checks if the given username and password are in the json file and are valid

        Args:
            username: username to check
            pw: password to check (not yet hashed)
            get: calls the dict.get() function with the given parameter

        Returns:
            returns True if username and password are valid

        """
        users = self.load_users(get)
        actual_pw = users.get(username)
        if actual_pw is None:
            return False
        return cipher.compare_hash(pw, actual_pw)

    def get_address_by_user(self, user: str) -> tuple:
        """
        uses the username to get the address

        Args:
            user: username

        Returns:
            returns the address

        """
        return list(self.users.keys())[list(self.users.values()).index(user)]

    def get_public_key(self, username: str) -> RSA.RSA_PUBLIC_KEY:
        """
        gets the public key from the username

        Args:
            username: username

        Returns:
            returns a RSA Public Key

        """
        return self.client_keys.get(username)

    def recv_data(self, client: Server_Client) -> Socket_Response:
        """
        function collects incoming data

        Args:
            client: client socket

        Returns:
            tuple: first the target, second the type, third the data

        """
        recv = super().recv_data(client)
        type, rest = recv.response.split(self.seperators[0])
        target, data = rest.split(self.seperators[1])

        # Decrypt
        try:
            type = self.own_keys[0].decrypt(type, 1)
            target = self.__decypt_data(target, self.own_keys[0])
        except ValueError:
            pass
        return Socket_Response((target, type, data), _time(), client)

    def send_data(self, target: bytes, type: bytes, data: bytes, username: Optional[str] = None,
                  key: Optional[RSA.RSA_PUBLIC_KEY] = None, client: Optional[Server_Client] = None,
                  encr_data: Optional[bool] = True, encr_rest: bool = True) -> bool:
        """
        function sends encrypted data to a user or socket

        Args:
            target: information used for target
            type: information used for type
            data: data to send
            username: the username of the user to send, if not given, you must give a socket and a key
            key: the RSA Public Key used for encryption,  if not given, you must give an username
            client: client object, if not given, you must give an username
            encr_data: if the data should be encrypted
            encr_rest: if the target and type should be encrypted

        Returns:
            returns True if the sending was successful

        """
        if key is not None and client is not None and username is None:
            pass
        elif key is None and client is None and username is not None:
            key = self.client_keys.get(username)
            client = self.clients.get(self.get_address_by_user(username))[1]
        elif key is None and client is not None and username is None and encr_data is False and encr_rest is False:
            pass
        elif encr_rest is False and encr_data is False and client is not None:
            pass
        elif client.key is not None:
            key = client.key
        else:
            self.event.exception.occurred = True
            self.event.exception.exceptions.add(
                Exception("You must give an username or key and clientsocket", traceback.format_exc()))
            self._event_system.happened(self.EVENT_EXCEPTION.copy())
            return False

        if encr_rest:
            target = self.__enrcypt_data(target, key)
            type = key.encrypt(type, 1)
        if encr_data:
            data = self.__enrcypt_data(data, key)

        to_send = type + self.seperators[0] + target + self.seperators[1] + data
        return super().send_data(to_send, client)

    def get_client_keys(self) -> dict:
        """

        Returns:
            returns a copy of the dictonary containing clients and there importable keys

        """
        return self.to_send_client_keys.copy()

    def decrypt_data(self, data: bytes) -> bytes:
        """
        function can be used for decrypting the received data with the Server RSA Private Key

        Args:
            data: data which should be decrypted

        Returns:
            returns decrypted data

        """
        return self.__decypt_data(data, self.own_keys[0])
