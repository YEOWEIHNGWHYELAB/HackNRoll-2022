import pygame
from matplotlib import pyplot as plt

from network import Network

from units import Soldier
from units import Rocket
import ai_network
import const
import server.server_const
from const import SHOOTING_AI_NETWORK, MOVEMENT_AI_NETWORK

# State Const
INDEX_OF_IS_FIRED = 2

# Movement Reward Const
MOVEMENT_LIVING_PENALTY = -0.3
HIT_PENALTY = -1.0
NEAR_ENEMY_REWARD = 0.2
DODGE_REWARD = 1.0

# Shooting Reward Const
MISS_PENALTY = -0.02
FIRING_NOT_READY_PENALTY = -0.01
SHOOTING_LIVING_PENALTY = -0.3
HIT_REWARD = 1
FIRING_REWARD = 0.2
POINTING_GUN_AT_TARGET_REWARD = 0.01

# Gun Vector Adjust
gunVectorDeltaFineA = 1
gunVectorDeltaCoarseA = 20
gunVectorDeltaFine = -1
gunVectorDeltaCoarse = -20

# Initialize Movement Param
enemyPosX = 0
enemyPosY = 0
enemyBulletX = 0
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


def cal_shooting_reward():
    pass


def cal_movement_reward(playerPosX, playerPosY):
    global hit_dodge_reward, near_enemy_reward
    edgePenalty = 0

    if playerPosX >= 700 or playerPosX <= 30:
        edgePenalty = -0.5
    elif playerPosY >= 500 or playerPosY <= 30:
        edgePenalty = -0.5

    final_movement_reward = hit_dodge_reward + near_enemy_reward + MOVEMENT_LIVING_PENALTY + edgePenalty

    return final_movement_reward


def ai_firing(rocket_group, player):
    rocket_group.add(player.shoot_angle(gunVector))


def ai_shoot(next_action, rocket_group, player):
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


def draw_window(screen, soldier_group, player_rocket, enemy_fired, enemy_rocket):
    screen.fill((0, 0, 0))
    soldier_group.draw(screen)

    if player_rocket is not None:
        player_rocket.draw(screen)

    if enemy_fired and enemy_rocket is not None:
        enemy_rocket.draw(screen)


def display_not_ready(screen, x, y, font):
    screen.fill((0, 0, 0))
    not_ready = font.render("WAITING FOR PLAYER!", True, (255, 255, 255))
    screen.blit(not_ready, (x, y))


