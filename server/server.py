# Sever Script must always be running while having multiple Client Script connected to it.

from _thread import *
import socket
import server_const


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


current_player = 0
connected = set()
games_session = {}
idCount = 1


def threaded_client(conn, player_index, game_id):
    global idCount

    conn.send(str.encode(str(player_index)))

    reply = ""
    while True:
        try:
            data = read_game_data(conn.recv(4096).decode())

            if game_id in games_session:
                # If no Info received
                if not data:
                    print("Disconnected")
                    break
                # If got Info
                else:
                    # Check both player ready
                    if data[0] == 1:
                        conn.sendall(str.encode(str(games_session[game_id][2])))
                    elif data[0] == 2:
                        if player_index == 1:
                            games_session[game_id][3] = data[1]
                        else:
                            games_session[game_id][5] = data[1]

                        conn.sendall(str.encode(str("OK")))
                    elif data[0] == 3:
                        if player_index == 1:
                            games_session[game_id][4] = (data[1] / 100.0)
                        else:
                            games_session[game_id][6] = (data[1] / 100.0)

                        conn.sendall(str.encode(str("OK")))
                    # Ready Status
                    elif data[0] == 4:
                        # Player 1 -> Set self to ready while setting Player 0 to not ready
                        if player_index == 1:
                            games_session[game_id][8] = 1
                            games_session[game_id][7] = 0
                            conn.sendall(str.encode(str(games_session[game_id][8])))
                        # Player 0 -> Set self to ready while setting Player 1 to not ready
                        else:
                            games_session[game_id][8] = 0
                            games_session[game_id][7] = 1
                            conn.sendall(str.encode(str(games_session[game_id][7])))
                    # Check other player is ready
                    elif data[0] == 5:
                        # Player 1 -> See if Player 0 is ready already
                        if player_index == 1:
                            if games_session[game_id][7] == 1:
                                conn.sendall(str.encode(str("1")))
                            else:
                                conn.sendall(str.encode(str("0")))
                        # Player 0 -> See if Player 1 is ready already
                        else:
                            if games_session[game_id][8] == 1:
                                conn.sendall(str.encode(str("0")))
                            else:
                                conn.sendall(str.encode(str("1")))
                    else:
                        games_session[game_id][player_index] = data

                        if player_index == 1:
                            reply = games_session[game_id][0]
                        else:
                            reply = games_session[game_id][1]

                        conn.sendall(str.encode(game_data_to_string(reply)))
            else:
                break
        except:
            break

    # Delete games that are closed
    print("Lost Connection")

    try:
        del games_session[game_id]
        print("Closing Game", game_id)
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
    current_player = 0
    game_id = (idCount - 1) // 2

    # If is player 1 (Game Host)
    if idCount % 2 == 1:
        # Initialize List
        # (PLAYER_1_XY_FIRED_BULLET_XY_ANGLE), (PLAYER_2_XY_FIRED_BULLET_XY_ANGLE), BOTH_PLAYER_READY_BOOL,
        # SCORE_P1, AVG_REWARD_P1, SCORE_P2, AVG_REWARD_P2, PLAYER_1_READY_BOOL, PLAYER_2_READY_BOOL
        games_session[game_id] = [(server_const.START_POS_P1_X, server_const.START_POS_P1_Y, False, 0, 0, -1),
                                  (server_const.START_POS_P2_X, server_const.START_POS_P2_Y, False, 0, 0, -1), 0,
                                  0, 0.0, 0, 0.0, 0, 0]

        print("Creating a new game...")

    # If is player 2
    else:
        current_player = 1
        games_session[game_id][2] = 1

    # Increment ID Count
    idCount += 1

    # Assign new thread
    start_new_thread(threaded_client, (conn, current_player, game_id))
