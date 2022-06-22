# API VERSION 1.1.2


# Game Rules
On the game world, there are troops and resources.
There are 2 win conditions:
1. destroy each enemy troop before turn 1000
2. have more resources than the enemy at exactly turn 1000
If both enemy troops are destroyed in the same turn, or if both players have the same resources at the final turn, the game is considered a draw.

Resources are also used to spawn new ally troops or to level up their statistics.

The world is a 11x11 grid, with coordinate (0,0) in the bottom left corner.
Player 1 spawn position is at (2, 2).
Player 2 spawn position is at (8, 8).

Each player can:
1. Move each troop once per turn
2. Use each troop to attack enemy troops or resources
3. Improve how many troop statistics you want, consuming resources in the process. Each troop can be upgraded multiple times, even the same statistic.
4. Spawn at most 1 new troop per turn, consuming resources in the process. You can control at most 10 troops at the same time.


# API Basics
Players and world alternate between reading and writing data into a txt called a "channel".
Your bot will receive the name of the txt as a command line argument when started.
Each turn you'll be able to read the latest state of the game and to write your commands for this turn.

Inside the channel you'll immediately read a `spawn_pos <x> <y>` information, telling you what your spawn position is, followed by a `match_start`command.
When your bot is ready to start you should write `ready` inside the same channel. You might overwrite previous information without any problem, the game will do the same in the following turns.

After the `ready` command is accepted from bot players the world will start the game, writing for each turn the latest state of the game and the latest important events.
The game always finishes writing data with a "world_done" statement, you'll then be able to write your own commands (see below for more information).
Players always should finish writing data with an "end_turn" statement, so the world can calculate what happens and pass to the next turn, replying with new data.
When the game is finished you'll read a `end_match` statement. You might safely close your bot or ignore it as you please.


# PLAYER COMMANDS
- move <troopID> <direction> <amount>:
    moves a troop in a straight line in a given direction by a given number of steps. Each troop can only move once per turn. If multiple move command with the same id are given, only the first one will be executed. If an obstacle is found while moving the troop will collide with the obstacle, meaning each cell can only be occupied by 1 troop or 1 resource at the same time.
    <troopID>: integer number which uniquely identifies the troop to move
    <direction>: one of "up", "down", "left", "right"
    <amount>: integer number [0, maxSpeed] of how many steps to take in that direction, if amount is more than the troop's movement speed, the troop will only move by its max speed
    example:
        move 0 right 1
        move 1 up 5

- action <troopID> <direction>:
    lets a troop attacks or harvests in a given direction. Each troop can only make an action once per turn. If multiple action commands with the same id are given, only the first one will be executed
    The troop attacks a cell directly in front him. If the cell is an enemy troop or a resource, damage is inflicted, based on the troops damage stat. If a resource is destroyed each player who attacked the resource in this turn will be awarded with a portion of the resource value. Each resource grants 6 resource points.
    <troopID>: integer number which uniquely identifies the troop which attacks/harvests
    <direction>: one of "up", "down", "left", "right"
    example:
        action 0 right
        action 1 up

- powerup <troopID> <powerID>:
    powers up a troop statistic, consuming 3 resources. If the player doesn't have enough resources the powerup command is ignored. You can powerup how many times you want in a single turn.
    <troopID>: integer number which uniquely identifies the troop to powerup
    <powerID>: one of "health", "speed" or "damage":
        health -> increases current HP by 1
        speed  -> increases current Move Speed by 1
        damage -> increases current Damage by 1

- create:
    creates a new troop at the player spawn position, consuming 5 resources. If the player doesn't have enough resources the create command is ignored. If the spawn position is occupied by something the command will be ignored. Because of this you might spawn at most 1 troop per turn. You can control at most 10 troops at the same time.

- end_turn:
    finishes a turn. Other commands sent after this are ignored. Turn doesn't resume until end_turn is written by both players into each channel.


# WORLD EVENTS
- turn <n> <resources>
    tells the current turn number
    <n>: integer of current turn
    <resources>: float amount of resources the player has

- troop <team> <botID> <x_position> <y_position> <health> <move_speed> <damage>
    tells information on a troop in the game
    <team>: "ally" or "enemy", your bots are always "ally"
    <botID>: integer number [0, n] where n is how many bots that team has
    <x_position>: the troop's x position in range [0, w] as an integer
    <y_position>: the troop's y position in range [0, h] as an integer
    <health>: the troop's health as an integer
    <move_speed>: the troop's move speed as an integer, see troop's move command for more info
    <damage>: the troop's damage as an integer, see troop's action command for more info
    example:
        troop ally 0 2 2 2 1 1
        troop enemy 1 8 8 2 1 1
    
- resource <x_position> <y_position> <health> <gain>
    tells information on a resource in the game
    <x_position>: the resource's x position in range [0, w] as an integer
    <y_position>: the resource's y position in range [0, h] as an integer
    <health>: integer health remaining of the resource
    <gain>: integer amount of resource gained when destroyed

- action <action>
    tells the last meaningful actions
    examples:
        "action troop ally 1 10 20 move 11 20"
        "action troop ally 1 10 20 harvest 11 20"
        "action troop ally 1 10 20 attack 11 20"
        "action troop enemy 2 4 6 powerup damage"
        "action troop enemy 2 spawn"
    formats:
        "action troop" <team> <troopID> <x_position> <y_position> <move | harvest | attack> <x_target> <y_target>
        "action troop" <team> <troopID> <x_position> <y_position> "powerup" <damage | health | speed>
        "action troop" <team> <troopID> "spawn"

- world_done
    tells the player the world's turn has ended, meaning the bot can now write into the channel his actions for the turn

- end_match
    tells the player the match has finished. The bot may safely close after having read this command. If the bot is not closed after some time it will be closed automatically


# Running the game
## World Executable (windows only)
To run your bots and play your game locally:
- open a first console, then start a world game with the command `./world.py <debug> <print_speed>` where <debug> = "True" or "False" and <print_speed> is a float from 0 to n, where n is the number of seconds to wait before writing the next important event to console.
- open a second console, then start a bot accordingly
  - if the bot is yours you might start it as required
  - if the bot is a python script use the command `python <bot_name>.py channel1.txt`
  - if the bot is an exe use the command `./<bot_name>.exe channel1.txt`
- open a third console with the other bot to play against, sending the `channel2.txt` instead


## World Python version
Requirements:
python version 3.10.4
pip install rich
a coding language that can
- accept command line arguments as input
- read and write txt files


# Sending us your bot
To let the bot be able to play competitively you should send us its source code (we don't trust executables!)