def main():
    # Shooting Global Var
    global is_Fired, gunVector, anglePlayerToEnemy, distancePlayerToEnemy, bulletPosX, bulletPosY
    global gunVectorDeltaFineA, gunVectorDeltaCoarseA, gunVectorDeltaFine, gunVectorDeltaCoarse
    global hit_reward, reward_pointing_near_target, gun_ready_reward

    # Movement Global Var
    global enemyPosX, enemyPosY, playerPosX, playerPosY, enemyBulletX, enemyBulletY
    global hit_dodge_reward, near_enemy_reward
    enemy_fired = False

    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("2D MultiAI Playground")
    not_ready_disp = pygame.font.Font('freesansbold.ttf', 60, )

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

    # DQN Network Initialization
    manaul_ctrl = False
    sliding_window_scores_Move = []
    sliding_window_scores_Shoot = []
    last_reward_movement = 0
    # last_reward_shooting = 0
    dqnMovement = ai_network.Dqn(6, 4, 0.75)
    # dqnShooting = ai_network.Dqn(4, 5, 0.75)

    # Initialize Data
    initial_state = [(server.server_const.START_POS_P1_X, server.server_const.START_POS_P1_Y, False, 0, 0, -1),
                     (server.server_const.START_POS_P2_X, server.server_const.START_POS_P2_Y, False, 0, 0, -1)]

    # Player & Enemy Initialization
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

    # Polling for second player.
    while not_ready:
        clock.tick(1000)
        display_not_ready(screen, 50, 250, not_ready_disp)
        ready_status = network.send("1")
        not_ready_int = int(ready_status)
        pygame.display.update()
        if not_ready_int == 1:
            not_ready = False
            print("Ready!")

    # Main Loop
    while running:
        # set game to 30fps
        clock.tick(30)

        # Button and Manual Firing
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and is_fired is False:
                    dest = pygame.mouse.get_pos()
                    is_fired = True
                    player_rocket = player.shoot(dest)
                    rocket_angle = int(player_rocket.angle)
                # Saving DQN network
                elif event.button == 2:
                    # dqnShooting.save(SHOOTING_AI_NETWORK)
                    # plt.plot(sliding_window_scores_Shoot)
                    # plt.xlabel('Number of Iteration', fontsize=18)
                    # plt.ylabel('Average Reward', fontsize=16)
                    # plt.show()
                    dqnMovement.save(MOVEMENT_AI_NETWORK)
                    plt.plot(sliding_window_scores_Move)
                    plt.xlabel('Number of Iteration', fontsize=18)
                    plt.ylabel('Average Reward', fontsize=16)
                    plt.show()
                # Loading DQN network
                elif event.button == 3:
                    # dqnShooting.load(SHOOTING_AI_NETWORK)
                    dqnMovement.load(MOVEMENT_AI_NETWORK)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    manaul_ctrl = not manaul_ctrl

        # Player Rocket Management
        if player_rocket is not None:
            hit, target = player_rocket.update()

            rocket_X = player_rocket.rect.x
            rocket_Y = player_rocket.rect.y

            if hit:
                player_rocket = None
                is_fired = False

            elif player_rocket.is_out_of_bounds():
                player_rocket = None
                is_fired = False

        # Send Server and Receive Updates
        player_state = game_data_to_string([player.rect.x, player.rect.y,
                                            is_fired, rocket_X, rocket_Y, rocket_angle])
        enemy_state = network.send(player_state)
        enemy_state = read_game_data(enemy_state)
        enemy.setpos(enemy_state[0], enemy_state[1])

        # Check did enemy fire
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
                print(enemy_rocket)
                if pygame.sprite.collide_rect(player, enemy_rocket):
                    hit_dodge_reward = -1.0
                    enemy_fired = False
                # Went out of bound
                else:
                    hit_dodge_reward = 1.0
                    enemy_fired = False

        # Update Movement Param
        enemyPosX = enemy_state[0]
        enemyPosY = enemy_state[1]
        playerPosX = player.rect.x
        playerPosY = player.rect.y

        # Update Shooting Param
        distancePlayerToEnemy = ((((enemyPosX - playerPosX) ** 2) + ((enemyPosY - playerPosY) ** 2)) ** 0.5)

        # Update Rewards
        if distancePlayerToEnemy <= 300:
            near_enemy_reward = 0.2
        else:
            near_enemy_reward = -0.1
        last_reward_movement = cal_movement_reward(playerPosX, playerPosY)
        print(near_enemy_reward, hit_dodge_reward)
        # last_reward_shooting = cal_shooting_reward()

        # last_state update
        last_state_movement = [enemyPosX, enemyPosY, enemyBulletX, enemyBulletY, playerPosX, playerPosY]
        # last_state_shooting = [is_Fired, anglePlayerToEnemy, gunVector, distancePlayerToEnemy]
        # print(last_state_movement)
        # print(last_state_shooting)

        # Toggle AI control and manual control
        if not manaul_ctrl:
            next_action_movement = dqnMovement.update(last_reward_movement, last_state_movement)
            avg_score_movement = dqnMovement.overall_score()
            sliding_window_scores_Move.append(avg_score_movement)
            player.ai_move(next_action_movement)

            # next_action_shooting = dqnShooting.update(last_reward_shooting, last_state_shooting)
            # avg_score_shoot = dqnShooting.overall_score()
            # sliding_window_scores_Shoot.append(avg_score_shoot)
            # ai_shoot(next_action_shooting)
        else:
            player.manual_move()


        # Draw onto screen
        draw_window(screen, soldier_group, player_rocket,
                    enemy_state[INDEX_OF_IS_FIRED], enemy_rocket)
        pygame.display.update()

    pygame.quit()


if __name__ == "__main__":
    main()
