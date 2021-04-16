import socket
import threading
import json


class Server:
    """Server side of Jelly app."""

    # TODO: move into a config file.
    HOST = 'localhost'
    PORT = 9091

    # When a player is spawned, its size is equal to this value.
    DEFAULT_PLAYER_SIZE = 1

    # A collection of constant strings for information interchange between a client and the server.
    GET = 'GET'
    SPAWN = 'SPAWN'
    MOVE = 'MOVE'
    DISCONNECT = 'DISCONNECT'

    def __init__(self):
        self.players = dict()
        self.listen()

    def spawn_player(self, nick, x, y):
        """Spawns a player with nick `nick` at the point (`x`, `y`)."""
        # TODO: check nick
        if nick not in self.players:
            self.players[nick] = [x, y, Server.DEFAULT_PLAYER_SIZE]

    @staticmethod
    def gen_spawn_coords(vicinity):
        """Returns a point P(x, y) such that there are no player points in the circle
            with the centre at P and radius `vicinity`"""
        # TODO: implement
        return 0, 0

    def get_players(self):
        """Returns a `JSON` string of players data. Used to implement `GET` command."""
        # TODO: catch exceptions
        return json.dumps(self.players)

    def move_player(self, nick, x, y):
        """Changes the position of the player with nick 'nick' to (`x`, `y`)."""
        # TODO: check values.
        self.players[nick][0] = x
        self.players[nick][1] = y

    def disconnect_player(self, nick):
        """Clears the data after player `nick` has disconnected."""
        self.players.pop(nick, None)

    def listen_to_client(self, conn):
        """Handle client commands. Server.listen() calls it for each connected client in a separate thread."""
        with conn:
            while True:
                # Receive client data.
                raw_data = conn.recv(2048)
                if not raw_data:
                    break

                # Parse JSON. See docs/protocol.md
                # TODO: write json_protocol.md
                try:
                    data = json.loads(raw_data.decode("UTF-8"))
                except Exception as e:
                    # TODO: handle exceptions.
                    raise

                # Handle requests here.
                # GET
                if isinstance(data, str) and data == Server.GET:
                    # TODO: cover the case when the len is greater than 2048.
                    conn.sendall(self.get_players().encode("UTF-8"))
                elif isinstance(data, dict):
                    for command, args in data.items():
                        # SPAWN
                        if command == Server.SPAWN:
                            self.spawn_player(args, *self.gen_spawn_coords(Server.DEFAULT_PLAYER_SIZE))
                        # MOVE
                        elif command == Server.MOVE:
                            self.move_player(args[0], args[1], args[2])
                        # DISCONNECT
                        elif command == Server.DISCONNECT:
                            self.disconnect_player(args)

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
