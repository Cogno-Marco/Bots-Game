from enum import Enum
from typing import Final, List, Tuple, Dict
from random import sample
from rich.text import Text as ColoredText
from rich.console import Console
from time import sleep
import os
import sys

"""
WORLD VERSION: 1.1.1
"""


class AppState(Enum):
    WAITING_FOR_CONNECTION_B1 = object()
    WAITING_FOR_CONNECTION_B2 = object()
    WRITING_LAST_STATE = object()
    WAITING_CMD_B1 = object()
    WAITING_CMD_B2 = object()


class MatchResult(Enum):
    DRAW = 0
    WIN_PLAYER1 = 1
    WIN_PLAYER2 = 2


class Vec:
    def __init__(self, x: int | List[int] | Tuple[int, int], y: int = -1):
        if type(x) in [list, tuple]:
            self.x: int = x[0]
            self.y: int = x[1]
        else:
            self.x: int = x
            self.y: int = y

    def __add__(self, cell2: 'Vec'):
        return Vec(self.x + cell2.x, self.y + cell2.y)

    def __sub__(self, cell2: 'Vec'):
        return Vec(self.x - cell2.x, self.y - cell2.y)

    def __str__(self):
        return f"{self.x} {self.y}"


class Resource:
    def __init__(self, position: Vec) -> None:
        self.health: int = 3
        self.position: Vec = position
        self.hit_by: List[Player] = []


class Player:
    def __init__(self, spawn_pos) -> None:
        self.resources: int = 0
        self.troops: List[Troop] = []
        self.spawn_pos: Vec = spawn_pos


class Troop:
    def __init__(self, troop_ID, owner: Player, position: Vec) -> None:
        self.id: int = troop_ID
        self.owner: Player = owner
        self.position: Vec = position
        self.health: int = 2
        self.move_speed: int = 1
        self.damage: int = 1
        self.has_hit: bool = False

        # add the troop to the player's troop list
        owner.troops.append(self)


class Map:
    def __init__(self, width: int, height: int):
        self.width: int = width
        self.height: int = height
        self.map: List[List[None | Troop | Resource]] = [[None for _ in range(self.width)] for _ in range(self.height)]

    def get_cell(self, pos: Vec) -> None | Troop | Resource:
        true_cell = (map_height - pos.y - 1, pos.x)
        return self.map[true_cell[0]][true_cell[1]]

    def set_cell(self, pos: Vec, obj: None | Resource | Troop):
        true_cell = (map_height - pos.y - 1, pos.x)
        self.map[true_cell[0]][true_cell[1]] = obj

    def print_formatted(self, player1, player2):
        texts = ColoredText()

        for row in self.map:
            for cell in row:
                if type(cell) is Resource:
                    texts.append("o ", style="green")
                if type(cell) is Troop and cell.owner is player1:
                    texts.append("X ", style="blue")
                if type(cell) is Troop and cell.owner is player2:
                    texts.append("X ", style="red")
                if cell is None:
                    texts.append("- ", style="white")
            texts.append("\n")

        console.print(texts)

    def copy(self):
        m = Map(self.width, self.height)
        m.map = [[cell for cell in row] for row in self.map]
        return m

    def is_outside(self, pos: Vec) -> bool:
        return pos.x < 0 or pos.x >= self.width or pos.y < 0 or pos.y >= self.height


def debug_log(text, map_to_show: Map, player1, player2):
    if not debug:
        return

    # clear terminal and write map
    os.system('cls' if os.name == 'nt' else 'clear')
    map_to_show.print_formatted(player1, player2)
    console.print(text)
    sleep(sleep_time)


def movement_str_to_vec(dir_):
    match dir_:
        case "up":
            return 0, 1
        case "down":
            return 0, -1
        case "left":
            return -1, 0
        case "right":
            return 1, 0
        case _:
            return 0, 0


def get_troop_from_id(troop_ID, player_) -> Troop | None:
    for troop in player_.troops:
        if troop.id == troop_ID:
            return troop
    return None


