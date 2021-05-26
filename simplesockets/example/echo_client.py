
if __name__ == "__main__":
    from simplesockets import TCPClient

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