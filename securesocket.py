import socket
import threading
import time
import traceback
import uuid


class TCPClient_secure:
    def __init__(self, key_length=2048):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.recved_data = []
        self.__autorecv = False
        self.__autorecv_thread = threading.Thread(target=self.__reciving_automatic)
        self.is_connected = False

        self.new_data_recved = False

        self.exception = False
        self.__all_exceptions = []

        from support_files import cipher
        self.__cipher = cipher
        private, public = self.__cipher.gen_asym_keys(key_length)
        self.own_keys = [private, public]  # private, public
        self.__keys_by_synonym = {}

        self.__public_server_key = None

        self.id = None

        self.types = ["keys_by_id", "file", "msg"]

        self.seperators = [b'prefixuHOCvqQjMf', b'type_targ_sepLnpEwEljZi', b'targ_data_sepcLkGqydgGY']

        self.__allthreads = [self.__autorecv_thread]

        self.__target_ip = None
        self.__target_port = None
        self.__recv_buffer = None

        self.__start_target = None

    def setup(self, target_ip, target_port=25567, recv_buffer=2048):
        self.__target_ip = target_ip
        self.__target_port = target_port
        self.__recv_buffer = recv_buffer

    def reconnect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect()

    def return_public_server_key(self):
        return self.__public_server_key

    def connect(self):
        try:
            self.socket.connect((self.__target_ip, self.__target_port))
            self.is_connected = True
            self.send_data(self.__cipher.export_asym_key(self.own_keys[1]))
            self.__public_server_key = self.__cipher.import_asym_key(self.recv_data())
            self.id = self.__cipher.decr_data(self.recv_data(), self.own_keys[0], output="bytes")

        except Exception as e:
            self.__all_exceptions.append((traceback.format_exc(), e))
            self.exception = True

    def send_data(self, data: bytes):
        if self.seperators[0] not in data:  # if b'prefixuHOCvqQjMf' not in data
            data = b'unsecure' + self.seperators[0] + data

        data_length = len(data)
        sended_length = 0
        while sended_length < data_length:
            sent = self.socket.send(data[sended_length:])
            if sent == 0:
                self.__all_exceptions.append(RuntimeError("socket connection error"))
                self.exception = True
            sended_length += sent

    def send_secure_data(self, data: bytes, type: str, target: bytes, public_key, encrypt_data: bool = False):
        if type not in self.types:
            return False
        prefix = b"secure"
        if encrypt_data:
            data = self.__cipher.encr_data(data, public_key)
        type = self.__cipher.encr_data(type.encode(), self.__public_server_key)
        target = self.__cipher.encr_data(target, self.__public_server_key)
        data = prefix + self.seperators[0] + type + self.seperators[1] + target + self.seperators[2] + data
        self.send_data(data)
        return True

    def decrypt_data(self, data: bytes):
        prefix, rest = data.split(self.seperators[0])
        if prefix is b'unsecure':
            return rest
        type, rest = rest.split(self.seperators[1])
        target, data = rest.split(self.seperators[2])
        type = self.__cipher.decr_data(type, self.own_keys[0])
        target = self.__cipher.decr_data(target, self.own_keys[0], output="bytes")
        data = self.__cipher.decr_data(data, self.own_keys[0], output="bytes")
        return (type, target, data)

    def return_recved_data(self):
        self.new_data_recved = False
        data = self.recved_data.copy()
        self.recved_data = []
        return data

    def __reciving_automatic(self):
        while self.__autorecv:
            try:
                recved = self.recv_data()
                if len(recved) > 0:
                    print("SOme data recved")
                    if b'keys_by_id' in recved:
                        recved = recved.replace(b'keys_by_id', b'')
                        self.__keys_by_synonym = dict(eval(recved.decode()))
                        continue
                    self.recved_data.append(recved)
                    self.new_data_recved = True

            except Exception as e:
                self.__all_exceptions.append((traceback.format_exc(), e))
                self.exception = True
                self.is_connected = False

    def autorecv(self):
        if self.__autorecv is False:
            self.__autorecv = True
            self.__autorecv_thread.start()

    def shutdown(self):
        self.__autorecv = False
        self.__autorecv_thread = threading.Thread(target=self.__reciving_automatic)
        self.socket.close()

    def recv_data(self):
        chunks = []
        recv_data = True
        while recv_data:
            chunk = self.socket.recv(self.__recv_buffer)
            chunks.append(chunk)
            if len(chunk) < self.__recv_buffer:
                recv_data = False

        return b''.join(chunks)

    def return_exceptions(self, delete=True, reset_exceptions=True):
        exceptions = self.__all_exceptions.copy()
        if delete:
            self.__all_exceptions = []
        if reset_exceptions:
            self.exception = False
        return exceptions

    def exit(self):
        for thread in self.__allthreads:
            thread.join()


