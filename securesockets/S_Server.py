from simplesockets._support_files import cipher
from simplesockets.simplesockets import TCPServer

import json
import threading
import socket
import time


class Server_(TCPServer):
    def __init__(self, max_connections=None):
        super().__init__(max_connections)
        self.users = {}  # Key: address, value: username

        private, public = cipher.gen_asym_keys()

        self.own_keys = [private, public]  # 0 is private, 1 is public
        self.__client_keys = {}  # Key: username, value: public key
        self.__to_send_client_keys = {}  # Key: username, value: public key as bytes

        self.seperators = [b'type_targ_sepLnpEwEljZi', b'targ_data_sepcLkGqydgGY']

        self.filepath = None

        self.indent = 4

    def setup(self, filepath: str, ip: str = socket.gethostname(), port: int = 25567, listen: int = 5,
              recv_buffer: int = 2048, handle_client=None, on_connect=None, on_disconnect=None, on_receive=None):

        if on_connect is None:
            on_connect = self.__on_connect

        if on_disconnect is None:
            on_disconnect = self.__on_disconnect

        self.filepath = filepath

        super().setup(ip, port, listen, recv_buffer, handle_client, on_connect=on_connect,
                      on_disconnect=on_disconnect, on_receive=on_receive)

    def __on_connect(self, address):
        def spread_keys(ip, port):
            address_ = (ip, port)
            clients_keys_to_send = str(self.__to_send_client_keys.copy()).encode()
            clients = self.clients.copy()
            users = self.users.copy()
            client_keys = self.__client_keys.copy()
            for address, username in users.items():

                if address == address_:
                    continue

                client_socket_ = clients.get(address)[1]
                try:
                    self.send_data(target=b'Server', type=b'keys', data=clients_keys_to_send,
                                   key=client_keys.get(username), client_socket=client_socket_)
                except Exception:
                    self.clients.pop(address)
                    self.__client_keys.pop(username)
                    self.__to_send_client_keys.pop(username)

        t = threading.Thread(target=spread_keys, args=(address), daemon=True)

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
            t.start()

            self.__client_keys[user] = cipher.import_asym_key(public_key)
            self.__to_send_client_keys[user] = public_key
            self.users[address] = user
            time.sleep(0.05)
            to_send_keys = self.__to_send_client_keys.copy()
            client_keys = b''
            for user, key in to_send_keys.items():
                client_keys = client_keys + user.encode() + b'user-key' + key + b'!!next!!'
            self.send_data(target=b'Client', type=b'keys', data=client_keys, username=user)

        else:
            self.send_data(target=b'Client', type=b'Rejected', data=b'Rejected',
                           key=cipher.import_asym_key(public_key), client_socket=client_socket)
            self.clients.pop(address)
            self.__allthreads.pop(address)
            self.disconnect(client_socket)

    def __on_disconnect(self, address):
        def spread_keys(ip, port):
            address_ = (ip, port)
            clients_keys_to_send = str(self.__to_send_client_keys.copy()).encode()
            clients = self.clients.copy()
            users = self.users.copy()
            client_keys = self.__client_keys.copy()
            for address, username in users.items():

                if address == address_:
                    continue

                client_socket_ = clients.get(address)[1]
                try:
                    self.send_data(target=b'Server', type=b'keys', data=clients_keys_to_send,
                                   key=client_keys.get(username), client_socket=client_socket_)
                except Exception:
                    self.clients.pop(address)
                    self.__client_keys.pop(username)
                    self.__to_send_client_keys.pop(username)

        username = self.users.pop(address)
        self.__client_keys.pop(username)
        self.__to_send_client_keys.pop(username)
        print(f"User {username} disconnected")
        t = threading.Thread(target=spread_keys, args=(address), daemon=True)
        t.start()

    def load_users(self, get: str = None) -> dict:  # json
        with open(self.filepath, 'r') as file:
            loaded = json.loads(file.read())
        if get is None:
            return loaded
        else:
            return loaded.get(get)

    def save_users(self, users: dict, get: str = None):  # json
        with open(self.filepath, 'r') as file:
            read_: dict = json.loads(file.read())

        if get is not None:
            read_[get] = users
        else:
            read_ = users

        with open(self.filepath, 'w') as file:
            json.dump(read_, file, indent=self.indent)

    def add_user(self, username: str, pw: str, get: str = None):
        users = self.load_users(get)
        hashed_pw = cipher.gen_hash(pw)
        users[username] = hashed_pw
        self.save_users(users, get)

    def check_user(self, username: str, pw: str, get: str = None) -> bool:  # pw not hashed already
        users = self.load_users(get)
        actual_pw = users.get(username)
        if actual_pw is None:
            return False
        return cipher.compare_hash(pw, actual_pw)

    def get_address_by_user(self, user: str) -> tuple:
        return list(self.users.keys())[list(self.users.values()).index(user)]

    def get_public_key(self, username: str):
        return self.__client_keys.get(username)

    def recv_data(self, client_socket: socket.socket) -> tuple:
        recv: bytes = super().recv_data(client_socket)
        type, rest = recv.split(self.seperators[0])
        target, data = rest.split(self.seperators[1])

        # Decrypt
        type = cipher.decrypt_asym(type, self.own_keys[0])
        target = cipher.decr_data(target, prkey=self.own_keys[0], output="bytes")

        return (target, type, data)

    def send_data(self, target: bytes, type: bytes, data: bytes, username: str = None, key=None,
                  client_socket :socket.socket = None, encr_data: bool = True) -> bool:

        if key is not None and client_socket is not None and username is None:
            pass
        elif key is None and client_socket is None and username is not None:
            key = self.__client_keys.get(username)
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
        return self.__to_send_client_keys.copy()
