import socket
from threading import Thread
from json import loads, dumps
from random import randrange
from datetime import datetime, timedelta

from jelly.utils import Direction, InvalidData, assert_nick, random_color
from jelly.player import Players, Player, player_was_eaten
from jelly.food import Food, FoodKind, food_was_eaten


class Server:
    """Server side of Jelly app."""

    # A collection of constant strings for information interchange between a client and the server.
    GET = 'GET'
    SPAWN = 'SPAWN'
    MOVE = 'MOVE'
    DISCONNECT = 'DISCONNECT'

    def __init__(self, host, port, food_num, width, height, game_time, restart_time, food_min_size, food_max_size,
                 food_probability, init_player_size):
        self.HOST = host
        self.PORT = port
        self.FOOD_NUM = food_num
        self.MAP_WIDTH = width
        self.MAP_HEIGHT = height
        self.GAME_TIME = timedelta(seconds=game_time)
        self.RESTART_TIME = timedelta(seconds=restart_time)
        self.FOOD_MIN_SIZE, self.FOOD_MAX_SIZE = food_min_size, food_max_size

        assert len(food_probability) == len(FoodKind)
        self.FOOD_PROBABILITY = food_probability

        self.INIT_PLAYER_SIZE = init_player_size

        # TODO: move params (def pl size & food prob) into the constructor.
        self.players = Players(self.INIT_PLAYER_SIZE)
        self.food = Food(self.FOOD_PROBABILITY, food_min_size, food_max_size)

        self.start_time = datetime.now()

        # Spawn `FOOD_NUM` units of food.
        for _ in range(self.FOOD_NUM):
            self.food.spawn(self.rand_coords())

        self.listen()

    @staticmethod
    def _json_date_handler(obj):
        return obj.isoformat() if isinstance(obj, datetime) else None

    def rand_coords(self) -> (int, int):
        """Returns a point P(x, y) such that there are no player points in the circle
            with the centre at P and radius `vicinity`"""
        return randrange(self.MAP_WIDTH), randrange(self.MAP_HEIGHT)

    def new_round(self):
        """Respawn all players and food. Update start_time (to start a new round)."""
        for nick in self.players.get_players_raw().keys():
            self.players.spawn(nick, self.rand_coords(), random_color())

        self.food.clear()
        for _ in range(self.FOOD_NUM):
            self.food.spawn(self.rand_coords())

        self.start_time = datetime.now()

    def round_end(self):
        """Returns a point in time, when a new round's going to be started."""
        result = self.start_time + self.GAME_TIME
        # If RESTART_TIME is out, start a new round.
        if datetime.now() - result >= self.RESTART_TIME:
            self.new_round()
        return result

    def json_get_data(self) -> str:
        """Returns a `JSON` string of players and food data. Used to implement `GET` command."""
        return dumps({"players": self.players.get_players_raw(), "food": self.food.get_food_raw(),
                      "round_end": self.round_end()}, default=self._json_date_handler)

    def process_moved(self, moved: Player):
        """Searches through and finds if `moved` ate another player, a food unit or was eaten by someone else. If so,
         (a) increases the size of the eater and clears the size of the victim; OR
         (b) deletes food from the game field, spawns a new one and applies the effect of the food unit to the eater.

        :param moved: A player whose coordinates were changed.
        """
        for player in self.players.get_players():
            result = player_was_eaten(moved, player)
            if result is not None:
                eater, victim = result
                self.players.grow(eater, victim.size)
                self.players.kill(victim)

        for food in self.food.get_food():
            if food_was_eaten(moved, food):
                self.food.pop(food)
                if food.kind == FoodKind.ORDINARY:
                    self.players.grow(moved, food.size)
                elif food.kind == FoodKind.SPEEDING_UP:
                    self.players.mul_speed_factor(moved, 1.15)
                    self.players.inc_speed_effect_time(moved, timedelta(seconds=5))
                elif food.kind == FoodKind.SLOWING_DOWN:
                    self.players.mul_speed_factor(moved, 0.95)
                    self.players.inc_speed_effect_time(moved, timedelta(seconds=5))
                elif food.kind == FoodKind.FREEZING:
                    self.players.mul_speed_factor(moved, 0)
                    self.players.inc_speed_effect_time(moved, timedelta(seconds=7))

                self.food.spawn(self.rand_coords())

    def listen_to_client(self, conn: socket.socket):
        """Handle client commands. Server.listen() calls it for each connected client in a separate thread."""
        with conn:
            while True:
                # Receive client data.
                raw_data = conn.recv(4096)
                if not raw_data:
                    break

                # Parse JSON. See docs/protocol.md
                # TODO: write protocol.md
                data = loads(raw_data.decode("UTF-8"))

                # Handle requests here.
                # GET
                if isinstance(data, str) and data == Server.GET:
                    conn.sendall(self.json_get_data().encode("UTF-8"))
                elif isinstance(data, dict):
                    for command, args in data.items():
                        # SPAWN
                        if command == Server.SPAWN:
                            nick = args
                            assert_nick(nick)
                            assert nick not in self.players
                            self.players.spawn(nick, self.rand_coords(), random_color())
                        # MOVE
                        elif command == Server.MOVE:
                            nick = args[0]
                            direction = Direction(args[1])

                            if nick not in self.players:
                                raise InvalidData("There's no player with nick '{}'.".format(args[0]))

                            player = self.players[nick]

                            # ====================================
                            # radius = self.players[args[0]][2]
                            # try:
                            #     cam = self.coords_after_move(args[0], Direction(args[1]))
                            #     self.assert_coords(*cam, radius)
                            # except ClientInvalidDataError:
                            #     continue

                            self.players.move(player, direction)
                            self.process_moved(player)
                            # ====================================

                        # DISCONNECT
                        elif command == Server.DISCONNECT:
                            nick = args
                            try:
                                self.players.pop(nick)
                            except KeyError:
                                raise InvalidData("There's no player with nick '{}'.".format(args))

    def listen(self):
        """Accepts connections. After a client has connected, talks to it in a separate thread
            at Server.listen_to_client()."""

        # Open a TCP IPv4 socket at HOST=Server.HOST and port=Server.port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((self.HOST, self.PORT))
            # Allow up to 64 connection to queue up.
            sock.listen(64)

            while True:
                # Accept a connection
                conn, _ = sock.accept()

                # Raise an exception if the client has sent no data in a minute.
                conn.settimeout(60)

                # Start a new thread per client.
                thread = Thread(target=self.listen_to_client, args=(conn, ))
                thread.daemon = True
                thread.start()
