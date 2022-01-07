import eventlet
import socketio
import json

import data_store
import server_const

sio = socketio.Server()
app = socketio.WSGIApp(sio)

sid_table = {}


@sio.event
def connect(sid, env):
    print("Connected:", sid)


@sio.event
def disconnect(sid):
    print("Disconnected:", sid)

    if sid in sid_table:
        data_store.del_learning_state(sid_table[sid])
        del sid_table[sid]


@sio.event
def new_learning_state(sid, learn_id):
    sid_table[sid] = learn_id
    data_store.add_learning_state(learn_id)


@sio.event
def update(sid, data):
    data = json.loads(data)
    data_store.update_learning_state(data["learn_id"], data["info"])


if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(
        (server_const.HOST_IP_ADDRESS, server_const.HOST_UPDATE_PORT)
    ), app)
