
if __name__ == "__main__":
    from simplesockets.simplesockets import TCPServer

    Server = TCPServer()
    Server.setup(ip='127.0.0.1',port=25567) #prepares the server
    Server.start() #starts the server

    while True:
        if Server.new_data_recved: #checks if any data recved
            data = Server.return_recved_data() #returns the recved data as a list
            for element in data:
                client_socket, addres, data = element #data is saved like this (client_socket,address,recved_data)
                Server.send_data(data,client_socket)