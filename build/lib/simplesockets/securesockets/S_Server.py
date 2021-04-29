from simplesockets._support_files import cipher
from simplesockets.simple_sockets import TCPServer

import json
import socket
import time


class Server_(TCPServer):
    def __init__(self, max_connections=None):
        super().__init__(max_connections)
        self.users = {}  # Key: address, value: username

        private, public = cipher.gen_asym_keys()

        self.own_keys = [private, public]  # 0 is private, 1 is public
        self.client_keys = {}  # Key: username, value: public key
        self.to_send_client_keys = {}  # Key: username, value: public key as bytes

        self.seperators = [b'type_targ_sepLnpEwEljZi', b'targ_data_sepcLkGqydgGY']

        self.filepath = None

        self.indent = 4

    def setup(self, filepath: str, ip: str = socket.gethostname(), port: int = 25567, listen: int = 5,
              recv_buffer: int = 2048, handle_client=None, on_connect=None, on_disconnect=None, on_receive=None):
        '''
        function prepares the Server

        :param filepath: absolut Path of the json file containing usernames and their passwords
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
        if on_connect is None:
            on_connect = self.on_connect

        if on_disconnect is None:
            on_disconnect = self.on_disconnect

        self.filepath = filepath

        super().setup(ip, port, listen, recv_buffer, handle_client, on_connect=on_connect,
                      on_disconnect=on_disconnect, on_receive=on_receive)

    def on_connect(self, address):
        '''
        this function gets call when a nwe client connects to the Server
        '''
        # exchange keys
        client_socket = self.clients.get(address)[1]
        super().send_data(cipher.export_asym_key(self.own_keys[0]), client_socket=client_socket)
        target, type_, data = self.recv_data(client_socket)
        public_key = cipher.decr_data(data, prkey=self.own_keys[0], output="bytes")
        # login

        target, type_, login_data = self.recv_data(client_socket)
        login_data: str = cipher.decr_data(login_data, prkey=self.own_keys[0])
        user, pw = login_data.split('%|%')
        check = self.check_user(user, pw)

        if check:

            self.client_keys[user] = cipher.import_asym_key(public_key)
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
                           key=cipher.import_asym_key(public_key), client_socket=client_socket)

            self.disconnect(address)

    def on_disconnect(self, address):
        '''
        this function gets called when a client gets disconnected
        '''
        username = self.users.pop(address)
        self.client_keys.pop(username)
        self.to_send_client_keys.pop(username)

    def load_users(self, get: str = None) -> dict:  # json
        '''
        this function loads the json file with the users and their passwords

        :param get: calls the dict.get() function with the given parameter
        :return: returns a dict
        '''
        with open(self.filepath, 'r') as file:
            loaded = json.loads(file.read())
        if get is None:
            return loaded
        else:
            return loaded.get(get)

    def save_users(self, users: dict, get: str = None):  # json
        '''
        saves the users and their password dict

        :param users: the users dictionary
        :param get: calls the dict.get() function with the given parameter
        '''
        with open(self.filepath, 'r') as file:
            read_: dict = json.loads(file.read())

        if get is not None:
            read_[get] = users
        else:
            read_ = users

        with open(self.filepath, 'w') as file:
            json.dump(read_, file, indent=self.indent)

    def add_user(self, username: str, pw: str, get: str = None):
        '''
        adds a username and a password to the already given json file

        :param username: the username
        :param pw: the password
        :param get: calls the dict.get() function with the given parameter
        '''
        users = self.load_users(get)
        hashed_pw = cipher.gen_hash(pw)
        users[username] = hashed_pw
        self.save_users(users, get)

    def check_user(self, username: str, pw: str, get: str = None) -> bool:  # pw not hashed already
        '''
        checks if the given username and password are in the json file and are valid

        :param username: username to check
        :param pw: password to check (not yet hashed)
        :param get: calls the dict.get() function with the given parameter
        :return: returns True if username and password are valid
        '''
        users = self.load_users(get)
        actual_pw = users.get(username)
        if actual_pw is None:
            return False
        return cipher.compare_hash(pw, actual_pw)

    def get_address_by_user(self, user: str) -> tuple:
        '''
        uses the username to get the address

        :param user: username
        :return: returns the address
        '''
        return list(self.users.keys())[list(self.users.values()).index(user)]

    def get_public_key(self, username: str):
        '''
        gets the public key from the username

        :param username: username
        :return: returns a RSA Public Key
        '''
        return self.client_keys.get(username)

    def recv_data(self, client_socket: socket.socket) -> tuple:
        '''
        function collects all incoming data

        :param client_socket: client socket
        :return: tuple, first the target, second the type, third the data
        '''
        recv: bytes = super().recv_data(client_socket)
        type, rest = recv.split(self.seperators[0])
        target, data = rest.split(self.seperators[1])

        # Decrypt
        type = cipher.decrypt_asym(type, self.own_keys[0])
        target = cipher.decr_data(target, prkey=self.own_keys[0], output="bytes")

        return (target, type, data)

    def send_data(self, target: bytes, type: bytes, data: bytes, username: str = None, key=None,
                  client_socket :socket.socket = None, encr_data: bool = True) -> bool:
        '''
        function sends encrypted data to a user or socket

        :param target: information used for target
        :param type: information used for type
        :param data: data to send
        :param username: the username of the user to send, if not given, you must give a socket and a key
        :param key: the RSA Public Key used for encryption,  if not given, you must give an username
        :param client_socket: client socket,  if not given, you must give an username
        :param encr_data: if the data should be encrypted
        :return: returns True if the sending was successful
        '''
        if key is not None and client_socket is not None and username is None:
            pass
        elif key is None and client_socket is None and username is not None:
            key = self.client_keys.get(username)
            client_socket = self.clients.get(self.get_address_by_user(username))[1]
        else:
            self.event.exception.occurred = True
            self.event.exception.list.append((Exception("You must give an username or key and clientsocket")))
            return False

        target = cipher.encr_data(target, key)
        type = cipher.encrypt_asym(type, key)
        if encr_data:
            data = cipher.encr_data(data, key)

        to_send = type + self.seperators[0] + target + self.seperators[1] + data
        return super().send_data(to_send, client_socket)

    def get_client_keys(self):
        '''
        :return: returns a copy of the dictonary containing clients and there importable keys
        '''
        return self.to_send_client_keys.copy()

    def decrypt_data(self, data: bytes):
        '''
        function can be used for decrypting the received data with the Server RSA Private Key

        :param data: data which should be decrypted
        :return: returns decrypted data
        '''
        return cipher.decr_data(data, self.own_keys[0])