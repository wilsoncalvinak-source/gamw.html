import sys
import time
import random
import textwrap
import os

# --- CONFIGURATION ---
WIDTH = 80
SPEED_FAST = 0.01
SPEED_SLOW = 0.04
SPEED_SCARY = 0.08

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# --- UTILITY FUNCTIONS ---
def type_text(text, speed=SPEED_FAST, color=None):
    """Effect for typing out text character by character."""
    if color:
        sys.stdout.write(color)
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(speed)
    if color:
        sys.stdout.write(Colors.ENDC)
    print() # Newline

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# --- GAME CLASSES ---

class Item:
    def __init__(self, name, description, is_key=False):
        self.name = name
        self.description = description
        self.is_key = is_key

class Room:
    def __init__(self, name, description, dark_description=None):
        self.name = name
        self.description = description
        self.dark_description = dark_description # Used when sanity is low
        self.exits = {} # {'north': room_obj}
        self.items = []
        self.locked = False
        self.key_needed = None

    def get_description(self, sanity_level):
        """Returns description based on player sanity."""
        if sanity_level < 40 and self.dark_description:
            return f"{self.description}\n\n{Colors.FAIL}{self.dark_description}{Colors.ENDC}"
        return self.description

    def add_exit(self, direction, room):
        self.exits[direction] = room

    def add_item(self, item):
        self.items.append(item)

    def remove_item(self, item_name):
        for item in self.items:
            if item.name.lower() == item_name.lower():
                self.items.remove(item)
                return item
        return None

class Player:
    def __init__(self):
        self.inventory = []
        self.sanity = 100
        self.alive = True
        self.location = None

    def move(self, direction):
        if direction in self.location.exits:
            next_room = self.location.exits[direction]
            if next_room.locked:
                # Check for key
                if next_room.key_needed in [i.name for i in self.inventory]:
                    type_text(f"You unlock the door with the {next_room.key_needed}...", SPEED_SLOW)
                    next_room.locked = False
                    self.location = next_room
                    self.drain_sanity(2)
                else:
                    type_text("The door is locked. You need a key.", SPEED_FAST, Colors.WARNING)
            else:
                self.location = next_room
                self.drain_sanity(random.randint(1, 3))
        else:
            type_text("You cannot go that way.", SPEED_FAST)

    def take_item(self, item_name):
        item = self.location.remove_item(item_name)
        if item:
            self.inventory.append(item)
            type_text(f"You picked up: {item.name}", SPEED_FAST, Colors.GREEN)
        else:
            type_text("I don't see that here.", SPEED_FAST)

    def check_inventory(self):
        if not self.inventory:
            type_text("Your pockets are empty.", SPEED_FAST)
        else:
            type_text("You are carrying:", SPEED_FAST)
            for item in self.inventory:
                print(f"- {item.name}: {item.description}")

    def drain_sanity(self, amount):
        self.sanity -= amount
        if self.sanity <= 0:
            self.alive = False

    def print_status(self):
        status_bar = f"SANITY: {self.sanity}%"
        if self.sanity > 70:
            col = Colors.GREEN
        elif self.sanity > 30:
            col = Colors.WARNING
        else:
            col = Colors.FAIL
            status_bar += " (MIND FRACTURING)"
        
        print("-" * WIDTH)
        print(f"{col}{status_bar}{Colors.ENDC}")
        print("-" * WIDTH)

# --- GAME ENGINE ---

class Game:
    def __init__(self):
        self.player = Player()
        self.setup_world()

    def setup_world(self):
        # 1. Create Items
        rusty_key = Item("Rusty Key", "A heavy, corroded iron key.", is_key=True)
        note = Item("Crumbled Note", "It reads: 'DON'T LOOK AT THE WALLS.'")
        flashlight = Item("Flashlight", "Flickers constantly.")

        # 2. Create Rooms
        hallway = Room("Grand Hallway", 
                       "You stand in a grand hallway. Dust motes dance in the stagnant air. Portraits line the walls.",
                       "The portraits... their eyes are following you. Some are bleeding.")
        
        kitchen = Room("Kitchen", 
                       "Rotting food sits on the counters. The smell is unbearable.",
                       "You hear the sound of chopping meat, but no one is there.")
        
        basement = Room("Basement", 
                        "It is pitch black. Water drips somewhere in the distance.",
                        "Something is breathing down your neck.")
        
        garden = Room("Withered Garden",
                      "Dead vines choke the statues. The moon is the only light.",
                      "The statues have moved closer since you last looked.")

        exit_gate = Room("The Gate", "The iron gate leading to freedom.", "")

        # 3. Link Rooms
        hallway.add_exit("north", kitchen)
        hallway.add_exit("south", garden)
        kitchen.add_exit("south", hallway)
        kitchen.add_exit("down", basement)
        basement.add_exit("up", kitchen)
        garden.add_exit("north", hallway)
        garden.add_exit("east", exit_gate)

        # 4. Place Items & Locks
        hallway.add_item(note)
        kitchen.add_item(rusty_key)
        garden.add_item(flashlight)

        exit_gate.locked = True
        exit_gate.key_needed = "Rusty Key"

        # 5. Set Start
        self.player.location = hallway

    def play(self):
        clear_screen()
        type_text("Welcome to ECHOES OF THE MANOR", SPEED_SLOW, Colors.HEADER)
        type_text("Escape before your mind breaks...", SPEED_SLOW)
        time.sleep(1)

        while self.player.alive:
            print("\n")
            self.player.print_status()
            
            # Room Header
            print(f"{Colors.BOLD}{self.player.location.name}{Colors.ENDC}")
            
            # Dynamic Description
            desc = self.player.location.get_description(self.player.sanity)
            print(textwrap.fill(desc, WIDTH))
            
            # Show Items
            if self.player.location.items:
                print(f"{Colors.CYAN}You see: {', '.join([i.name for i in self.player.location.items])}{Colors.ENDC}")

            # Hallucination Event
            if self.player.sanity < 50 and random.random() < 0.3:
                type_text("\n*** You hear a whisper calling your name... ***", SPEED_SCARY, Colors.FAIL)
                self.player.drain_sanity(5)

            # Input Loop
            command = input("\n> ").lower().split()
            
            if not command:
                continue

            action = command[0]

            if action in ["quit", "exit"]:
                break
            
            elif action in ["n", "north"]:
                self.player.move("north")
            elif action in ["s", "south"]:
                self.player.move("south")
            elif action in ["e", "east"]:
                self.player.move("east")
            elif action in ["w", "west"]:
                self.player.move("west")
            elif action in ["u", "up"]:
                self.player.move("up")
            elif action in ["d", "down"]:
                self.player.move("down")
            
            elif action == "look":
                type_text(self.player.location.description, SPEED_FAST)
            
            elif action == "take" and len(command) > 1:
                item_name = " ".join(command[1:])
                # Handle multi-word items loosely
                found = False
                for item in self.player.location.items:
                    if item_name in item.name.lower():
                        self.player.take_item(item.name)
                        found = True
                        break
                if not found:
                    type_text("Can't find that here.", SPEED_FAST)
            
            elif action in ["i", "inv", "inventory"]:
                self.player.check_inventory()
            
            elif action == "help":
                print("COMMANDS: north, south, east, west, up, down, take [item], inv, look, quit")
            
            else:
                type_text("I don't understand that.", SPEED_FAST)

            # Win Condition
            if self.player.location.name == "The Gate":
                type_text("\n\nThe rusty gate creaks open. You step into the cool night air.", SPEED_SLOW, Colors.BLUE)
                type_text("You have escaped... for now.", SPEED_
