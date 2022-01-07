import array

import pygame
from matplotlib import pyplot as plt
import threading
import socketio

from network import Network

from units import Soldier
from units import Rocket
import ai_network
import server.server_const
from const import MOVEMENT_AI_NETWORK

import json
import tkinter as tk
from tkinter import *
import os

# Override Intel MKL
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# State Const
INDEX_OF_IS_FIRED = 2

# Param To Include
is_enemy_pos_X = False
is_enemy_pos_Y = False
is_player_pos_X = False
is_player_pos_Y = False
is_enemy_bullet_X = False
is_enemy_bullet_Y = False
is_enemy_bullet_dist = False

# Movement Reward Const
MOVEMENT_LIVING_PENALTY = -0.005
HIT_PENALTY = -6.0
NEAR_ENEMY_PENALTY = -1.0
ENEMY_MISS_REWARD = 0.0

# Initialize Movement Param
enemyPosX = 0
enemyPosY = 0
enemyBulletX = 0
enemyBulletY = 0
enemyBulletY = 0
playerPosX = 0
playerPosY = 0

# Initialize Shooting Param
is_Fired = False
anglePlayerToEnemy = 0
distancePlayerToEnemy = 0
gunVector = 0

# Reward for shooting
hit_reward = 0
reward_pointing_near_target = 0
gun_ready_reward = 0

# Reward for Movement
hit_dodge_reward = 0
near_enemy_reward = 0

# Scores
num_hit = 0
avg_score_movement = 0.0

# Telegram updater
sio = socketio.Client()
learn_id = "-1"
action_count = 0

# User inputs
MOVEMENT_LIVING_PENALTY_ = -0.005
HIT_PENALTY_ = -6.0
NEAR_ENEMY_PENALTY_ = -1.0
ENEMY_MISS_REWARD_ = 0.0


def cal_movement_reward(playerPosX, playerPosY, MOVEMENT_LIVING_PENALTY):
    global hit_dodge_reward, near_enemy_reward

    final_movement_reward = hit_dodge_reward + MOVEMENT_LIVING_PENALTY + near_enemy_reward


    return final_movement_reward


def ai_firing(rocket_group, player):
    rocket_group.add(player.shoot_angle(gunVector))


def read_game_data(data):
    data = data.split(",")

    for i in range(len(data)):
        data[i] = int(data[i])
        if i == 2:
            data[i] = bool(data[i])

    return data


def game_data_to_string(data):
    for i in range(len(data)):
        if isinstance(data[i], bool):
            data[i] = "1" if data[i] else "0"
        else:
            data[i] = str(data[i])

    return ",".join(data)


def game_progress_to_string():
    global num_hit
    return str(num_hit)


def game_progress_avg():
    global avg_score_movement
    return str(int(avg_score_movement * 100))


def draw_window(screen, soldier_group, player_rocket, enemy_fired, enemy_rocket, stat_disp, player_number, playerX,
                playerY, player_disp):
    screen.fill((0, 0, 0))
    soldier_group.draw(screen)

    if player_rocket is not None:
        player_rocket.draw(screen)

    if enemy_fired and enemy_rocket is not None:
        enemy_rocket.draw(screen)

    display_hit_count(screen, 10, 10, stat_disp)
    display_player_number(screen, playerX, playerY - 10, player_number, player_disp)


def display_not_ready(screen, x, y, font):
    screen.fill((0, 0, 0))
    not_ready = font.render("WAITING FOR PLAYER!", True, (255, 255, 255))
    screen.blit(not_ready, (x, y))


def display_hit_count(screen, x, y, font):
    global num_hit, avg_score_movement
    curr_score = font.render("SCORE: " + str(num_hit), True, (255, 255, 255))
    screen.blit(curr_score, (x, y))
    curr_avg = "{:.2f}".format(avg_score_movement)
    curr_avg = font.render("AVG Reward: " + str(curr_avg), True, (255, 255, 255))
    screen.blit(curr_avg, (x, y + 30))


