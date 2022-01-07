import json
import pygame
import random
import math
from matplotlib import pyplot as plt

import threading
import socketio
from server.server_const import HOST_IP_ADDRESS, HOST_UPDATE_PORT

import ai_network
from const import MoveType, SHOOTING_AI_NETWORK
from units import Soldier, Target

HIT_REWARD = 1
POINTING_GUN_AT_TARGET_REWARD = 0.01
MISS_PENALTY = -0.02
FIRING_NOT_READY_PENALTY = -0.01
FIRING_REWARD = 0.2
LIVING_PENALTY = -0.3

# Player States
is_Fired = False
anglePlayerToEnemy = 0
distancePlayerToEnemy = 0
gunVector = 0
bulletPosX = 0
bulletPosY = 0

# Gun Vector Adjust
gunVectorDeltaFineA = 1
gunVectorDeltaCoarseA = 20
gunVectorDeltaFine = -1
gunVectorDeltaCoarse = -20

# Reward
hit_reward = 0
reward_pointing_near_target = 0
gun_ready_reward = 0

# Telegram updater
sio = socketio.Client()
learn_id = "-1"


def display_input_param(win, x, y, font, avg_reward):
    dist = distancePlayerToEnemy
    format_float_avg_reward = "{:.2f}".format(dist)
    distance = font.render(
        "Distance: " + str(format_float_avg_reward), True, (255, 255, 255))
    win.blit(distance, (x, y))

    angleEn = anglePlayerToEnemy
    format_float_angle = "{:.2f}".format(angleEn)
    angle = font.render(
        "Enemy Angle: " + str(format_float_angle), True, (255, 255, 255))
    win.blit(angle, (x, y + 30))

    gunPoint = font.render(
        "Gun Angle: " + str(gunVector), True, (255, 255, 255))
    win.blit(gunPoint, (x, y + 60))

    avgR = avg_reward
    format_float_avg_reward = "{:.2f}".format(avgR)
    avgReward = font.render(
        "AVG_Reward: " + str(format_float_avg_reward), True, (255, 255, 255))
    win.blit(avgReward, (x, y + 90))


def ai_firing(rocket_group, player):
    rocket_group.add(player.shoot_angle(gunVector))


def ai_control(next_action, rocket_group, player):
    global gunVector, is_Fired, gun_ready_reward

    if next_action == 0:
        if (gunVector + gunVectorDeltaFineA) > 360:
            gunVector += (gunVectorDeltaFineA - 360)
        else:
            gunVector += gunVectorDeltaFineA
    elif next_action == 1:
        if (gunVector + gunVectorDeltaCoarseA) > 360:
            gunVector += (gunVectorDeltaCoarseA - 360)
        else:
            gunVector += gunVectorDeltaCoarseA
    elif next_action == 2:
        if (gunVector + gunVectorDeltaFine) < 0:
            gunVector += (gunVectorDeltaFine + 360)
        else:
            gunVector += gunVectorDeltaFine
    elif next_action == 3:
        if (gunVector + gunVectorDeltaCoarse) < 0:
            gunVector += (gunVectorDeltaCoarse + 360)
        else:
            gunVector += gunVectorDeltaCoarse
    else:
        # Only 1 bullet at a time
        if not is_Fired:
            ai_firing(rocket_group, player)
            is_Fired = True
            gun_ready_reward = FIRING_REWARD
        else:
            gun_ready_reward = FIRING_NOT_READY_PENALTY


