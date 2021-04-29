This library allows to easily create TCP Servers and Clients using Python sockets

If you want a secure connection, use the secure variant `securesockets`. It uses the 
[pycryptodome](https://pypi.org/project/pycryptodome/) library. It should be clear, that you need to install said 
library to use the secure variant.  
If you have encountered a bug or have an idea, share it on [github](https://github.com/MrPoisen/simplesockets). For 
more help look up the [docs](https://mrpoisen.github.io/simplesocketsdocs/)  
This package also contains an example, an echo Server and Client:

echoclient.py
```` python

if __name__ == "__main__":
    from simplesockets.simplesockets import TCPClient
    
    Client = TCPClient()
    Client.setup(target_ip="localhost", target_port=25567) #prepares the Client
    Client.connect() #connects the Client to the Server
    
    Client.autorecv()   #enables autorecv: automaticle saves all incoming data in Client.recved_data,
                        # return them with Client.return_recved_data()
    
    Client.send_data(b'Test') #sends the text to the Server
    while True:
        if Client.event.new_data: #checks if any data recved
            data = Client.return_recved_data() #returns the recved data as a list
            for element in data:
                print(element) #should return b'Test'
````

echoserver.py
```` python

if __name__ == "__main__":
    from simplesockets.simplesockets import TCPServer
    
    Server = TCPServer()
    Server.setup(ip='127.0.0.1',port=25567) #prepares the server
    Server.start() #starts the server
    
    while True:
        if Server.event.new_data: #checks if any data recved
            data = Server.return_recved_data() #returns the recved data as a list
            for element in data:
                client_socket, address, data = element #data is saved like this (client_socket,address,recved_data)
                Server.send_data(data, client_socket)
````