def display_hit_status(screen, x, y, font, hit_miss):
    if hit_miss is False:
        hit_stat = font.render("Missed Me!" + str(num_hit), True, (255, 255, 255))
    else:
        hit_stat = font.render("I'm Hit!" + str(num_hit), True, (255, 255, 255))
    screen.blit(hit_stat, (x, y))


def display_player_number(screen, x, y, playernum, font):
    player_number = font.render("PLAYER: " + str(playernum + 1), True, (255, 255, 255))
    screen.blit(player_number, (x, y))


def sio_connect():
    """Creates a connection with the socketio server
    """

    global sio

    try:
        sio.connect(f"http://{server.server_const.HOST_IP_ADDRESS}:{server.server_const.HOST_UPDATE_PORT}")
        print("Connected to socket server, SID:", sio.sid)

    except Exception as e:
        print(e)


def sio_update(info: str):
    """Updates socketio server with latest information

    Args:
        data (str): [description]
    """

    global sio

    if sio.connected:
        data = {
            "learn_id": learn_id,
            "info": str(info)
        }
        sio.emit("update", json.dumps(data))


@sio.event
def id_generation(id: str):
    """Updates learn_id upon receiving "id_generation" event from server

    Args:
        id (str): Generated learn_id to be used for this training session
    """
    global learn_id

    learn_id = id
    print(f"Subscribe to learn id {learn_id} to receive updates on telegram!")


def plot_graph(sliding_window_scores_move):
    plt.plot(sliding_window_scores_move)
    plt.xlabel('Number of Iteration', fontsize=14)
    plt.ylabel('Average Reward', fontsize=14)
    plt.savefig('./saved_graph/Training_Graph.png')


