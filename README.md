# 2D-MultiAI-PlayGround

## Prerequisites
Install the required packages before running our program

```
pip install -r requirements.txt
```

## Starting
Start our game with app.py
```
python app.py
```

## Networking
### LAN/WAN Multiplayer
IMPORTANT!
1) Ensure that your anti-virus/firewall is not blocking the connection.
2) Ensure that Port-Forwarding is enabled on your router for your HOST IP and HOST PORT is available.
3) Use the the public port when connecting. 

Check server connectivity with:
1) Website: https://check-host.net/check-tcp
2) PowerShell: Test-NetConnection <online host> -p <public port>


### Telegram Bot Setup (Optional)
This is optional and the reinforcement learning will still work without it.
Launch server/socket_server.py and server/telebot.py
```
python server/socket_server.py
python server/telebot.py
```

Message [@multiai_postman_bot](https://t.me/multiai_postman_bot) on telegram the commands to retrieve latest training information
- /subscribe - Receive updates from learning model every x minutes (If $interval_minute isn't specified, default is 15 minutes)
- /unsubscribe - Stop receiving updates from learning model
- /update - Retrieves the latest update from learning model
```
/subscribe $learn_id $interval_minute
/(unsubscribe|update) $learn_id
```


## Resources
[Soldier sprite](https://www.cleanpng.com/png-pixel-art-soldier-1821529/)

[Rocket sprite](https://gamesupply.itch.io/massive-weapon-package)