import socket
import threading
import time
import traceback


class TCPClient:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.recved_data = []
        self.__autorecv = False
        self.__autorecv_thread = threading.Thread(target=self.__reciving_automatic)
        self.is_connected = False

        self.new_data_recved = False

        self.exception = False
        self.__all_exceptions = []

        self.__allthreads = [self.__autorecv_thread]

        self.__target_ip = None
        self.__target_port = None
        self.__recv_buffer = None

        self.__start_taregt = None

    def setup(self, target_ip, target_port=25567, recv_buffer=2048):
        self.__target_ip = target_ip
        self.__target_port = target_port
        self.__recv_buffer = recv_buffer

    def reconnect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect()

    def connect(self):
        try:
            self.socket.connect((self.__target_ip, self.__target_port))
            self.is_connected = True
            # self.socket.setblocking(False)

        except Exception as e:
            self.__all_exceptions.append((traceback.format_exc(), e))
            self.exception = True

    def send_data(self, data: bytes):
        data_length = len(data)
        sended_length = 0
        while sended_length < data_length:
            sent = self.socket.send(data[sended_length:])
            if sent == 0:
                self.__all_exceptions.append(RuntimeError("socket connection error"))
                self.exception = True
                return False
            sended_length += sent
        return True

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
        for number, thread in enumerate(self.__allthreads):
            try:
                thread.join()
            except Exception:
                self.__allthreads.pop(number)


class TCPServer:

    def __init__(self, max_connections=None):
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

        self.__allthreads = {None: self.__accepting_thread}

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

    # Sends bytes to a target
    def send_data(self, data: bytes, client_socket):
        data_length = len(data)
        sended_length = 0
        while sended_length < data_length:
            sent = client_socket.send(data[sended_length:])
            if sent == 0:
                self.__all_exceptions.append(RuntimeError("socket connection error"))
                self.exception = True
                return False

            sended_length += sent
        return True

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

    # returns all received data and clears self.recved_data and sets new_data_recved to False
    def return_recved_data(self):
        self.new_data_recved = False
        data = self.recved_data.copy()
        self.recved_data = []
        return data

    # handles the connection
    def __handle_client(self, client_socket, address):
        try:
            while True:
                recved = self.recv_data(client_socket)
                if len(recved) > 0:
                    self.new_data_recved = True
                    self.recved_data.append((client_socket, address, recved))

        except Exception as e:
            self.__all_exceptions.append((traceback.format_exc(), e))
            self.exception = True

            self.clients.pop(address)
            self.__allthreads.pop(address)

            if self.max_connections is not None and len(self.clients) < self.max_connections:
                self.run = True

    def __accept_clients(self):
        while self.__kill is False:
            time.sleep(2)
            while self.run:
                # print("while_accepting")
                client_socket, address = self.socket.accept()
                # print("accepted connection")
                ct = threading.Thread(target=self.__start_target, args=(client_socket, address))
                self.clients[address] = [ct, client_socket]
                ct.start()

                self.__allthreads[address] = ct  # add thread to all threads dict

                if self.max_connections is not None and len(self.clients) >= self.max_connections:
                    self.run = False
                # client_socket.setblocking(False)

    # starts the server
    def start(self):
        self.run = True

    # stops the server
    def stop(self):
        self.run = False

    def restart(self):
        if self.__kill:
            self.__kill = False
            self.__accepting_thread = threading.Thread(target=self.__accept_clients)
            self.__accepting_thread.start()

        elif self.__kill is False:
            raise Exception("Can't restart stopped or running thread")

    def killed(self):
        return self.__kill

    @staticmethod
    def disconnect(client_socket):
        client_socket.close()

    def return_exceptions(self, delete=True, reset_exception=True):
        exceptions = self.__all_exceptions.copy()
        if delete:
            self.__all_exceptions = []
        if reset_exception:
            self.exception = False

        return exceptions

    def exit(self):
        for thread in self.__allthreads.values():
            thread.join()
        self.__kill = True

    def shutdown(self):
        self.__kill = True
