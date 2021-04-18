from simplesockets._support_files import RSA, b_veginer
from simplesockets.simplesockets import TCPClient, TCPServer
from simplesockets._support_files import cipher

import socket, time, json


class Client_(TCPClient):
    def __init__(self):
        super().__init__()
        self.user = ""
        self.pw = ""

        self.seperators = [b'type_targ_sepLnpEwEljZi', b'targ_data_sepcLkGqydgGY']

        private = RSA.get_private_key()
        public = private.public_key()
        self.own_keys = [private, public] #0:private, 1:public

        self.server_key: RSA.RSA_Public_Key = None
        self.users_keys = {} #Key: username, value: public key

        self.__first_keys = True

    @property
    def connected_users(self):
        return list(self.users_keys.keys())

    def __enrcypt_data(self, data: bytes, key: RSA.RSA_Public_Key) -> bytes:
        pad = b_veginer.Pad(b_veginer.get_key())
        encrypted = pad.encrypt(data)
        encr_key = key.encrypt(pad.bytes, 1)
        return b''.join([encrypted, b'$$$$', encr_key])

    def __decypt_data(self, data: bytes, prkey: RSA.RSA_Private_Key) -> bytes:
        pad, enrcypted = data.split(b'$$$$')
        pad = prkey.decrypt(pad, 1)
        pad = b_veginer.import_pad(pad)
        return pad.decrypt(enrcypted)

    def setup(self, target_ip: str, target_port: int = 25567, recv_buffer: int = 2048, on_connect=None,
              on_disconnect=None, on_receive=None):

        if on_connect is None:
            on_connect = self.on_connect

        super().setup(target_ip, target_port, recv_buffer, on_connect, on_disconnect, on_receive)

    def connect(self, user: str, pw: str) -> bool:
        self.user = user
        self.pw = pw
        return super().connect()

    def on_connect(self) -> bool:
        # Exchange
        recved = super().recv_data()
        self.server_key = RSA.import_key(recved)
        self.send_data(target=b'Server', type=b'key', data=self.own_keys[1].unofficial_export(), key=self.server_key)

        #Login

        login = self.user.encode() + b'%|%' + self.pw.encode()
        self.send_data(b'Server', b'login', login, key=self.server_key)
        target, type, data = self.recv_data()

        if type == b'Rejected':
            self.socket.close()
            return False

        if type == b'keys':
            if self.__first_keys:
                self.__first_key = False
            keys = {}
            try:
                pairs = data.split(b'!!next!!')
                for pair in pairs:
                    if len(pair) > 0:
                        user, key = pair.split(b'user-key')
                        keys[user.decode()] = RSA.import_key(key)
                self.users_keys = keys.copy()
            except Exception as e:
                print(e)
            return True

    def recv_data(self):
        recv:bytes = super().recv_data()
        type, rest = recv.split(self.seperators[0])
        target, data = rest.split(self.seperators[1])

        #Decrypt
        type = self.own_keys[0].decrypt(type, 1)
        target = self.__decypt_data(target, self.own_keys[0]).decode()
        data = self.__decypt_data(data, self.own_keys[0])

        return (target, type, data)

    def send_data(self, target: bytes, type: bytes, data: bytes, username:str=None, key=None) -> bool:

        if key is not None and username is None:
            pass
        elif key is None and username is not None:
            key = self.users_keys.get(username)
        else:
            return False

        if key is None:
            return False

        target = self.__enrcypt_data(target, self.server_key)
        type = self.server_key.encrypt(type, 1)
        data = self.__enrcypt_data(data, key)

        to_send = type + self.seperators[0] + target + self.seperators[1] + data
        return super().send_data(to_send)

    def get_key(self, username:str):
        return self.users_keys.get(username)


class Server_(TCPServer):
    def __init__(self, max_connections=None):
        super().__init__(max_connections)
        self.users = {}  # Key: address, value: username

        private = RSA.get_private_key()
        public = private.public_key()

        self.own_keys = [private, public]  # 0 is private, 1 is public
        self.__client_keys = {}  # Key: username, value: public key
        self.to_send_client_keys = {}  # Key: username, value: public key as bytes

        self.seperators = [b'type_targ_sepLnpEwEljZi', b'targ_data_sepcLkGqydgGY']

        self.filepath = None

        self.indent = 4

    def __enrcypt_data(self, data: bytes, key: RSA.RSA_Public_Key) -> bytes:
        pad = b_veginer.Pad(b_veginer.get_key())
        encrypted = pad.encrypt(data)
        encr_key = key.encrypt(pad.bytes, 1)
        return b''.join([encrypted, b'$$$$', encr_key])

    def __decypt_data(self, data: bytes, prkey: RSA.RSA_Private_Key) -> bytes:
        pad, enrcypted = data.split(b'$$$$')
        pad = prkey.decrypt(pad, 1)
        pad = b_veginer.import_pad(pad)
        return pad.decrypt(enrcypted)

    def setup(self, filepath: str, ip: str = socket.gethostname(), port: int = 25567, listen: int = 5,
              recv_buffer: int = 2048, handle_client=None, on_connect=None, on_disconnect=None, on_receive=None):

        if on_connect is None:
            on_connect = self.on_connect

        if on_disconnect is None:
            on_disconnect = self.on_disconnect

        self.filepath = filepath

        super().setup(ip, port, listen, recv_buffer, handle_client, on_connect=on_connect,
                      on_disconnect=on_disconnect, on_receive=on_receive)

    def on_connect(self, address):

        # exchange keys
        client_socket = self.clients.get(address)[1]
        super().send_data(self.own_keys[1].unofficial_export(), client_socket=client_socket)
        target, type_, data = self.recv_data(client_socket)
        public_key: bytes = (self.__decypt_data(data, self.own_keys[0]))
        # login

        target, type_, login_data = self.recv_data(client_socket)
        login_data = self.__decypt_data(login_data, self.own_keys[0]).decode()
        user, pw = login_data.split('%|%')
        check = self.check_user(user, pw)

        if check:

            self.__client_keys[user] = RSA.import_key(public_key)
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
                           key=RSA.import_key(public_key), client_socket=client_socket)
            self.disconnect(address)

    def on_disconnect(self, address):
        username = self.users.pop(address)
        self.__client_keys.pop(username)
        self.to_send_client_keys.pop(username)

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
        type = self.own_keys[0].decrypt(type, 1)
        target = self.__decypt_data(target, self.own_keys[0])

        return (target, type, data)

    def send_data(self, target: bytes, type: bytes, data: bytes, username: str = None, key=None,
                  client_socket :socket.socket = None, encr_data: bool = True) -> bool:

        if key is not None and client_socket is not None and username is None:
            pass
        elif key is None and client_socket is None and username is not None:
            key: RSA.RSA_Public_Key = self.__client_keys.get(username)
            client_socket = self.clients.get(self.get_address_by_user(username))[1]
        else:
            self.event.exception.occurred = True
            self.event.exception.list.append((Exception("You must give an username or key and clientsocket")))
            return False

        target = self.__enrcypt_data(target, key)
        type = key.encrypt(type, 1)
        if encr_data:
            data = self.__enrcypt_data(data, key)

        to_send = type + self.seperators[0] + target + self.seperators[1] + data
        return super().send_data(to_send, client_socket)

    def get_client_keys(self):
        return self.to_send_client_keys.copy()

    def decrypt_data(self, data: bytes):
        return self.__decypt_data(data, self.own_keys[0])