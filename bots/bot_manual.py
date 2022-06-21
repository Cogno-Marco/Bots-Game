import sys
from typing import List, Tuple, Final

"""
BOT VERSION: 1.1.1
"""

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
    
    def value(self):
        return (self.x, self.y)

channel = ""
match sys.argv:
    case [_, str(filename)] if filename.endswith(".txt"):
        channel = filename
    case [_, str(filename)]:
        channel = f"{filename}.txt"
    case _:
        print("First command must be che name of the txt to use as a channel")
        sys.exit()

# read spawn position from file
with open(channel, "r") as f:
    data = f.read().split("\n")
spawn_pos = [2, 2]
for row in data:
    if "spawn_pos" in row:
        spawn_pos = list(map(int, row.split(" ")[1::]))

with open(channel, "w") as f:
    f.write("ready")

can_write = False
resources: float = 0
allies_info = []
enemies_info = []
resources_info = []

while True:
    if can_write:
        with open(channel, "w") as f:
            print("writing data")
            while True:
                action = input()
                f.write(f"{action}\n")
                if action == "end_turn":
                    break
        can_write = False
        continue
    else:
        with open(channel, "r") as f:
            data = f.read()
        if not "end_turn" in data and not "ready" in data:
            print(data)

        if "world_done" in data:
            allies_info.clear()
            enemies_info.clear()
            resources_info.clear()            
            splitted = data.split("\n")
            for event in splitted:
                match event.split(" "):
                    case ["turn", _, my_res]:
                        resources = float(my_res)
                    case ["troop", "ally", troopID, xPos, yPos, health, moveSpeed, damage]:
                        allies_info.append((int(troopID), Vec(int(xPos), int(yPos)), int(health), int(moveSpeed), int(damage)))
                    case ["troop", "enemy", troopID, xPos, yPos, health, moveSpeed, damage]:
                        enemies_info.append((int(troopID), Vec(int(xPos), int(yPos)), int(health), int(moveSpeed), int(damage)))
                    case ["resource", xPos, yPos, health, resourceGain]:
                        resources_info.append((Vec(int(xPos), int(yPos)), int(health), int(resourceGain)))
            
            print(f"turn: {splitted[0]}")
            print("state received, passing to writing commands")
            can_write = True
            continue
        else:
            print("waiting for world")