def compute_movement(cmds_move, next_frame, actions_logging):
    # remove invalid movements
    for i in range(len(cmds_move))[::-1]:
        troop: Troop
        movement: Vec
        amount: int
        troop, movement, amount = cmds_move[i]
        if troop is None:  # I'm trying to move a troop I don't have control of (it doesn't exist, or it's the enemy's troop)
            cmds_move.pop(i)
            continue

    # remove duped move commands
    valid_cmds: List[Tuple[Troop | None, Vec, int]] = []
    ids_found: List[int] = []
    for troop, vec, amount in cmds_move:
        if troop.id not in ids_found:
            ids_found.append(troop.id)
            valid_cmds.append((troop, vec, amount))
    cmds_move = valid_cmds

    moved_troops: Dict[Troop, Vec] = {}

    while len(cmds_move) > 0:
        for i in range(len(cmds_move))[::-1]:  # NOTE: reverse order, so we can edit the list while working on it
            troop: Troop
            movement: Vec
            amount: int
            troop, movement, amount = cmds_move[i]

            # clamp in [0, move_speed]
            amount = max(0, min(amount, troop.move_speed))
            if amount <= 0:
                cmds_move.pop(i)
                continue

            # work here
            target_pos: Vec = troop.position + movement
            # trying to get off map, stop and finish command
            if next_frame.is_outside(target_pos):
                cmds_move.pop(i)
                continue
            target_cell = next_frame.get_cell(target_pos)

            # getting into a position filled by a resource = stop movement
            if type(target_cell) == Resource:
                cmds_move.pop(i)
                continue

            # trying to move in an occupied position
            if type(target_cell) == Troop:
                cmds_move.pop(i)
                continue

            # move by 1 cell
            next_frame.set_cell(troop.position, None)
            next_frame.set_cell(target_pos, troop)
            troop.position = target_pos
            cmds_move[i] = (troop, movement, amount - 1)

            # add moved amount to temp list, used for logging
            if troop not in moved_troops:
                moved_troops[troop] = troop.position - movement

    # logging
    for troop, start_position in moved_troops.items():
        for k in actions_logging:
            if k == troop.owner:
                actions_logging[k].append(f"action troop ally {troop.id} {start_position} move {troop.position}")
            else:
                actions_logging[k].append(f"action troop enemy {troop.id} {start_position} move {troop.position}")

    del moved_troops


def compute_actions(cmds_action, next_frame, actions_logging):
    resources_hit: List[Resource] = []
    for troop, movement in cmds_action:
        if troop is None:
            continue

        target_pos = troop.position + movement
        target_cell = next_frame.get_cell(target_pos)
        if not troop.has_hit:
            troop.has_hit = True

            if type(target_cell) is Troop:
                target_cell.health -= troop.damage
                # destroy troop
                if target_cell.health <= 0:
                    next_frame.set_cell(target_pos, None)
                    target_cell.owner.troops.remove(target_cell)

                for k in actions_logging:
                    if k == troop.owner:
                        actions_logging[k].append(f"action troop ally {troop.id} {troop.position} attack {target_pos}")
                    else:
                        actions_logging[k].append(f"action troop enemy {troop.id} {troop.position} attack {target_pos}")
            elif type(target_cell) is Resource:
                target_cell.health -= troop.damage
                resources_hit.append(target_cell)
                # whoever destroys the resource cell, get the resources (health, for now)
                target_cell.hit_by.append(troop.owner)
                for k in actions_logging:
                    if k == troop.owner:
                        actions_logging[k].append(f"action troop ally {troop.id} {troop.position} harvest {target_pos}")
                    else:
                        actions_logging[k].append(f"action troop enemy {troop.id} {troop.position} harvest {target_pos}")

    # resets hit action of troops
    for troop, movement in cmds_action:
        troop.has_hit = False

    for resource in resources_hit:
        if resource.health <= 0:
            destroyed_by = list(set(resource.hit_by))
            next_frame.set_cell(resource.position, None)
            for owner in destroyed_by:
                owner.resources += round(gain_per_resource / len(destroyed_by), 2)
        else:
            resource.hit_by.clear()

    # count resources in map
    resources_count = 0
    for row in next_frame.map:
        for cell in row:
            if type(cell) == Resource:
                resources_count += 1

    if resources_count < max_resources:
        empty_spots: List[Vec] = []
        for x in range(map_width):
            for y in range(map_height):
                pos: Vec = Vec(x, y)

                if next_frame.get_cell(pos) is None:
                    empty_spots.append(pos)

        chosen_spots: List[Vec] = sample(empty_spots, max_resources - resources_count)
        for pos in chosen_spots:
            next_frame.set_cell(pos, Resource(pos))


def compute_powerup(cmds_powerup, actions_logging):
    for troop, powerID in cmds_powerup:
        if troop is None:
            continue

        if troop.owner.resources < troop_powerup_cost:  # not enough to buy an upgrade
            continue

        match powerID:
            case "health":
                troop.health += 1
            case "speed":
                troop.move_speed += 1
            case "damage":
                troop.damage += 1

        troop.owner.resources -= troop_powerup_cost

        for k in actions_logging:
            if k == troop.owner:
                actions_logging[k].append(f"action troop ally {troop.id} {troop.position} powerup {powerID}")
            else:
                actions_logging[k].append(f"action troop enemy {troop.id} {troop.position} powerup {powerID}")


