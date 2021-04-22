from jelly.server import Server

import socket
import json
import threading
import pygame
from pygame import gfxdraw
import random


# https://stackoverflow.com/a/62480486
def draw_circle(window: pygame.Surface, x: int, y: int, radius: int, color: pygame.Color):
    """Draws a circle at (`x`, `y`) with radius `radius` and color `color` on `window` using antialiasing."""
    gfxdraw.aacircle(window, x, y, radius, color)
    gfxdraw.filled_circle(window, x, y, radius, color)


def world_to_screen(x: int, y: int, offset_x: int, offset_y: int):
    return x - offset_x, y - offset_y


def random_color() -> pygame.Color:
    """Returns a random color"""
    return pygame.Color(random.randrange(0, 256), random.randrange(0, 256), random.randrange(0, 256))


class Client:
    WIDTH = 1000
    HEIGHT = 500
    BACKGROUND = pygame.color.Color(255, 255, 255)
    SCALE = 1
    MOVE_STEP = int(Server.DEFAULT_PLAYER_SIZE/10)

    FOOD_SIZE = 5

    def __init__(self, nick: str, server_host=Server.HOST, server_port=Server.PORT):
        self.nick = nick
        self.players = dict()
        self.food = []

        self.player_colors = dict()
        self.food_colors = dict()

        self.HOST = server_host
        self.PORT = server_port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.HOST, self.PORT))
        self.sock_mutex = threading.Lock()

        # Precompute some commands. Those are just JSON binary string. See docs/protocol.md
        self.SPAWN = json.dumps({Server.SPAWN: self.nick}).encode("UTF-8")
        self.GET = json.dumps(Server.GET).encode("UTF-8")
        self.DISCONNECT = json.dumps({Server.DISCONNECT: self.nick}).encode("UTF-8")

        # Create a player with the same nick at the server side.
        self.send_spawn()

        # Draw GUI
        self.game_loop()

    def __del__(self):
        """Sends `DISCONNECT` command and closes the socket."""
        self.send_disconnect()
        self.sock.close()

    def send_command(self, command: bytes):
        """Send `command` binary string to the server. See docs/protocol.md"""
        with self.sock_mutex:
            self.sock.sendall(command)

    def receive(self):
        """Receive and return server response."""
        with self.sock_mutex:
            response = self.sock.recv(2048)
        return response

    def send_disconnect(self):
        """After the corresponding binary string is sent to the server, the last removes data about the player."""
        self.send_command(self.DISCONNECT)

    def receive_get(self):
        """Sends `GET` command to the server. Parses server JSON response and saves it."""
        self.send_command(self.GET)

        # TODO: check if response is longer than 2048 bytes.
        response = self.receive()

        # Parse the received JSON and save it into self.players
        parsed_response = json.loads(response.decode("UTF-8"))
        self.players = parsed_response["players"]
        self.food = parsed_response["food"]
        self.assign_colors()

    def assign_colors(self) -> None:
        for player in self.players:
            if player not in self.player_colors:
                self.player_colors[player] = random_color()
        for food in self.food:
            temp = (food[0], food[1])
            if temp not in self.food_colors:
                self.food_colors[temp] = random_color()

    def send_move(self, x: int, y: int):
        """Sends `MOVE` command to the server. `x` and `y` are new coordinates of the player."""
        command = json.dumps({Server.MOVE: [self.nick, x, y]}).encode("UTF-8")
        self.send_command(command)

    def send_spawn(self):
        """Sends `SPAWN` command to the server."""
        self.send_command(self.SPAWN)

    def game_loop(self):
        pygame.init()
        window = pygame.display.set_mode((Client.WIDTH, Client.HEIGHT))
        pygame.display.set_caption("Jelly")

        # TODO: generate it in a separate thread.
        font = pygame.font.SysFont('helvetica.ttf', 30)

        self.receive_get()
        x, y = self.players[self.nick][:2]

        offset_x = int(x - self.WIDTH/2)
        offset_y = int(y - self.HEIGHT/2)

        run = True
        while run:
            pygame.time.delay(100)

            # Networking thread
            get_thread = threading.Thread(target=self.receive_get, daemon=True)
            get_thread.start()

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    run = False

            keys = pygame.key.get_pressed()

            if keys[pygame.K_LEFT]:
                x -= self.MOVE_STEP
                offset_x -= self.MOVE_STEP
            if keys[pygame.K_UP]:
                y -= self.MOVE_STEP
                offset_y -= self.MOVE_STEP
            if keys[pygame.K_RIGHT]:
                x += self.MOVE_STEP
                offset_x += self.MOVE_STEP
            if keys[pygame.K_DOWN]:
                y += self.MOVE_STEP
                offset_y += self.MOVE_STEP

            get_thread.join()

            post_thread = threading.Thread(target=self.send_move, args=(x, y), daemon=True)
            post_thread.start()

            window.fill(self.BACKGROUND)
            for nick, v in self.players.items():
                screen_x, screen_y = world_to_screen(v[0], v[1], offset_x, offset_y)
                draw_circle(window, screen_x, screen_y, v[2]*self.SCALE, self.player_colors[nick])

                image = font.render(nick, True, (0, 0, 0))
                rect = image.get_rect(center=(screen_x, screen_y))
                window.blit(image, rect)

            for v in self.food:
                screen_x, screen_y = world_to_screen(v[0], v[1], offset_x, offset_y)
                temp = (v[0], v[1])
                draw_circle(window, screen_x, screen_y, self.FOOD_SIZE, self.food_colors[temp])

            pygame.display.update()

            post_thread.join()

        pygame.quit()

