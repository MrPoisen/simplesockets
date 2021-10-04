# Introduction  
This library allows to easily create TCP Servers and Clients using Python sockets

If you want a secure connection, use the secure variant `securesockets`. It uses the 
[pycryptodome](https://pypi.org/project/pycryptodome/) library. It should be clear, that you need to install said library to use 
the secure variant.  
If you have encountered a bug or have an idea, share it on [github](https://github.com/MrPoisen/simplesockets). For more help look 
up the [docs](https://mrpoisen.github.io/simplesockets/)
(Note: They may be incomplete)

# Installation
use `pip install simplesockets` to install this library.

# Examples
This package also contains an example, an echo Server and Client:

echoclient.py
```` python

if __name__ == "__main__":
    from simplesockets import TCPClient

    Client = TCPClient()
    Client.setup(target_ip="localhost", target_port=25567)  # prepares the Client
    Client.connect()  # connects the Client to the Server

    Client.autorecv()  # enables autorecv: automatically saves all incoming data in Client.recved_data,
    # return them with Client.return_recved_data()

    Client.send_data(b'Test')  # sends the text to the Server
    while True:
        if Client.event.new_data:  # checks if any data received
            data: list = Client.return_recved_data()  # returns the received data as a list
            for element in data:
                print(element.response)  # should print b'Test'
            break  # ends the while loop
````

echoserver.py
```` python

if __name__ == "__main__":
    from simplesockets import TCPServer

    Server = TCPServer()
    Server.setup(ip='127.0.0.1', port=25567)  # prepares the server
    Server.start()  # starts the server

    while True:
        if Server.event.new_data:  # checks if any data received
            data: list = Server.return_recved_data()  # returns the received data as a list
            for element in data:
                response: bytes = element.response  # element is a Socket_Response object,
                client = element.from_  # sets client to a Server_Client object
                Server.send_data(response, client)
````