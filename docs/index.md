# Welcome to simplesockets

This is the simplesockets documentation. Here, you can learn how to use 
[this](https://github.com/MrPoisen/simplesockets) library.  

If you want to use the "unsecure" variant, use ``simplesockets``  
If you want to use the "secure" variant, use `securesockets`. For this one, you will need 
[pycryptodome](https://pypi.org/project/pycryptodome/) if you need real security. If you just need increased security, 
use [this](Selfmade_Crypto_Socket-reference.md) one. For more information, read [here](Securesockets_selfwritten.md)  

Here you can learn more about the [``simplesockets``](simple_sockets_selfwritten.md)
Here you can learn more about the [`securesockets`](Securesockets_selfwritten.md)

If you need an example, you can find one in the example folder.

## Installation  

For installation, write on the command prompt:  
`pip install simplesockets`  
Now, you can use this library.  

## Example  

If you want a simple echo Client, it could look something like this:

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

A simple echo Server could look something like this:
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
                data: bytes = element.response  # element is a Socket_Response object,
                client = element.from_  # sets client to a Server_Client object
                Server.send_data(data, client)
````

If you encounter any bugs, report them on [github](https://github.com/MrPoisen/simplesockets)

Should you be interested in the changelog, you can find it [here](Changelog.md)