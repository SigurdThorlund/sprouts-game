from enum import Enum

class Player(Enum):
    PLAYER_1 = 1
    PLAYER_2 = 2


class State(Enum):
    MAIN_MENU = 1
    RUN_GAME = 2
    OPTIONS_MENU = 3
    GAME_OVER = 4
    VALIDATION = 5
