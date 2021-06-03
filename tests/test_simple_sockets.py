import simplesockets.simple_sockets as s


def test_data_exchange():

    Client = s.TCPClient()
    Server = s.TCPServer(1)

    pr = lambda clientsocket, address, data: Server.send_data(data, clientsocket)
    on_connect = lambda *args: print("connect", args)
    on_receive = lambda *args: print(args)
    on_disconnect = lambda *args: print(args)

    Server.setup(on_receive=pr, on_connect=on_connect, on_disconnect=on_disconnect)
    Client.setup("localhost", on_connect=on_connect, on_receive=on_receive, on_disconnect=on_disconnect)
    Server.start()
    Client.connect()

    Client.autorecv()

    text = b'test'

    Client.send_data(text)

    event, value = Client.await_event(disable_on_functions=True)

    Client.close()
    Server.close()

    assert event == Client.EVENT_RECEIVED and value[0] == text

def test_reconnect():
    Client = s.TCPClient()
    Server = s.TCPServer(1)

    Server.setup()
    Client.setup("localhost")

    Server.start()
    Client.reconnect()

    assert Client.event.connected is True
