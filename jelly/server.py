import socket
import threading
import json


class ClientInvalidDataError(RuntimeError):
    """Raised when the data provided by a client is not valid"""
    pass


class Server:
    """Server side of Jelly app."""

    # TODO: move into a config file.
    HOST = 'localhost'
    # TODO: choose another port.
    PORT = 1513

    # When a player is spawned, its size is equal to this value.
    DEFAULT_PLAYER_SIZE = 1

    MAP_WIDTH = 1000
    MAP_HEIGHT = 500

    # A collection of constant strings for information interchange between a client and the server.
    GET = 'GET'
    SPAWN = 'SPAWN'
    MOVE = 'MOVE'
    DISCONNECT = 'DISCONNECT'

    def __init__(self):
        self.players = dict()
        self.listen()

    @staticmethod
    def assert_nick(nick: str) -> None:
        """Checks if there are only printable characters in `nick`. If not, raises an exception."""
        if not nick.isprintable():
            raise ClientInvalidDataError("Nickname '{}' isn't valid because is contains a "
                                         "non-printable character".format(nick))

    @staticmethod
    def assert_coords(x: int, y: int, radius: int) -> None:
        """Checks a circle with the center at point (`x`, `y`) and radius `radius` is on the map.
        If it isn't, raise an exception"""

        if not (radius > 0 and 0 <= x - radius < Server.MAP_WIDTH and 0 <= x + radius < Server.MAP_WIDTH
                and 0 <= y - radius < Server.MAP_HEIGHT and 0 <= y + radius < Server.MAP_HEIGHT):
            raise ClientInvalidDataError("Player with center at ({}, {}) and size {} isn't on the map."
                                         .format(x, y, radius))

    def spawn_player(self, nick: str, x: int, y: int) -> None:
        """Spawns a player with nick `nick` at the point (`x`, `y`)."""
        # TODO: check nick
        if nick not in self.players:
            self.players[nick] = [x, y, Server.DEFAULT_PLAYER_SIZE]

    @staticmethod
    def gen_spawn_coords(vicinity: int) -> (int, int):
        """Returns a point P(x, y) such that there are no player points in the circle
            with the centre at P and radius `vicinity`"""
        # TODO: implement
        return 1, 1

    def get_players(self) -> str:
        """Returns a `JSON` string of players data. Used to implement `GET` command."""
        # TODO: catch exceptions
        return json.dumps(self.players)

    def move_player(self, nick: str, x: int, y: int) -> None:
        """Changes the position of the player with nick 'nick' to (`x`, `y`)."""
        # TODO: check values.
        self.players[nick][0] = x
        self.players[nick][1] = y

    def disconnect_player(self, nick: str):
        """Clears the data after player `nick` has disconnected."""
        self.players.pop(nick, None)

    def listen_to_client(self, conn: socket.socket):
        """Handle client commands. Server.listen() calls it for each connected client in a separate thread."""
        with conn:
            while True:
                # Receive client data.
                raw_data = conn.recv(2048)
                if not raw_data:
                    break

                # Parse JSON. See docs/protocol.md
                # TODO: write json_protocol.md
                data = json.loads(raw_data.decode("UTF-8"))

                # Handle requests here.
                # GET
                if isinstance(data, str) and data == Server.GET:
                    # TODO: cover the case when the len is greater than 2048.
                    conn.sendall(self.get_players().encode("UTF-8"))
                elif isinstance(data, dict):
                    for command, args in data.items():
                        # SPAWN
                        if command == Server.SPAWN:
                            # Check user data.
                            self.assert_nick(args)
                            self.spawn_player(args, *self.gen_spawn_coords(Server.DEFAULT_PLAYER_SIZE))
                        # MOVE
                        elif command == Server.MOVE:
                            if not args[0] in self.players:
                                raise ClientInvalidDataError("There's no player with nick '{}'.".format(args[0]))

                            # radius = self.players[args[0]][2]
                            # self.assert_coords(args[1], args[2], radius)
                            self.move_player(args[0], args[1], args[2])
                        # DISCONNECT
                        elif command == Server.DISCONNECT:
                            try:
                                self.disconnect_player(args)
                            except KeyError:
                                raise ClientInvalidDataError("There's no player with nick '{}'.".format(args))

    def listen(self):
        """Accepts connections. After a client has connected, talks to it in a separate thread
            at Server.listen_to_client()."""

        # Open a TCP IPv4 socket at HOST=Server.HOST and PORT=Server.PORT
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((Server.HOST, Server.PORT))
            # Allow up to 64 connection to queue up.
            sock.listen(64)

            while True:
                # Accept a connection
                conn, _ = sock.accept()

                # Raise an exception if the client has sent no data in a minute.
                conn.settimeout(60)

                # Start a new thread per client.
                thread = threading.Thread(target=self.listen_to_client, args=(conn, ))
                thread.daemon = True
                thread.start()
