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


def draw_text(surface: pygame.Surface, font: pygame.font.Font, text: str, color=(0, 0, 0), **kargs):
    image = font.render(text, True, color)
    rect = image.get_rect(**kargs)
    surface.blit(image, rect)


def random_color() -> pygame.Color:
    """Returns a random color"""
    return pygame.Color(random.randrange(0, 256), random.randrange(0, 256), random.randrange(0, 256))


class Client:
    BACKGROUND = pygame.color.Color(255, 255, 255)
    LARGE_FONT_SIZE = 30
    SMALL_FONT_SIZE = 20
    FOOD_SIZE = 5

    def __init__(self, nick: str, host: str, port: int, width: int, height: int):
        self.nick = nick

        self.HOST = host
        self.PORT = port

        self.DEFAULT_SCREEN_WIDTH = width
        self.DEFAULT_SCREEN_HEIGHT = height
        self.DEFAULT_LEADER_BOARD_WIDTH = self.DEFAULT_SCREEN_WIDTH // 4

        self.move_step = round(Server.DEFAULT_PLAYER_SIZE/8)

        self.players = dict()
        self.food = []

        self.player_colors = dict()
        self.food_colors = dict()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.HOST, self.PORT))
        self.sock_mutex = threading.Lock()

        # Precompute some commands. Those are just JSON binary string. See docs/protocol.md
        self.SPAWN = json.dumps({Server.SPAWN: self.nick}).encode("UTF-8")
        self.GET = json.dumps(Server.GET).encode("UTF-8")
        self.DISCONNECT = json.dumps({Server.DISCONNECT: self.nick}).encode("UTF-8")

        # Create a player with the same nick at the server side.
        self.send_spawn()

        self.time_left = None

        self.small_font, self.large_font = None, None
        self.winner = None

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
            response = self.sock.recv(4096)
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
        self.time_left = parsed_response["time_left"]

    def assign_colors(self) -> None:
        for player in self.players:
            if player not in self.player_colors:
                self.player_colors[player] = random_color()
        for food in self.food:
            temp = (food[0], food[1])
            if temp not in self.food_colors:
                self.food_colors[temp] = random_color()

    def calculate_move_step(self):
        """Assume the player have grown by `g` times. Therefore slow down by `g` times."""
        times = self.players[self.nick][2]/Server.DEFAULT_PLAYER_SIZE
        self.move_step = round(Server.DEFAULT_PLAYER_SIZE/(4*times))

    def send_move(self, x: int, y: int):
        """Sends `MOVE` command to the server. `x` and `y` are new coordinates of the player."""
        command = json.dumps({Server.MOVE: [self.nick, x, y]}).encode("UTF-8")
        self.send_command(command)

    def send_spawn(self):
        """Sends `SPAWN` command to the server."""
        self.send_command(self.SPAWN)

    @staticmethod
    def render_fonts():
        return pygame.font.Font(None, Client.SMALL_FONT_SIZE), pygame.font.Font(None, Client.LARGE_FONT_SIZE)

    @staticmethod
    def calculate_offset(world_x: int, world_y: int, width: int, height: int):
        """
        Calculates offset so that we can draw the player in the center of the screen.

        :param world_x: player's x coordinate in the world (not screen)
        :param world_y: player's y coordinate in the world (not screen)
        :param width: width of the screen
        :param height: height of the screen
        :returns: a pair of integers k & m such that world_to_screen(world_x, world_y, k, m)
         returns the center of the screen.
        """
        return world_x - width // 2, world_y - height // 2

    @staticmethod
    def world_to_screen(x: int, y: int, offset_x: int, offset_y: int):
        """
        Translates coordinates in the world to screen coordinates.

        :param x: player's x coordinate in the world (not screen)
        :param y: player's y coordinate in the world (not screen)
        :param offset_x: a value calculated by calculate_offset() function
        :param offset_y: a value calculated by calculate_offset() function
        :return: coordinates in terms of the screen applying the offset.
        """
        return x - offset_x, y - offset_y

    @staticmethod
    def is_circle_on_screen(x: int, y: int, r: int, w: int, h: int):
        """Returns True, if a circle with radius `r` and center at (`x`, `y`) is
        on the screen with width `w` and height `h`. Assume each point (`i`, `j`) is on the screen
        iff 0 <= i < w and 0 <= j < h."""
        p = (0 <= x + r < w) or (0 <= x - r < w)
        q = (0 <= y + r < w) or (0 <= y - r < w)
        return p and q

    def died(self, surface: pygame.Surface, lb_offset_x: int, lb_text_height: int):
        draw_text(surface, self.large_font, "Game Over",
                  center=(surface.get_width() // 2, surface.get_height() // 2))
        self.draw_leader_board(surface, lb_offset_x, lb_text_height)

    def timeout(self, surface: pygame.Surface, lb_offset_x: int, lb_text_height: int):
        if self.winner is None:
            # TODO: do NOT rely on implementation-dependent behaviour.
            #  Items of the dictionary aren't required to be sorted.
            self.winner = list(self.players.keys())[0]

        draw_text(surface, self.large_font, "{} is the winner!".format(self.winner),
                  center=(surface.get_width() // 2, surface.get_height() // 2))

        self.draw_leader_board(surface, lb_offset_x, lb_text_height)

    def draw_leader_board(self, surface: pygame.Surface, lb_offset_x, lb_text_height):
        myself_in_top_ten = False
        for iter_count, nick in enumerate(list(self.players.keys())[:10]):
            if nick == self.nick:
                myself_in_top_ten = True
            draw_text(surface, self.small_font, "#{} {}".format(iter_count + 1, nick), (0, 0, 0),
                      topleft=(lb_offset_x, lb_text_height * iter_count))
        if not myself_in_top_ten:
            rank = list(self.players.keys()).index(self.nick)
            draw_text(surface, self.small_font, "#{} {}".format(rank + 1, self.nick), (0, 0, 0),
                      topleft=(lb_offset_x, lb_text_height * 10))

    def game_loop(self):
        pygame.init()

        # Create a resizable window.
        surface = pygame.display.set_mode((self.DEFAULT_SCREEN_WIDTH, self.DEFAULT_SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Jelly - {}".format(self.nick))

        self.small_font, self.large_font = Client.render_fonts()

        lb_offset_x = self.DEFAULT_SCREEN_WIDTH - self.DEFAULT_LEADER_BOARD_WIDTH
        lb_text_height = self.large_font.render('#0 TEST', True, (0, 0, 0)).get_height()

        self.receive_get()
        x, y = self.players[self.nick][:2]

        offset_x, offset_y = Client.calculate_offset(x, y, *surface.get_size())

        run = True
        while run:
            # Networking thread
            get_thread = threading.Thread(target=self.receive_get, daemon=True)
            get_thread.start()

            pygame.time.delay(20)

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    run = False
                if e.type == pygame.VIDEORESIZE:
                    surface = pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)
                    # Recalculate offsets after the window was resized
                    offset_x, offset_y = Client.calculate_offset(x, y, e.w, e.h)
                    lb_offset_x = e.w - self.DEFAULT_LEADER_BOARD_WIDTH

            surface.fill(self.BACKGROUND)
            size = self.players[self.nick][2]
            if size <= 0:
                get_thread.join()
                self.died(surface, lb_offset_x, lb_text_height)
            elif self.time_left > 0:
                keys = pygame.key.get_pressed()

                self.calculate_move_step()
                if keys[pygame.K_LEFT]:
                    x -= self.move_step
                    offset_x -= self.move_step
                if keys[pygame.K_UP]:
                    y -= self.move_step
                    offset_y -= self.move_step
                if keys[pygame.K_RIGHT]:
                    x += self.move_step
                    offset_x += self.move_step
                if keys[pygame.K_DOWN]:
                    y += self.move_step
                    offset_y += self.move_step

                post_thread = threading.Thread(target=self.send_move, args=(x, y), daemon=True)
                post_thread.start()

                get_thread.join()

                self.assign_colors()
                for nick, v in self.players.items():
                    screen_x, screen_y = Client.world_to_screen(v[0], v[1], offset_x, offset_y)
                    if Client.is_circle_on_screen(screen_x, screen_y, v[2], *surface.get_size()) or nick == self.nick:
                        draw_circle(surface, screen_x, screen_y, v[2], self.player_colors[nick])
                        draw_text(surface, self.large_font, nick, (0, 0, 0), center=(screen_x, screen_y))

                for v in self.food:
                    screen_x, screen_y = Client.world_to_screen(v[0], v[1], offset_x, offset_y)
                    temp = (v[0], v[1])

                    if Client.is_circle_on_screen(screen_x, screen_y, Client.FOOD_SIZE, *surface.get_size()):
                        draw_circle(surface, screen_x, screen_y, self.FOOD_SIZE, self.food_colors[temp])

                draw_text(surface, self.small_font, "Time left: {}".format(int(self.time_left)), topleft=(0, 0))
                self.draw_leader_board(surface, lb_offset_x, lb_text_height)

                post_thread.join()
            else:
                self.timeout(surface, lb_offset_x, lb_text_height)

            pygame.display.update()
        pygame.quit()

