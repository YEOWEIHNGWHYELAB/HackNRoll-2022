
from _thread import *
import socket
import server_const

# Sever Script must always be running while having multiple Client Script connected to it.


server = server_const.HOST_IP_ADDRESS
port = server_const.HOST_GAME_PORT
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


try:
    s.bind((server, port))
except socket.error as e:
    print(str(e))


s.listen(2)
print("Server Ready! Waiting for connection...")


def read_game_data(data):
    data = data.split(",")

    for i in range(len(data)):
        data[i] = int(data[i])
        if i == 2:
            data[i] = bool(data[i])

    return data


def game_data_to_string(data):
    data = list(data)
    for i in range(len(data)):
        if isinstance(data[i], bool):
            data[i] = "1" if data[i] else "0"
        else:
            data[i] = str(data[i])

    return ",".join(data)


currentPlayer = 0
connected = set()
games_session = {}
idCount = 1


def threaded_client(conn, player_index, gameId):
    global idCount

    conn.send(str.encode(str(player_index)))

    reply = ""
    while True:
        try:
            data = read_game_data(conn.recv(4096).decode())

            if gameId in games_session:
                # If no Info received
                if not data:
                    print("Disconnected")
                    break
                # If got Info
                else:
                    if data[0] == 1:
                        conn.sendall(str.encode(str(games_session[gameId][2])))
                    else:
                        games_session[gameId][player_index] = data

                        if player_index == 1:
                            reply = games_session[gameId][0]
                        else:
                            reply = games_session[gameId][1]

                        # print("Received: ", data)
                        # print("Sending: ", reply)

                        conn.sendall(str.encode(game_data_to_string(reply)))
            else:
                break
        except:
            break

    # Delete games that are closed
    print("Lost Connection")

    try:
        del games_session[gameId]
        print("Closing Game", gameId)
    except:
        pass

    idCount -= 1
    conn.close()


# Continuously check if someone is connecting, if so assign a new thread
while True:
    # Accepts incoming connection
    conn, addr = s.accept()
    print("Connected to:", addr)

    # ID management
    currentPlayer = 0
    gameId = (idCount - 1) // 2

    # If is player 1
    if idCount % 2 == 1:
        games_session[gameId] = [(server_const.START_POS_P1_X, server_const.START_POS_P1_Y, False, 0, 0, -1),
                                 (server_const.START_POS_P2_X, server_const.START_POS_P2_Y, False, 0, 0, -1), 0]

        print("Creating a new game...")

    # If is player 2
    else:
        currentPlayer = 1
        games_session[gameId][2] = 1

    # Increment ID Count
    idCount += 1

    # Assign new thread
    start_new_thread(threaded_client, (conn, currentPlayer, gameId))