class TCPServer_secure:

    def __init__(self, max_connections=None, key_length=2048):
        self.run = True
        self.__kill = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = {}  # key: address, value : [client_thread,client_socket]
        self.__recv_buffer = 2048

        self.__accepting_thread = threading.Thread(target=self.__accept_clients)

        self.recved_data = []

        self.new_data_recved = False

        self.__all_exceptions = []
        self.exception = False

        self.max_connections = max_connections

        from support_files import cipher
        self.__cipher = cipher
        private, public = self.__cipher.gen_asym_keys(key_length)
        self.own_keys = [private, public]
        self.__keys = {}
        self.__keys_by_synonym = {}
        self.__special_keys_by_synonym = {}

        self.__addr_by_id = {}

        self.types = ["keys_by_id", "file", "msg"]

        self.seperators = [b'prefixuHOCvqQjMf', b'type_targ_sepLnpEwEljZi', b'targ_data_sepcLkGqydgGY']

        self.__allthreads = {None: self.__accepting_thread}

        self.__recv_buffer = None

        self.__start_target = None

    # Prepares the Server
    def setup(self, ip=socket.gethostname(), port=25567, listen=5, recv_buffer=2048, handle_client=None):
        self.socket.bind((ip, port))
        self.socket.listen(listen)
        self.__recv_buffer = recv_buffer

        if handle_client is not None:
            self.__start_target = handle_client
        else:
            self.__start_target = self.__handle_client

        self.__accepting_thread.start()  # starts the accepting thread while the while loop is still false

    def add_types(self, types: list):
        self.types.extend(types)

    def return_key_by_addr(self, addr):
        return self.__keys.get(addr)

    def return_key_by_id(self, id):
        return self.__keys_by_synonym.get(id)

    # Sends bytes to a target
    def send_data(self, data: bytes, client_socket):
        data_length = len(data)
        sended_length = 0
        while sended_length < data_length:
            sent = client_socket.send(data[sended_length:])
            if sent == 0:
                self.__all_exceptions.append(RuntimeError("socket connection error"))
                self.exception = True

            sended_length += sent

    # recv data from a target
    def recv_data(self, client_socket):
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

    def send_secure_data(self, data: bytes, type: str, target: bytes, public_key, client_socket):
        if type not in self.types:
            return False
        prefix = b"secure"
        data = self.__cipher.encr_data(data, public_key)
        type = self.__cipher.encr_data(type.encode(), public_key)
        target = self.__cipher.encr_data(target, public_key)
        data = prefix + self.seperators[0] + type + self.seperators[1] + target + self.seperators[2] + data
        self.send_data(data, client_socket)
        return True

    def decrypt_data(self, data: bytes):
        prefix, rest = data.split(self.seperators[0])
        if prefix is b'unsecure':
            return rest
        type, rest = rest.split(self.seperators[1])
        target, data = rest.split(self.seperators[2])
        type = self.__cipher.decr_data(type, self.own_keys[0])
        target = self.__cipher.decr_data(target, self.own_keys[0], output="bytes")
        return (type, target, data)

    # returns all received data and clears self.recved_data and sets new_data_recved to False
    def return_recved_data(self):
        self.new_data_recved = False
        data = self.recved_data.copy()
        self.recved_data = []
        return data

    def __key_management(self):
        for client in self.clients.values():
            try:
                self.send_data((b'keys_by_id' + str(self.__special_keys_by_synonym).encode()), client[1])
            except Exception as e:
                self.exception = True
                self.__all_exceptions.append([traceback.format_exc(), e])

    # handles the connection
    def __handle_client(self, client_socket, address):
        try:
            client_public_key = self.recv_data(client_socket)  # gets public key in bytes

            client_public_key = client_public_key[8:]  # removes b'unsecure'

            self.__keys[address] = self.__cipher.import_asym_key(client_public_key)  # imports and saves key to address

            self.send_data(self.__cipher.export_asym_key(self.own_keys[1]), client_socket)  # sends server key

            id = str(uuid.uuid4())
            self.__keys_by_synonym[id] = self.__cipher.import_asym_key(client_public_key)
            self.__special_keys_by_synonym[id] = client_public_key
            self.__addr_by_id[id] = address
            self.send_data(self.__cipher.encr_data(id, self.__cipher.import_asym_key(client_public_key)), client_socket)

            t = threading.Thread(target=self.__key_management)
            t.start()  # sends all public keys by synonym to the clients

            while True:
                recved = self.recv_data(client_socket)
                if len(recved) > 0:
                    self.new_data_recved = True
                    self.recved_data.append((client_socket, address, recved))

        except Exception as e:
            self.__all_exceptions.append((traceback.format_exc(), e))
            self.exception = True

            self.clients.pop(address)
            self.__keys.pop(address)
            self.__keys_by_synonym.pop(id)
            self.__addr_by_id.pop(id)
            self.__special_keys_by_synonym.pop(id)
            self.__allthreads.pop(address)

            if self.max_connections is not None and len(self.clients) < self.max_connections:
                self.run = True

    def __accept_clients(self):
        while self.__kill is False:
            time.sleep(2)
            while self.run:
                print("while_accepting")
                client_socket, address = self.socket.accept()
                print("accepted connection")
                ct = threading.Thread(target=self.__start_target, args=(client_socket, address))
                self.clients[address] = [ct, client_socket]

                self.__allthreads[address] = ct

                ct.start()

                if self.max_connections is not None and len(self.clients) >= self.max_connections:
                    self.run = False

    # starts the server
    def start(self):
        self.run = True

    # stops the server
    def stop(self):
        self.run = False

    def shutdown(self):
        self.__kill = True

    def restart(self):
        if self.__kill:
            self.__kill = False
            self.__accepting_thread = threading.Thread(target=self.__accept_clients)
            self.__accepting_thread.start()

        elif self.__kill is False:
            raise Exception("Can't restart stopped or running thread")

    def killed(self):
        return self.__kill

    def disconnect(self, addr):
        def get_key(dictionary: dict, value):
            return list(dictionary.keys())[list(dictionary.values()).index(value)]

        client_socket = self.clients.pop(addr)[1]
        id = get_key(self.__addr_by_id, addr)
        self.__keys.pop(addr)
        self.__special_keys_by_synonym.pop(id)
        self.__keys_by_synonym.pop(id)
        thread = self.__allthreads.pop(addr)
        client_socket.close()
        thread.join()

    def return_exceptions(self, delete=True, reset_exception=True):
        exceptions = self.__all_exceptions.copy()
        if delete:
            self.__all_exceptions = []
        if reset_exception:
            self.exception = False
        return exceptions

    def exit(self):
        for thread in self.__allthreads:
            thread.join()

    def get_prefix(self, data: bytes):
        if self.seperators[0] not in data:
            return None
        prefix, rest = data.split(self.seperators[0])
        return (prefix, rest)
