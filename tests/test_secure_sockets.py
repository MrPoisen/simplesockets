import simplesockets.secure_sockets as s

def test_data_exchange():

    Client = s.SecureClient()
    Server = s.SecureServer(1)

    pr = lambda client, data: client.send(data.response)
    on_connect = lambda *args: print("connect", args)
    on_receive = lambda *args: print(args) if len(args) > 0 else None
    on_disconnect = lambda *args: print(args) if len(args) > 0 else None

    Server.setup(on_receive=pr, on_connect=on_connect, on_disconnect=on_disconnect)
    Client.setup("localhost", on_connect=on_connect, on_receive=on_receive, on_disconnect=on_disconnect)
    Server.start()
    Client.connect()

    Client.autorecv()

    text = b'test'

    Client.send_data(text)

    event, value = Client.await_event(disable_on_functions=True, timeout=3000)

    Client.close()
    Server.close()
    if Server.event.exception.occurred:
        print(Server.return_exceptions())

    assert event == Client.EVENT_RECEIVED and value[0].response == text

def test_reconnect():
    Client = s.TCPClient()
    Server = s.TCPServer(1)

    Server.setup()
    Client.setup("localhost")

    Server.start()
    Client.reconnect()

    assert Client.event.connected is True