def main():
    global is_Fired, anglePlayerToEnemy, distancePlayerToEnemy, bulletPosX, bulletPosY, gunVector
    global gunVectorDeltaFineA, gunVectorDeltaCoarseA, gunVectorDeltaFine, gunVectorDeltaCoarse
    global hit_reward, reward_pointing_near_target, gun_ready_reward
    global sio

    # AI Param
    manaul_ctrl = False
    last_reward = 0
    rocketXpos = 0
    rocketYpos = 0

    # DQN Network Initialization
    sliding_window_scores = []
    dqnShooting = ai_network.Dqn(4, 5, 0.75)

    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("2D MultiAI Playground")
    paramDisplay = pygame.font.Font('freesansbold.ttf', 22, )

    running = True
    player = Soldier(100, 250, False)

    move_type = MoveType.UP_DOWN
    target = Target(600, 100, move_type=move_type)

    player.set_target(target)
    soldier_group = pygame.sprite.Group()
    soldier_group.add(player)

    rocket_group = pygame.sprite.Group()

    while running:
        # set game to 30fps
        pygame.time.delay(33)

        hit_reward = 0
        reward_pointing_near_target = 0
        gun_ready_reward = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    sio_update(f"last_reward: {last_reward}")

                    dqnShooting.save(SHOOTING_AI_NETWORK)
                    plt.plot(sliding_window_scores)
                    plt.show()
                elif event.key == pygame.K_DOWN:
                    dqnShooting.load(SHOOTING_AI_NETWORK)
                elif event.key == pygame.K_m:
                    manaul_ctrl = not manaul_ctrl
                elif event.key == pygame.K_a and manaul_ctrl:
                    ai_control(0, rocket_group, player)
                elif event.key == pygame.K_s and manaul_ctrl:
                    ai_control(1, rocket_group, player)
                elif event.key == pygame.K_d and manaul_ctrl:
                    ai_control(2, rocket_group, player)
                elif event.key == pygame.K_f and manaul_ctrl:
                    ai_control(3, rocket_group, player)
                elif event.key == pygame.K_SPACE and manaul_ctrl:
                    if not is_Fired:
                        rocket_group.add(player.shoot_angle(gunVector))
                        is_Fired = True

        # collision detection for all spawned rockets
        for rocket in rocket_group.sprites():
            hit, sprite = rocket.update()

            rocketXpos = rocket.rect.x
            rocketYpos = rocket.rect.y

            if hit:
                rocket_group.remove(rocket)
                hit_reward = HIT_REWARD
                is_Fired = False
                if sprite == target:
                    move_type = random.randint(0, 3)

                    # starts player at center of screen if circular movement
                    if move_type == MoveType.CIRCLE:
                        player.setpos(350, 250)
                        target = Target(350, 250, move_type=move_type)

                    else:
                        player.setpos(100, 250)
                        target = Target(600, 100, move_type=move_type)

                    player.set_target(target)
                    rocket_group.empty()
                    print("Player wins!")

            elif rocket.is_out_of_bounds():
                rocket_group.remove(rocket)
                hit_reward = MISS_PENALTY
                is_Fired = False

        # Player & Target positional update
        # player.setpos(, )
        target.move()

        # Update AI Input
        if is_Fired:
            bulletPosX = rocketXpos
            bulletPosY = rocketYpos
        else:
            bulletPosX = player.rect.x
            bulletPosY = player.rect.y

        deltaY = target.rect.y - player.rect.y
        deltaX = target.rect.x - player.rect.x
        anglePlayerToEnemy = (math.atan2(
            abs(deltaY), abs(deltaX)) * 180 / math.pi)
        # print(anglePlayerToEnemy)

        # First Quadrant
        if deltaY < 0 and deltaX > 0:
            anglePlayerToEnemy = 90 - anglePlayerToEnemy
        # Second Quadrant
        elif deltaY > 0 and deltaX > 0:
            anglePlayerToEnemy = 90 + anglePlayerToEnemy
        # Third Quadrant
        if deltaY > 0 and deltaX < 0:
            anglePlayerToEnemy = 180 + (90 - anglePlayerToEnemy)
        # Fourth Quadrant
        elif deltaY < 0 and deltaX < 0:
            anglePlayerToEnemy += 270

        if deltaY == 0 and deltaX > 0:
            anglePlayerToEnemy = 90
        elif deltaY == 0 and deltaX < 0:
            anglePlayerToEnemy = 270
        elif deltaY > 0 and deltaX == 0:
            anglePlayerToEnemy = 180
        elif deltaY < 0 and deltaX == 0:
            anglePlayerToEnemy = 0

        distancePlayerToEnemy = (
            (((target.rect.x - player.rect.x) ** 2) + ((target.rect.y - player.rect.y) ** 2)) ** 0.5)

        # Reward Management
        if abs(anglePlayerToEnemy - gunVector) <= 30:
            reward_pointing_near_target = POINTING_GUN_AT_TARGET_REWARD
        last_reward = reward_pointing_near_target + \
            gun_ready_reward + hit_reward + LIVING_PENALTY

        # DQN update
        if not manaul_ctrl:
            last_state = [is_Fired, (anglePlayerToEnemy / 360.0),
                          (gunVector / 360.0), (distancePlayerToEnemy / 1000.0)]
            # print(last_state)
            # print(last_reward)
            next_action = dqnShooting.update(last_reward, last_state)
            avg_score = dqnShooting.overall_score()
            sliding_window_scores.append(avg_score)
            ai_control(next_action, rocket_group, player)

        screen.fill((0, 0, 0))
        rocket_group.draw(screen)
        soldier_group.draw(screen)
        player.draw_firing_angle(screen, gunVector)
        player.draw_firing_angle(screen, anglePlayerToEnemy)
        display_input_param(screen, 0, 0, paramDisplay, avg_score)
        screen.blit(target.image, target.rect)

        pygame.display.update()

    pygame.quit()
    sio.disconnect()


def sio_connect():
    """Creates a connection with the socketio server
    """

    global sio
    sio.connect(f"http://{HOST_IP_ADDRESS}:{HOST_UPDATE_PORT}")
    print("Connected to socket server, SID:", sio.sid)


def sio_update(info: str):
    """Updates socketio server with latest information

    Args:
        data (str): [description]
    """

    global sio

    data = {
        "learn_id": learn_id,
        "info": info
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


if __name__ == "__main__":
    t1 = threading.Thread(target=main)
    t1.start()
    sio_connect()