def main():
    # Shooting Global Var
    global is_Fired, gunVector, anglePlayerToEnemy, distancePlayerToEnemy, bulletPosX, bulletPosY
    global gunVectorDeltaFineA, gunVectorDeltaCoarseA, gunVectorDeltaFine, gunVectorDeltaCoarse
    global hit_reward, reward_pointing_near_target, gun_ready_reward, num_hit

    # Movement Global Var
    global enemyPosX, enemyPosY, playerPosX, playerPosY, enemyBulletX, enemyBulletY
    global hit_dodge_reward, near_enemy_reward, avg_score_movement
    global is_enemy_pos_X, is_enemy_pos_Y, is_player_pos_X, is_player_pos_Y, is_enemy_bullet_X, is_enemy_bullet_Y, is_enemy_bullet_angle, is_enemy_bullet_dist

    # Telegram Global Var
    global action_count

    # PyGame Initialization
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("2D MultiAI Playground")
    not_ready_disp = pygame.font.Font('freesansbold.ttf', 60, )
    stat_disp = pygame.font.Font('freesansbold.ttf', 22, )
    player_disp = pygame.font.Font('freesansbold.ttf', 10, )

    # tkinter GUI
    # Reward Weights Tweaking
    a = read_input()
    MOVEMENT_LIVING_PENALTY = float(a[0])
    HIT_PENALTY = float(a[1])
    NEAR_ENEMY_PENALTY = float(a[2])
    ENEMY_MISS_REWARD = float(a[3])
    print(MOVEMENT_LIVING_PENALTY, HIT_PENALTY, NEAR_ENEMY_PENALTY, ENEMY_MISS_REWARD)

    # States to Include
    is_enemy_pos_X = bool(a[4])
    is_enemy_pos_Y = bool(a[5])
    is_player_pos_X = bool(a[6])
    is_player_pos_Y = bool(a[7])
    is_enemy_bullet_X = bool(a[8])
    is_enemy_bullet_Y = bool(a[9])
    is_enemy_bullet_dist = bool(a[10])
    number_of_states = a[4] + a[5] + a[6] + a[7] + a[8] + a[9] + a[10]



    # Loop Conditions
    running = True
    not_ready = True

    # Networking
    network = Network()

    # Get the starting position from sever
    try:
        player_number = int(network.get_game_data())
        print("You are Player Number: ", player_number + 1)
    except:
        running = False
        print("Couldn't get game")
    is_server_sync = False

    # DQN Network Initialization
    manual_ctrl = False
    sliding_window_scores_move = []
    dqn_movement = ai_network.Dqn(number_of_states, 4, 0.80)

    # Initialize Data
    initial_state = [(server.server_const.START_POS_P1_X, server.server_const.START_POS_P1_Y, False, 0, 0, -1),
                     (server.server_const.START_POS_P2_X, server.server_const.START_POS_P2_Y, False, 0, 0, -1)]

    # Player & Enemy Initialization
    enemy_fired = False
    player = Soldier(initial_state[0][0], initial_state[0][1], False)
    enemy = Soldier(initial_state[1][0], initial_state[1][1], False)
    clock = pygame.time.Clock()
    player.set_target(enemy)
    enemy.set_target(player)
    soldier_group = pygame.sprite.Group()
    soldier_group.add(player)
    soldier_group.add(enemy)

    # Rocket Management
    is_fired = False
    player_rocket = None
    enemy_rocket = None
    rocket_X = 0
    rocket_Y = 0
    rocket_angle = -1
    count_delay = 0

    # Polling for second player.
    while not_ready:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                not_ready = False
                running = False

        clock.tick(60)
        display_not_ready(screen, 50, 250, not_ready_disp)
        ready_status = network.send("1")
        not_ready_int = int(ready_status)
        pygame.display.update()
        if not_ready_int == 1:
            not_ready = False
            print("Ready!")

    # Main Loop
    while running:
        # set game to 60 fps
        clock.tick(60)

        # Button and Manual Firing
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and manual_ctrl is True:
                if event.button == 1 and is_fired is False:
                    dest = pygame.mouse.get_pos()
                    is_fired = True
                    player_rocket = player.shoot(dest)
                    rocket_angle = int(player_rocket.angle)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    manual_ctrl = not manual_ctrl
                # Saving DQN network
                elif event.key == pygame.K_t:
                    dqn_movement.save(MOVEMENT_AI_NETWORK)
                    plot_graph(sliding_window_scores_move)
                # Loading DQN network
                elif event.key == pygame.K_y:
                    dqn_movement.load(MOVEMENT_AI_NETWORK)
                elif event.key == pygame.K_u:
                    string_to_send = game_progress_to_string()
                    print(network.send("2," + string_to_send))
                    string_to_send = game_progress_avg()
                    print(network.send("3," + string_to_send))

        # Server Synchronizing
        is_client_ready_check = network.send("4")
        while is_server_sync:
            is_client_ready_confirm = network.send("5")
            if int(is_client_ready_confirm) == player_number:
                is_server_sync = False
        is_server_sync = True

        if manual_ctrl is False and is_fired is False:
            count_delay += 1
            if count_delay > 20:
                count_delay = 0
                is_fired = True
                player_rocket = player.shoot((enemyPosX + 25, enemyPosY + 28))
                rocket_angle = int(player_rocket.angle)

        # Player Rocket Management
        if player_rocket is not None:
            hit, target = player_rocket.update()

            rocket_X = player_rocket.rect.x
            rocket_Y = player_rocket.rect.y

        # Send Server and Receive Updates
        player_state = game_data_to_string([player.rect.x, player.rect.y,
                                            is_fired, rocket_X, rocket_Y, rocket_angle])
        enemy_state = network.send(player_state)
        enemy_state = read_game_data(enemy_state)
        enemy.setpos(enemy_state[0], enemy_state[1])

        # We check for rocket collision only after update game state because enemy needs the "hit" state
        # Super inefficient but temporary workaround
        if player_rocket is not None:
            if hit:
                player_rocket = None
                is_fired = False
                num_hit += 1

            elif player_rocket.is_out_of_bounds():
                player_rocket = None
                is_fired = False

        # Check did enemy fire
        # hit_status = False
        if enemy_state[INDEX_OF_IS_FIRED]:
            enemy_fired = True
            if enemy_rocket is None:
                enemy_rocket = Rocket(enemy.rect.center,
                                      player.rect.center, player)
            enemy_rocket.vel_x = 0
            enemy_rocket.vel_y = 0
            enemy_rocket.rect.x = enemy_state[3]
            enemy_rocket.rect.y = enemy_state[4]
            enemyBulletX = enemy_state[3]
            enemyBulletY = enemy_state[4]
            enemy_rocket.angle = enemy_state[5]
            enemy_rocket.rotate_abs(enemy_state[5])
            hit_dodge_reward = 0.0
        else:
            enemyBulletX = enemy_state[0]
            enemyBulletY = enemy_state[1]
            if enemy_fired is False:
                hit_dodge_reward = 0.0
            else:
                # Hit Player
                if pygame.sprite.collide_rect(player, enemy_rocket):
                    hit_dodge_reward = HIT_PENALTY
                    enemy_fired = False
                    # print("I was hit!!!")
                # Went out of bound
                else:
                    hit_dodge_reward = ENEMY_MISS_REWARD
                    enemy_fired = False
                    # print("Enemy missed!!!")

        # Update Movement Param
        enemyPosX = enemy_state[0]
        enemyPosY = enemy_state[1]
        playerPosX = player.rect.x
        playerPosY = player.rect.y

        # Update Shooting Param
        distancePlayerToEnemy = (
                (((enemyBulletX - playerPosX) ** 2) + ((enemyBulletY - playerPosY) ** 2)) ** 0.5)

        # Update Rewards
        if distancePlayerToEnemy <= 100.0:
            near_enemy_reward = NEAR_ENEMY_PENALTY
        else:
            near_enemy_reward = 0

        # Calculate Reward
        last_reward_movement = cal_movement_reward(playerPosX, playerPosY, MOVEMENT_LIVING_PENALTY)

        if enemyBulletX < 0:
            enemyBulletX = 0
        if enemyBulletY < 0:
            enemyBulletY = 0

        # last_state update
        last_state_movement = []

        if is_enemy_bullet_X:
            last_state_movement.append(enemyBulletX / 800.0)
        if is_enemy_bullet_Y:
            last_state_movement.append(enemyBulletY / 600.0)
        if is_player_pos_X:
            last_state_movement.append(playerPosX / 800.0)
        if is_player_pos_Y:
            last_state_movement.append(playerPosY / 600.0)
        if is_enemy_pos_X:
            last_state_movement.append(enemyPosX / 800.0)
        if is_enemy_pos_Y:
            last_state_movement.append(enemyPosY / 600.0)
        if is_enemy_bullet_dist:
            last_state_movement.append(distancePlayerToEnemy / 1000.0)
        # print(last_state_movement)
        # last_state_movement = [(enemyBulletX / 800.0), (enemyBulletY / 600.0), playerPosX / 800.0, playerPosY / 600.0]

        # Toggle AI control and manual control
        if not manual_ctrl:
            next_action_movement = dqn_movement.update(last_reward_movement, last_state_movement)
            avg_score_movement = dqn_movement.overall_score()
            sliding_window_scores_move.append(avg_score_movement)
            player.ai_move(next_action_movement)
        else:
            player.manual_move()

        # Telegram Update
        action_count += 1
        if action_count > 1000:
            action_count = 0
            sio_update("Player: " + str(player_number + 1) + "\nAvg score: {:.4f}".format(
                avg_score_movement) + "\nNumber Hit: " + str(num_hit))

        # Draw onto screen
        draw_window(screen, soldier_group, player_rocket, enemy_state[INDEX_OF_IS_FIRED], enemy_rocket, stat_disp,
                    player_number, playerPosX, playerPosY, player_disp)
        pygame.display.update()

    pygame.quit()


