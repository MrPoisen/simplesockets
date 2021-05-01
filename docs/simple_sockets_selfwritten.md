# Introduction

This module contains two classes: TCPServer and TCPClient.  

Note: **This Page is still under construction and may be outdated. For the newest code 
documentation look [here](simple_sockets-reference.md).**

## Server
Let's get started with the TCPServer:

Setting up and starting the Server is really easy:

```` python
from simplesockets.simplesockets import TCPServer

Server = TCPServer() # you could specify the max amount of conections
Server.setup(ip="127.0.0.1", port=9999) # more options: listen=5, recv_buffer=2048, handle_client=None
Server.start()
````

When initializing the Server object, you can specify the amount of  
max connections: `Server = TCPServer(5)`.  
Then you need to call ``setup()``. You can give the following arguments:  
- ip: *The ip the Server binds to, standard: `socket.gethostname()`*  
- port: *The port the Server binds to, standard: `25567`*  
- listen: *Is the value used in `socket.listen()`, standard: `5`*  
- recv_buffer: *Is the amount of bytes the socket receives at maximum, standard: `2048`*  
- handle_client: *The function used for handling a Client which has been accepted, standard: `None`*, <span style="color:firebrick"> **I recommend 
  to not change anything here** </span>  
- on_connect: *This variable should contain a function. It will be executed, when the Server got a new 
connection. It takes the address as an argument. standard: `None`*  
- on_disconnect: *This variable should contain a function. It will be executed, when a Client disconnects from the 
  Server. It takes the address as an argument. standard: `None`*  
- on_receive: *This variable should contain a function. It will be executed when the Client 
received new data. It takes the client socket, address and received data as an argument.*    
  
Now the Server must do something.  
We will build an echo Server, which will disconnect the Client after sending the received text.  
I recommend using a while loop to keep the server going.
```` python
while True:
    if Server.event.new_data:
        recved_data = Server.return_recved_data()
````

The `Server.event.new_data` variable is True if the Server received new data. The `Server.return_recved_data()` 
function returns the received data and turns the `Server.event.new_data` variable False. The returned variable is a list of 
all received data. Now you need to iterate over them.  
```` python
        for data_element in recved_data:
            clientsocket, address, data = data_element
````

After iterating you will have a variable, here called `data_element`. It is a tuple containing a socket object from the Client, the 
address of the sender and the sent data. Now we can use the socket object for sending the data back, then we can close the connection.
Therefore, we call `Server.send_data()`. It takes two arguments:  
- data: *The data that you want to send. It should be type `bytes`*  
- client_socket: *The socket of the client*
```` python
            Server.send_data(data, clientsocket)
            Server.disconnect(clientsocket)
````

Now we are finished. Here the complete code:

```` python
from simplesockets.simplesockets import TCPServer

Server = TCPServer()
Server.setup(ip='127.0.0.1',port=9999) 
Server.start() 

while True:
    if Server.new_data_recved: #checks if any data recved
        recved_data = Server.return_recved_data() #returns the recved data as a list
        for data_element in recved_data:
            client_socket, address, data = data_element 
            Server.send_data(data, client_socket)
            Server.disconnect(client_socket)
````

Now we are going to take a look at all the functions we did not cover yet.

### Server Functions   

The `setup(self, ip: str = socket.gethostname(), port: int = 25567, listen: int = 5, recv_buffer: int = 2048,
handle_client=None, on_connect=None, on_disconnect=None, on_receive=None):` function prepares the Server. It got 
explained already.  

The `Server.exit_accept()` function stops and kills the accepting thread.  

The `Server.stop()` function pauses the accepting thread. You can start it again with `Server.start()`. The same function is
used when the amount of connections reaches the defined limit.

The `Server.recv_data(client_socket)` function is automatically called. You don't have to use it for receiving data.

The `Server.killed()` property returns True if the accepting thread got killed

The `Server.restart()` function will restart the accepting thread. If you want to accept Clients, make sure the 
`Server.event.accepting_thread.run` variable is True.  

The `Server.return_exceptions(delete=True, reset_exception=True)` returns all exceptions the class could catch. Use the 
`Server.event.exception.occurred` variable to check if an exception got caught. It can take two arguments. 
If `delete=True`, `Server.event.exception.list` gets reset. If `reset_exception=True`, `Server.exception` will be set 
False.  

The `Server.disconnect(address)` function tries to disconnect a connection to the address

Now, let's cover some variables

### Server Variables

The `Server.recved_data` variable contains all the received data. I recommend 
using the `Server.return_recved_data()` for using the received data.

