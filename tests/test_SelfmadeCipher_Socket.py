from simplesockets.securesockets.SelfmadeCipher_Socket import SecureServer, SecureClient


def test_simple_data_exchange():
    Client = SecureClient()
    Server = SecureServer()

    def send(clientsocket, address, data):
        Server.send_data(data[0],data[1], data[2], client_socket=clientsocket, encr_data=False, encr_rest=False)

    on_connect = lambda *args: print("!!on_connect", args)
    on_receive = lambda *args: print("!!on_receive",args)
    #on_disconnect = lambda *args: print("Callled on_disconnect") #print("!!on_disconnect",args)

    Server.setup(on_receive=send, on_connect=on_connect)
    Client.setup("localhost", on_connect=on_connect, on_receive=on_receive)

    Server.start()
    #Server.

    Client.login_data("Test", "Test")
    Client.connect()
    Client.autorecv()

    text = b'Does this work?'

    Client.send_data(Client.user.encode(), b"test", text, key=Client.own_keys[1], encr_rest=False)

    event, value = Client.await_event(disable_on_functions=True, timeout=3000)

    Client.close()
    Server.close()

    if event == Client.EVENT_EXCEPTION or event == Client.EVENT_DISCONNECT:
        print(value, Client.return_exceptions())

    assert event == Client.EVENT_RECEIVED and value[0][2] == text

def test_less_simple_data_exchange():
    Client = SecureClient()
    Server = SecureServer()

    def send(clientsocket, address, data):
        Server.send_data(data[0], data[1], data[2], client_socket=clientsocket, key=Client.own_keys[1], encr_data=False, encr_rest=True)

    on_connect = lambda *args: print("!!on_connect", args)
    on_receive = lambda *args: print("!!on_receive", args)
    # on_disconnect = lambda *args: print("Callled on_disconnect") #print("!!on_disconnect",args)

    Server.setup(on_receive=send, on_connect=on_connect)
    Client.setup("localhost", on_connect=on_connect, on_receive=on_receive)

    Server.start()
    # Server.

    Client.login_data("Test", "Test")
    Client.connect()
    Client.autorecv()

    Client.server_key = Server.own_keys[1]  # normally, this Server key will be exchanged on the on_connect_function

    text = b'Does this work?'

    Client.send_data(Client.user.encode(), b"test", text, key=Client.own_keys[1], encr_rest=True)

    event, value = Client.await_event(disable_on_functions=True, timeout=3000)

    Client.close()
    Server.close()

    if event == Client.EVENT_EXCEPTION or Client.EVENT_DISCONNECT:
        print(value, Client.return_exceptions())

    assert event == Client.EVENT_RECEIVED and value[0][2] == text