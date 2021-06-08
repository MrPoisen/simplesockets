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