def read_input():
    window = tk.Tk()
    window.title('Set AI parameters')
    window.geometry('350x600')

    a = [-0.005, -6.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    l = tk.Label(window, bg='white', fg='black', width=60, text='Adjust reward/penalty weights:')
    l.pack()

    def print_selection_s(v):
        global MOVEMENT_LIVING_PENALTY_
        MOVEMENT_LIVING_PENALTY_ = v

    def print_selection_t(v):
        global HIT_PENALTY_
        HIT_PENALTY_ = v

    def print_selection_u(v):
        global NEAR_ENEMY_PENALTY_
        NEAR_ENEMY_PENALTY_ = v

    def print_selection_v(v):
        global ENEMY_MISS_REWARD_
        ENEMY_MISS_REWARD_ = v

    s = tk.Scale(window, label='Living Penalty', from_=-0.02, to=0.00, orient=tk.HORIZONTAL, length=300, showvalue=0,
                 tickinterval=0.005,
                 resolution=0.001, command=print_selection_s)
    s.pack()
    s.set(-0.005)

    t = tk.Scale(window, label='Taking Hit Penalty', from_=-10, to=0, orient=tk.HORIZONTAL, length=300, showvalue=0,
                 tickinterval=2.5,
                 resolution=0.01, command=print_selection_t)
    t.pack()
    t.set(-6.0)

    u = tk.Scale(window, label='Enemy Proximity Penalty', from_=-5, to=0, orient=tk.HORIZONTAL, length=300, showvalue=0,
                 tickinterval=1.25,
                 resolution=0.01, command=print_selection_u)
    u.pack()
    u.set(-1.0)

    v = tk.Scale(window, label='Dodge Reward', from_=0, to=2, orient=tk.HORIZONTAL, length=300, showvalue=0,
                 tickinterval=-0.25,
                 resolution=0.01, command=print_selection_v)
    v.pack()
    v.set(0.2)

    Checkbutton1 = IntVar()
    Checkbutton2 = IntVar()
    Checkbutton3 = IntVar()
    Checkbutton4 = IntVar()
    Checkbutton5 = IntVar()
    Checkbutton6 = IntVar()
    Checkbutton7 = IntVar()

    m = tk.Label(window, bg='white', fg='black', width=60, text='Select states to feed to AI:')
    m.pack()
    Button1 = Checkbutton(window, text="Enemy Bullet X Coordinate",
                          variable=Checkbutton1,
                          onvalue=1,
                          offvalue=0,
                          height=2,
                          width=100)

    Button2 = Checkbutton(window, text="Enemy Bullet Y Coordinate",
                          variable=Checkbutton2,
                          onvalue=1,
                          offvalue=0,
                          height=2,
                          width=100)

    Button3 = Checkbutton(window, text="Own X Coordinate",
                          variable=Checkbutton3,
                          onvalue=1,
                          offvalue=0,
                          height=2,
                          width=100)

    Button4 = Checkbutton(window, text="Own Y Coordinate",
                          variable=Checkbutton4,
                          onvalue=1,
                          offvalue=0,
                          height=2,
                          width=100)

    Button5 = Checkbutton(window, text="Enemy X Coordinate",
                          variable=Checkbutton5,
                          onvalue=1,
                          offvalue=0,
                          height=2,
                          width=100)

    Button6 = Checkbutton(window, text="Enemy Y Coordinate",
                          variable=Checkbutton6,
                          onvalue=1,
                          offvalue=0,
                          height=2,
                          width=100)
    Button7 = Checkbutton(window, text="Enemy Bullet Distance",
                          variable=Checkbutton7,
                          onvalue=1,
                          offvalue=0,
                          height=2,
                          width=100)

    Button1.pack()
    Button2.pack()
    Button3.pack()
    Button4.pack()
    Button5.pack()
    Button6.pack()
    Button7.pack()

    def save():
        window.destroy()
        a[0] = MOVEMENT_LIVING_PENALTY_
        a[1] = HIT_PENALTY_
        a[2] = NEAR_ENEMY_PENALTY_
        a[3] = ENEMY_MISS_REWARD_
        a[4] = Checkbutton1.get()
        a[5] = Checkbutton2.get()
        a[6] = Checkbutton3.get()
        a[7] = Checkbutton4.get()
        a[8] = Checkbutton5.get()
        a[9] = Checkbutton6.get()
        a[10] = Checkbutton7.get()
        print(a)
        return a

    btn = Button(window, text='Start !', bd='5',
                 command=save)

    btn.pack(side='bottom')
    window.mainloop()
    return a


if __name__ == "__main__":
    t1 = threading.Thread(target=main)
    t1.start()
    sio_connect()