def compute_create(cmds_create, next_frame, troop_id, actions_logging):
    for player in cmds_create:
        # check if the player has enough resources and the cell is not blocked
        if player.resources >= troop_creation_cost and next_frame.get_cell(player.spawn_pos) is None and len(player.troops) < max_troops:
            troop_id += 1
            next_frame.set_cell(player.spawn_pos, Troop(troop_id, player, player.spawn_pos))
            player.resources -= troop_creation_cost
            for k in actions_logging:
                if k == player:
                    actions_logging[k].append(f"action troop ally {troop_id} spawn")
                else:
                    actions_logging[k].append(f"action troop enemy {troop_id} spawn")

    return troop_id


def play_game():
    print("match started...")

    current_state = AppState.WAITING_FOR_CONNECTION_B1
    world_map: Map = Map(map_width, map_height)
    is_match_ended = False
    match_result = None

    player1: Player = Player(b1_spawn)
    player2: Player = Player(b2_spawn)

    b1_cmds: List[str] = []
    b2_cmds: List[str] = []

    turn = 0
    troop_id = -1

    # clean channels (or create them if they don't exist)
    with open(channel1, "w") as f:
        f.write("spawn_pos 2 2\nmatch_start")
    with open(channel2, "w") as f:
        f.write("spawn_pos 8 8\nmatch_start")

    while current_state == AppState.WAITING_FOR_CONNECTION_B1:
        with open(channel1, "r") as f:
            data = f.read()

        if "ready" in data:
            debug_log("b1 is ready", world_map, player1, player2)
            # gen the player and the first troop
            troop_id += 1
            world_map.set_cell(b1_spawn, Troop(troop_id, player1, b1_spawn))
            current_state = AppState.WAITING_FOR_CONNECTION_B2
        else:
            debug_log("waiting for b1", world_map, player1, player2)

    while current_state == AppState.WAITING_FOR_CONNECTION_B2:
        with open(channel2, "r") as f:
            data = f.read()

        if "ready" in data:
            debug_log("b2 is ready", world_map, player1, player2)
            # gen the player and the first troop
            troop_id += 1
            world_map.set_cell(b2_spawn, Troop(troop_id, player2, b2_spawn))
            current_state = AppState.WRITING_LAST_STATE
        else:
            debug_log("waiting for b2", world_map, player1, player2)

    while turn < max_turns and not is_match_ended:
        match current_state:
            case AppState.WRITING_LAST_STATE:
                # work on every command
                all_cmds: List[Tuple[str, Player]] = [(x, player2) for x in b2_cmds] + [(x, player1) for x in b1_cmds]
                actions_logging: Dict[Player, List[str]] = {player1: [], player2: []}

                cmds_move: List[Tuple[Troop | None, Vec, int]] = []
                cmds_action: List[Tuple[Troop | None, Vec]] = []
                cmds_powerup: List[Tuple[Troop | None, int]] = []
                cmds_create: List[Player] = []

                # filter only useful commands
                for cmd, player in all_cmds:
                    match cmd.split(" "):
                        case ["move", troopID, ("up" | "down" | "left" | "right") as direction, amount] if troopID.isnumeric() and amount.isnumeric():
                            cmds_move.append((get_troop_from_id(int(troopID), player), Vec(movement_str_to_vec(direction)), int(amount)))

                        case ["action", troopID, ("up" | "down" | "left" | "right") as direction] if troopID.isnumeric():
                            cmds_action.append((get_troop_from_id(int(troopID), player), Vec(movement_str_to_vec(direction))))

                        case ["powerup", troopID, ("health" | "speed" | "damage") as powerID] if troopID.isnumeric():
                            cmds_powerup.append((get_troop_from_id(int(troopID), player), powerID))

                        case ["create"] if player.resources >= troop_creation_cost:
                            cmds_create.append(player)

                # copy to have edits
                next_frame: Map = world_map.copy()

                # compute all the troops actions in order
                compute_movement(cmds_move, next_frame, actions_logging)
                compute_actions(cmds_action, next_frame, actions_logging)
                compute_powerup(cmds_powerup, actions_logging)
                troop_id = compute_create(cmds_create, next_frame, troop_id, actions_logging)

                # paste edits into map
                world_map = next_frame.copy()
                debug_log("COMMANDS COMPLETED: NEW FRAME", world_map, player1, player2)

                # collect resources info
                resources_txt = ""
                for row in world_map.map:
                    for cell in row:
                        if type(cell) == Resource:
                            resource: Resource = cell
                            resources_txt += f"resource {resource.position.x} {resource.position.y} {resource.health} {gain_per_resource}\n"

                # send messages to troops
                with open(channel1, "w") as f:
                    troops_actions = ""
                    for troop in player1.troops:
                        troops_actions += f"troop ally {troop.id} {troop.position} {troop.health} {troop.move_speed} {troop.damage}\n"
                    for troop in player2.troops:
                        troops_actions += f"troop enemy {troop.id} {troop.position} {troop.health} {troop.move_speed} {troop.damage}\n"
                    event_actions = '\n'.join(actions_logging[player1])
                    f.write(f"turn {turn} {round(float(player1.resources), 2)}\n{troops_actions}{resources_txt}{event_actions}\nworld_done")

                with open(channel2, "w") as f:
                    troops_actions = ""
                    for troop in player2.troops:
                        troops_actions += f"troop ally {troop.id} {troop.position} {troop.health} {troop.move_speed} {troop.damage}\n"
                    for troop in player1.troops:
                        troops_actions += f"troop enemy {troop.id} {troop.position} {troop.health} {troop.move_speed} {troop.damage}\n"
                    event_actions = '\n'.join(actions_logging[player2])
                    f.write(f"turn {turn} {round(float(player2.resources), 2)}\n{troops_actions}{resources_txt}{event_actions}\nworld_done")

                if len(player1.troops) == 0 and len(player2.troops) == 0:
                    print(f"Ended at turn {turn}!")
                    print("Draw!")
                    is_match_ended = True
                    match_result = MatchResult.DRAW
                elif len(player2.troops) == 0:
                    print(f"Ended at turn {turn}!")
                    print("Player 1 Win!")
                    is_match_ended = True
                    match_result = MatchResult.WIN_PLAYER1
                elif len(player1.troops) == 0:
                    print(f"Ended at turn {turn}!")
                    print("Player 2 Win!")
                    is_match_ended = True
                    match_result = MatchResult.WIN_PLAYER2

                # visualization
                b1_cmds.clear()  # clear for next round
                b2_cmds.clear()  # clear for next round
                turn += 1
                current_state = AppState.WAITING_CMD_B1
                if not debug:
                    print(f"TURN: {str(turn).rjust(4, ' ')}/1000")

            case AppState.WAITING_CMD_B1:
                with open(channel1, "r") as f:
                    data = f.read()

                if "end_turn" in data:
                    for cmd in data.split("\n"):
                        if cmd == "end_turn":
                            break
                        b1_cmds.append(cmd)
                    debug_log(f"b1 commands list: {b1_cmds}", world_map, player1, player2)

                    current_state = AppState.WAITING_CMD_B2
                else:
                    debug_log("waiting for b1 cmd", world_map, player1, player2)

            case AppState.WAITING_CMD_B2:
                with open(channel2, "r") as f:
                    data = f.read()

                if "end_turn" in data:
                    for cmd in data.split("\n"):
                        if cmd == "end_turn":
                            break
                        b2_cmds.append(cmd)
                    debug_log(f"b2 commands list: {b2_cmds}", world_map, player1, player2)
                    current_state = AppState.WRITING_LAST_STATE
                else:
                    debug_log("waiting for b2 cmd", world_map, player1, player2)

    # cases when reaching turn 1000
    if not is_match_ended:
        print(f"Ended at turn {turn}!")

        if player1.resources > player2.resources:
            print("Player 1 Win!")
            match_result = MatchResult.WIN_PLAYER1
        elif player2.resources > player1.resources:
            print("Player 2 Win!")
            match_result = MatchResult.WIN_PLAYER2
        else:
            print("Draw!")
            match_result = MatchResult.DRAW

    print(f"Player 1 Resources: {player1.resources}")
    print(f"Player 2 Resources: {player2.resources}")

    with open(channel1, "w") as f:
        f.write("end_match")
    with open(channel2, "w") as f:
        f.write("end_match")

    with open("result.txt", "w") as f:
        f.write(f"game_ended\n{match_result.name}")


