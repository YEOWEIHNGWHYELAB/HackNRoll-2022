import eventlet
import socketio
import json
import random

import data_store
from telebot import TeleBot
import server_const

sio = socketio.Server()
app = socketio.WSGIApp(sio)

sid_table = {}


@sio.event
def connect(sid: str, env: dict):
    """When learning session connects with the socketio server, it generates a 
       learn ID for them which will be used to keep track of any information

    Args:
        sid (str): Socket ID of learning session
        env (dict): Server environment variables
    """

    global sid_table

    # ensures there's no key collisions
    new_id = str(random.randint(1e2, 1e5))
    while new_id in sid_table:
        new_id = str(random.randint(1e2, 1e5))

    # sends learn_id to training session
    sio.emit("id_generation", data=new_id, room=sid)

    # adds it to the table and store.json
    sid_table[sid] = new_id
    data_store.add_learning_state(new_id)

    print("Connected:", sid)


@sio.event
def disconnect(sid: str):
    """When learning session disconnects from the socketio server
       all information of it will be deleted

    Args:
        sid (str): Socket ID of learning session
    """

    global sid_table

    # deletes training session when learning model disconnects
    if sid in sid_table:
        # broadcasts message on termination
        TeleBot.end_session(sid_table[sid])

        data_store.del_learning_state(sid_table[sid])
        del sid_table[sid]

    print("Disconnected:", sid)


@sio.event
def update(sid: str, data: str):
    """Updates latest information of learning model upon receiving "update" event from learning model

    Args:
        sid (str): Socket ID of learning session
        data (str): JSON string in the format of {
            "learn_id": Generated learn_id
            "info": Information for Telegram bot to send to users
        }
    """

    data = json.loads(data)
    data_store.update_learning_state(data["learn_id"], data["info"])


if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(
        (server_const.HOST_IP_ADDRESS, server_const.HOST_UPDATE_PORT)
    ), app)
