from simplesockets._support_files import cipher
from simplesockets.simplesockets import TCPClient

class Client_(TCPClient):
    def __init__(self):
        super().__init__()
        self.user = ""
        self.pw = ""

        self.seperators = [b'type_targ_sepLnpEwEljZi', b'targ_data_sepcLkGqydgGY']

        private, public = cipher.gen_asym_keys()
        self.own_keys = [private, public] #0:private, 1:public

        self.server_key = None
        self.users_keys = {} #Key: username, value: public key

        self.__first_keys = True

    @property
    def connected_users(self):
        return list(self.users_keys.keys())

    def setup(self, target_ip: str, target_port: int = 25567, recv_buffer: int = 2048, on_connect=None,
              on_disconnect=None, on_receive=None):
        '''
        function sets up the Client

        :param target_ip: IP the Client should connect to
        :param target_port: PORT the Client should connect to
        :param recv_buffer: the receive buffer used for socket.recv()
        :param on_connect: function that will be executed on connection, it takes not arguments
        :param on_disconnect: function that will be executed on disconnection, it takes no arguments
        :param on_receive: function that will be executed on receive, it takes the received data as an argument
        '''
        if on_connect is None:
            on_connect = self.on_connect

        super().setup(target_ip, target_port, recv_buffer, on_connect, on_disconnect, on_receive)

    def connect(self, user: str, pw: str) -> bool:
        '''
        function tries to connect

        :param user: username
        :param pw: password
        :return: returns True if connecting was successful
        '''
        self.user = user
        self.pw = pw
        return super().connect()

    def on_connect(self) -> bool:
        '''
        this function is executed on connection
        '''
        # Exchange
        recved = super().recv_data()
        self.server_key = cipher.import_asym_key(recved)
        self.send_data(target=b'Server', type=b'key', data=cipher.export_asym_key(self.own_keys[1]), key=self.server_key)

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
                        keys[user.decode()] = cipher.import_asym_key(key)
                self.users_keys = keys.copy()
            except Exception as e:
                print(e)
            return True

    def recv_data(self) -> tuple:
        '''
        function collects all incoming data

        :return: tuple, first the target, second the type, third the data
        '''
        recv:bytes = super().recv_data()
        type, rest = recv.split(self.seperators[0])
        target, data = rest.split(self.seperators[1])

        #Decrypt
        type = cipher.decrypt_asym(type, self.own_keys[0])
        target = cipher.decr_data(target, prkey=self.own_keys[0], output="bytes")
        data = cipher.decr_data(data, prkey=self.own_keys[0], output="bytes")

        return (target, type, data)

    def send_data(self, target: bytes, type: bytes, data: bytes, username: str = None, key=None) -> bool:
        '''
        function sends encrypted data to a user or socket

        :param target: information used for target
        :param type: information used for type
        :param data: data to send
        :param username: the username of the user to send, if not given, you must give a key
        :param key: the RSA Public Key used for encryption,  if not given, you must give an username
        :return: returns True if the sending was successful
        '''
        if key is not None and username is None:
            pass
        elif key is None and username is not None:
            key = self.users_keys.get(username)
        else:
            return False

        if key is None:
            return False

        target = cipher.encr_data(target, self.server_key)
        type = cipher.encrypt_asym(type, self.server_key)
        data = cipher.encr_data(data, key)

        to_send = type + self.seperators[0] + target + self.seperators[1] + data
        return super().send_data(to_send)

    def get_key(self, username:str):
        '''
        function returns a key for a username

        :param username: username used for finding the key
        :return: returns a RSA Public key
        '''
        return self.users_keys.get(username)
