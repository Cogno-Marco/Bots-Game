import sys
from typing import List, Tuple
from math import sqrt

"""
BOT VERSION: 1.1.2
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
spawn_pos = Vec(spawn_pos[0], spawn_pos[1])

with open(channel, "w") as f:
    f.write("ready")

can_write = False
my_troop = None
enemies_info = []
resources_info = []

while True:
    if can_write:
        with open(channel, "r") as f:
            print(f.read())
        
        # prendi risorsa più vicina
        troop_pos = my_troop[1]
        resource_pos = None
        min_dist = 100000
        for pos, health, gain in resources_info:
            offset = pos - troop_pos
            dist = sqrt(offset.x * offset.x + offset.y * offset.y)
            if dist < min_dist:
                min_dist = dist
                resource_pos = pos
        
        cmd = ""
        
        # move troop towards resource
        troop_dir = ""
        offset = resource_pos - troop_pos
        match offset.value():
            case (1, 0):
                cmd = "action"
                troop_dir = "right"
            case (-1, 0):
                cmd = "action"
                troop_dir = "left"
            case (0, 1):
                cmd = "action"
                troop_dir = "up"
            case (0, -1):
                cmd = "action"
                troop_dir = "down"
            case (x, y) if x != 0:
                cmd = "move"
                troop_dir = "right" if x > 0 else "left"
            case (x, y) if y != 0:
                cmd = "move"
                troop_dir = "up" if y > 0 else "down"
                
        with open(channel, "w") as f:
            print("writing data")
            if cmd == "move":
                f.write(f"move {my_troop[0]} {troop_dir} 1\nend_turn")
            elif cmd == "action":
                f.write(f"action {my_troop[0]} {troop_dir}\nend_turn")
        can_write = False
        continue

    else:
        with open(channel, "r") as f:
            data = f.read()
        
        if "world_done" in data:
            my_troop = None
            enemies_info.clear()
            resources_info.clear()            
            splitted = data.split("\n")
            for event in splitted:
                match event.split(" "):
                    case ["troop", "ally", troopID, xPos, yPos, health, moveSpeed, damage]:
                        my_troop = (int(troopID), Vec(int(xPos), int(yPos)), int(health), int(moveSpeed), int(damage))
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
