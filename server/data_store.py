from collections import defaultdict
import json
import os.path

STORE = f"{os.path.dirname(os.path.abspath(__file__))}/store.json"


def read_data() -> defaultdict:
    data = defaultdict(lambda: {"subscribers": [], "info": ""})
    with open(STORE, "r") as f:
        data = defaultdict(lambda: {
            "subscribers": [], "info": ""
        }, json.loads(f.read()))
        f.close()
    return data


def write_data(data: defaultdict):
    with open(STORE, "w") as f:
        json.dump(data, f)
        f.close()


def add_learning_state(learn_id: str, info: str = ""):
    data = read_data()
    data[learn_id]["info"] = info
    write_data(data)


def del_learning_state(learn_id: str):
    data = read_data()
    del data[learn_id]
    write_data(data)


def get_learning_state(learn_id: str) -> str:
    data = read_data()
    return data[learn_id]["info"]


def update_learning_state(learn_id: str, info: str = ""):
    data = read_data()
    data[learn_id]["info"] = info
    write_data(data)


def add_subscriber(learn_id: str, username: str) -> str:
    data = read_data()

    if not learn_id in data:
        return f"id: {learn_id} doesn't exist"
    if username in data[learn_id]["subscribers"]:
        return f"User is already subscribed to id: {learn_id}!"

    data[learn_id]["subscribers"].append(username)
    write_data(data)
    return f"User is now subscribed to id: {learn_id}"


def del_subscriber(learn_id: str, username: str) -> str:
    data = read_data()

    if not learn_id in data:
        return f"id: {learn_id} doesn't exist"
    if username in data[learn_id]["subscribers"]:
        data[learn_id]["subscribers"].remove(username)
        write_data(data)
        return f"User is now unsubscribed from id: {learn_id}"
    else:
        return f"User is not subscribed to id: {learn_id}"
