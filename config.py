HOST = 'localhost'
PORT = 1513

INIT_PLAYER_SIZE = 50

# Number of the food on the map.
FOOD_NUM = 30

FOOD_MIN_SIZE = 3
FOOD_MAX_SIZE = 5

# Food kind probability such that
# FOOD_PROBABILITY[n] is a probability of spawning a food unit of `FoodKind(n)` kind,
# where 0 <= n < len(FoodKind).
FOOD_PROBABILITY = [80, 15, 4, 1]

MAP_WIDTH = 2000
MAP_HEIGHT = 2000

SCREEN_WIDTH = 500
SCREEN_HEIGHT = 500

# In seconds.
GAME_TIME = 120
RESTART_TIME = 5