if __name__ == '__main__':
    # CONFIGS
    console: Final[Console] = Console()
    b1_spawn: Final[Vec] = Vec(2, 2)
    b2_spawn: Final[Vec] = Vec(8, 8)
    map_width: Final[int] = 11
    map_height: Final[int] = 11
    max_troops: Final[int] = 10
    troop_creation_cost: Final[int] = 5
    troop_powerup_cost: Final[int] = 3
    max_resources: Final[int] = 10
    gain_per_resource: Final[int] = 6
    max_turns: Final[int] = 1000
    channel1: Final[str] = "channel1.txt"
    channel2: Final[str] = "channel2.txt"

    # debug stuff
    sleep_time: float
    debug: bool


    def is_float(val) -> bool:
        try:
            float(val)
            return True
        except ValueError:
            return False


    # get bots names from command line arguments
    match sys.argv:
        case [_, "True", debug_speed] if is_float(debug_speed):
            print(f"received debug command: True, {debug_speed}")
            debug = True
            sleep_time = float(debug_speed)
        case [_, "False", debug_speed] if is_float(debug_speed):
            print(f"received debug command: False, {debug_speed}")
            debug = False
            sleep_time = float(debug_speed)
        case _:
            print(f"no command received (or received incorrectly), playing in debug mode")
            debug = True
            sleep_time = 0.3
    play_game()