The `Server.event.accepting_thread.run` variable is True if the accepting thread is running.  

The `Server.event.exception.occurred` variable is True if any exceptions got caught. You can find the 
exceptions in the `Server,event.exception.list` variable.  

The `Server.event.new_data` variable is True if the Server received new data.

The `Server.socket` variable contains the Server socket.

The `Server.clients` variable is a dictionary. The key is the address, the value is a list 
of the Client Thread as it's first value, and the Client socket as it second value.

The `Server.max_connections` variable defines how many connections the Server accepts before refusing new connections. It
can be defined in the initialization of the Server object:  
`Server = TCPServer(5)`.  

The `Server.on_connect`, `Server.on_disconnect` and `Server.on_receive` variables should 
contain functions. The `Server.on_connect` and `Server.on_disconnect` take the address as an 
argument. The `Server.on_receive` takes the received data as an argument.  
 

## Client
Let's get started with the Client.  
First you initialise the Client.  
Then you need to call ``setup()``. You can give the following arguments:  
- target_ip: *The ip the Client connects to*  
- target_port: *The port the Client connects to, standard: `25567`*  
- listen: *Is the value used in `socket.listen()`, standard: `5`*  
- recv_buffer: *Is the amount of bytes the socket receives at maximum, standard: `2048`*  
- on_connect: *This variable should contain a function. It will be executed right after the Client 
connected to the Server. It takes no arguments.*  
- on_disconnect: *This variable should contain a function. It will be executed when the Client disconnects 
  from the Server*  
- on_receive: *This variable should contain a function. It will be executed when the Client 
received new data. It takes the received data as an argument.*  
```` python
from simplesockets.simplesockets import TCPClient

Client = TCPClient() 
Client.setup(target_ip='localhost', target_port=9999) # more options: listen=5, recv_buffer=2048, handle_client=None
````

It's almost the same as with the Server. Next we need to connect to the Server.

```` python
Client.connect()
Client.autorecv()
````
The `Client.autorecv()` starts a Thread which collects all incoming data.

```` python
Client.send_data(b'Test)
while True:
  if Client.event.new_data: 
````
Then the Clients sends his message. Next, we wait for incoming data in a while loop. 
Should we receive data trough the `Client.autorecv()`, `Client.new_data_recved` will be true.

```` python
  recved_data = Client.return_recved_data()
    for data_element in recved_data:
      print(data_element)
````
Here is the complete code:
```` python
from simplesockets.simplesockets import TCPClient

Client = TCPClient() 
Client.setup(target_ip='localhost', target_port=9999) # more options: listen=5, recv_buffer=2048, handle_client=None
Client.start()

Client.connect()
Client.autorecv()

Client.send_data(b'Test')
while True:
  if Client.event.new_data: 
    recved_data = Client.return_recved_data()
    for data_element in recved_data:
      print(data_element)
````
Now we should take al look at all functions we didn't cover yet.
### Client Functions

The `Client.setup(target_ip: str, target_port: int = 25567, recv_buffer: int = 2048, on_connect: Callable = None,
on_disconnect: Callable = None, on_receive: Callable = None):` function prepares the Client. 
This function got explained previously.  

The `Client.connect()` function tries to connect to the Server.  

The `Client.send_data(data: bytes)` function tries to send the given data to the Server.  

The `Client.reconnect()` function try's to reconnect to the Server.

The `Client.shutdown()` function ends the `autrecv` Thread end closes the Connection.

The `Client.return_exceptions()` returns all exceptions

The `Client.return_recved_data()` function returns the received data and sets `Client.event.new_data` to False.  

The `Client.autorecv()` function toggles the `autorecv_thread`. It starts stopped.  

The `Client.disconnect()` function tries to disconnect from the Server.  

### Client Variables
The `Client.recved_data` variable contains all the received data. I recommend 
using the `Client.return_recved_data()` for using the received data.

The `Client.socket` variable contains the Client socket.

The `Client.event.exception.occurred` variable is true if any exceptions raised and got caught.  

The `Client.event.exception.list` variable contains all caught exceptions.  

The `CLient.event.new_data` variable is true if the Client received any new data.  

The `Client.event.disconnected` variable is True if the Client disconnected from the Serer.  

The `Client.event.connected` variable is True if the connecting proccess to the Server was succesful.  

The `Client.event.is_connected` variable is True if the Client is connected to the Server.

The `Client.Address` property is a tuple of the `target_ip` and the `target_port.`
