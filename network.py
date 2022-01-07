import socket
import server.server_const as server_const


class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = server_const.HOST_IP_ADDRESS
        self.port = server_const.HOST_GAME_PORT
        self.address = (self.server, self.port)
        self.game_data = self.connect()

    def get_game_data(self):
        return self.game_data

    def connect(self):
        try:
            self.client.connect(self.address)
            return self.client.recv(4096).decode()
        except:
            pass

    def send(self, data):
        try:
            self.client.send(str.encode(data))
            return self.client.recv(4096).decode()
        except socket.error as e:
            print(e)
